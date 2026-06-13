from __future__ import annotations

import asyncio
import re
from collections import deque
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any, Protocol
from uuid import uuid4

import httpx

from app.core.settings import Settings, settings
from app.models.incident import IncidentState
from app.services.autonomous_agent_state import (
    AutonomousRunState,
    AutonomousStateStore,
    RoleOutputRecord,
)
from app.services.autonomous_role_agents import (
    ROLE_DEFINITIONS,
    UPSTREAM_ROLES,
    AutonomousReasoningProvider,
    AutonomousRoleContext,
    AutonomousRoleOutput,
    ReasoningProvider,
)
from app.services.band_agent_registry import (
    BandRemoteAgent,
    build_band_client_for_agent,
    build_band_remote_agent_registry,
)
from app.services.band_client import (
    BandClient,
    BandConfigurationError,
    BandDeliveryResult,
    extract_mention_handles,
    normalize_mention_handle,
    normalize_mention_handles,
)
from app.services.incident_repository import incident_repository


AUTO_START_PATTERN = re.compile(r"\bAUTO:START\s+([A-Za-z0-9_.-]+)\b", re.IGNORECASE)
RUN_MARKER_PATTERN = re.compile(
    r"\[WL-AUTO:(?P<incident>[A-Za-z0-9_.-]+):(?P<role>[a-z_]+):(?P<run>[A-Za-z0-9_.-]+)\]"
)


@dataclass(frozen=True)
class BandMessageEvent:
    message_id: str
    content: str
    author_handle: str | None = None
    mention_handles: tuple[str, ...] = ()
    chat_id: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def normalized_mentions(self) -> tuple[str, ...]:
        handles = list(self.mention_handles)
        handles.extend(extract_mention_handles(self.content))
        return tuple(normalize_mention_handles(handles))


@dataclass(frozen=True)
class SentBandMessage:
    message_id: str
    role: str
    content: str
    mention_handles: tuple[str, ...]
    delivery: BandDeliveryResult


class BandEventSource(Protocol):
    async def events(self) -> AsyncIterator[BandMessageEvent]:
        ...

    async def publish_sent_message(
        self,
        sent_message: SentBandMessage,
        author_handle: str,
    ) -> None:
        ...


class BandMessenger(Protocol):
    async def send_role_output(
        self,
        role: str,
        output: AutonomousRoleOutput,
    ) -> SentBandMessage:
        ...


class ScriptedBandEventSource:
    def __init__(self, events: list[BandMessageEvent] | None = None) -> None:
        self._events: deque[BandMessageEvent] = deque(events or [])
        self.published_events: list[BandMessageEvent] = []

    async def events(self) -> AsyncIterator[BandMessageEvent]:
        while self._events:
            yield self._events.popleft()

    async def publish_sent_message(
        self,
        sent_message: SentBandMessage,
        author_handle: str,
    ) -> None:
        event = BandMessageEvent(
            message_id=sent_message.message_id,
            content=sent_message.content,
            author_handle=author_handle,
            mention_handles=sent_message.mention_handles,
        )
        self.published_events.append(event)
        self._events.append(event)


class LiveBandEventSource:
    """Polling receive adapter for Band room messages.

    The existing repo only documents the Band REST Agent send path. This adapter
    keeps live receive isolated so it can be replaced with an official SDK or
    WebSocket subscription when Band's receive contract is available.
    """

    def __init__(
        self,
        base_url: str,
        chat_id: str,
        agent_api_key: str,
        poll_interval_seconds: float = 5.0,
        single_pass: bool = False,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.chat_id = chat_id
        self.agent_api_key = agent_api_key
        self.poll_interval_seconds = poll_interval_seconds
        self.single_pass = single_pass
        self._seen_message_ids: set[str] = set()

    async def events(self) -> AsyncIterator[BandMessageEvent]:
        while True:
            for event in await self._poll_once():
                if event.message_id in self._seen_message_ids:
                    continue
                self._seen_message_ids.add(event.message_id)
                yield event

            if self.single_pass:
                return

            await asyncio.sleep(self.poll_interval_seconds)

    async def publish_sent_message(
        self,
        sent_message: SentBandMessage,
        author_handle: str,
    ) -> None:
        return None

    async def _poll_once(self) -> list[BandMessageEvent]:
        headers = {"X-API-Key": self.agent_api_key}
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(
                f"{self.base_url}/agent/chats/{self.chat_id}/messages",
                headers=headers,
                params={"limit": 50},
            )

        response.raise_for_status()
        payload = response.json()
        messages = _extract_message_list(payload)
        return [_event_from_band_payload(message, self.chat_id) for message in messages]


class DryRunBandMessenger:
    def __init__(self, registry: dict[str, BandRemoteAgent]) -> None:
        self.registry = registry
        self.sent_messages: list[SentBandMessage] = []

    async def send_role_output(
        self,
        role: str,
        output: AutonomousRoleOutput,
    ) -> SentBandMessage:
        message = SentBandMessage(
            message_id=f"dryrun-{len(self.sent_messages) + 1}-{role}",
            role=role,
            content=output.band_message,
            mention_handles=tuple(
                self.registry[target].handle
                for target in output.handoff_roles
                if target in self.registry
            ),
            delivery=BandDeliveryResult(
                delivered=True,
                detail="Dry-run message captured without live Band delivery.",
                status_code=None,
            ),
        )
        self.sent_messages.append(message)
        return message


class LiveBandMessenger:
    def __init__(
        self,
        settings_obj: Settings,
        registry: dict[str, BandRemoteAgent],
    ) -> None:
        self.settings = settings_obj
        self.registry = registry

    async def send_role_output(
        self,
        role: str,
        output: AutonomousRoleOutput,
    ) -> SentBandMessage:
        agent = self.registry[role]
        client = build_band_client_for_agent(self.settings, agent)
        chat_id = self._required_chat_id()
        mention_handles = [
            self.registry[target].handle
            for target in output.handoff_roles
            if target in self.registry
        ]

        delivery = await client.send_text_message(
            chat_id=chat_id,
            content=output.band_message,
            mention_handles=mention_handles,
        )
        return SentBandMessage(
            message_id=f"live-{role}-{uuid4().hex}",
            role=role,
            content=output.band_message,
            mention_handles=tuple(mention_handles),
            delivery=delivery,
        )

    def _required_chat_id(self) -> str:
        if not self.settings.band_chat_id:
            raise BandConfigurationError("Band chat ID is not configured.")
        return self.settings.band_chat_id


class AutonomousBandRuntime:
    def __init__(
        self,
        registry: dict[str, BandRemoteAgent],
        event_source: BandEventSource,
        messenger: BandMessenger,
        reasoning_provider: ReasoningProvider | None = None,
        state: AutonomousRunState | None = None,
        state_store: AutonomousStateStore | None = None,
        max_turns: int = 12,
        run_id: str | None = None,
        stop_after_complete: bool = True,
        settings_obj: Settings = settings,
    ) -> None:
        self.registry = registry
        self.event_source = event_source
        self.messenger = messenger
        self.reasoning_provider = reasoning_provider or AutonomousReasoningProvider(
            getattr(settings_obj, "autonomous_agent_provider_mode", "auto"),
            settings_obj=settings_obj,
        )
        self.state = state
        self.state_store = state_store or AutonomousStateStore()
        self.max_turns = max_turns
        self.run_id = run_id
        self.stop_after_complete = stop_after_complete
        self.settings = settings_obj

    async def run_until_complete(self) -> AutonomousRunState:
        async for event in self.event_source.events():
            await self.handle_event(event)

            if (
                self.stop_after_complete
                and self.state
                and self.state.status == "complete"
            ):
                break
            if self.state and self.state.turn_count >= self.state.max_turns:
                self.state.status = "max_turns_exceeded"
                self.state_store.save(self.state)
                break

        if self.state:
            self.state_store.save(self.state)
            return self.state

        raise RuntimeError("Autonomous runtime stopped before a run was started.")

    async def handle_event(self, event: BandMessageEvent) -> None:
        if self.state is None:
            incident_id = parse_auto_start(event.content)
            if not incident_id:
                return
            if not self._event_mentions_role(event, "triage"):
                return
            if self._authored_by_role(event, "triage"):
                return

            self.state = AutonomousRunState(
                incident_id=incident_id,
                run_id=self.run_id or uuid4().hex[:8],
                max_turns=self.max_turns,
            )
            self.state_store.save(self.state)

        assert self.state is not None

        for role in self._roles_triggered_by_event(event):
            if self.state.status == "complete":
                return
            if not self.state.mark_processed(role, event.message_id):
                continue
            if self.state.completed(role):
                continue
            if self._authored_by_role(event, role):
                continue

            self.state.add_pending_message(role, event.message_id)
            if not self._role_ready(role):
                self.state_store.save(self.state)
                continue

            await self._run_role(role)

    def _roles_triggered_by_event(self, event: BandMessageEvent) -> list[str]:
        if self.state is None:
            return []

        roles: list[str] = []
        for role in ROLE_DEFINITIONS:
            if not self._event_mentions_role(event, role):
                continue
            if role == "triage" and parse_auto_start(event.content) != self.state.incident_id:
                continue
            if role != "triage" and not self._event_matches_run(event):
                continue
            roles.append(role)

        return roles

    def _event_mentions_role(self, event: BandMessageEvent, role: str) -> bool:
        expected = normalize_mention_handle(self.registry[role].handle)
        return expected in event.normalized_mentions

    def _authored_by_role(self, event: BandMessageEvent, role: str) -> bool:
        if not event.author_handle:
            return False

        author = normalize_mention_handle(event.author_handle)
        role_handle = normalize_mention_handle(self.registry[role].handle)
        return author == role_handle

    def _event_matches_run(self, event: BandMessageEvent) -> bool:
        assert self.state is not None
        marker = parse_run_marker(event.content)
        return bool(
            marker
            and marker["incident_id"] == self.state.incident_id
            and marker["run_id"] == self.state.run_id
        )

    def _role_ready(self, role: str) -> bool:
        assert self.state is not None
        return all(
            upstream in self.state.completed_roles
            for upstream in UPSTREAM_ROLES[role]
        )

    async def _run_role(self, role: str) -> None:
        assert self.state is not None
        incident = incident_repository.get(self.state.incident_id)
        if incident is None:
            raise RuntimeError(f"Incident not found: {self.state.incident_id}")

        context = AutonomousRoleContext(
            incident=incident,
            run_id=self.state.run_id,
            source_message_ids=tuple(
                self.state.pending_role_message_ids.get(role, [])
            ),
            upstream_summaries={
                completed_role: output.summary
                for completed_role, output in self.state.role_outputs.items()
            },
            handles_by_role={
                role_name: agent.handle
                for role_name, agent in self.registry.items()
            },
        )
        definition = ROLE_DEFINITIONS[role]
        output = await self.reasoning_provider.decide(definition, context)
        sent_message = await self.messenger.send_role_output(role, output)

        self.state.complete_role(
            RoleOutputRecord(
                role=output.role,
                provider_name=output.provider_name,
                provider_mode=output.provider_mode,
                summary=output.summary,
                evidence=list(output.evidence),
                recommended_actions=list(output.recommended_actions),
                handoff_roles=list(output.handoff_roles),
                band_message=output.band_message,
                source_message_ids=list(context.source_message_ids),
            )
        )
        self.state_store.save(self.state)

        await self.event_source.publish_sent_message(
            sent_message,
            author_handle=self.registry[role].handle,
        )


def parse_auto_start(content: str) -> str | None:
    match = AUTO_START_PATTERN.search(content)
    return match.group(1).upper() if match else None


def parse_run_marker(content: str) -> dict[str, str] | None:
    match = RUN_MARKER_PATTERN.search(content)
    if not match:
        return None

    return {
        "incident_id": match.group("incident"),
        "role": match.group("role"),
        "run_id": match.group("run"),
    }


def build_dry_run_start_event(
    registry: dict[str, BandRemoteAgent],
    incident_id: str,
) -> BandMessageEvent:
    triage_handle = registry["triage"].handle
    return BandMessageEvent(
        message_id=f"dryrun-human-start-{incident_id}",
        content=f"@{triage_handle} AUTO:START {incident_id}",
        author_handle="human-operator",
        mention_handles=(triage_handle,),
    )


def build_runtime_from_settings(
    dry_run: bool = False,
    incident_id: str = "WL-INC-001",
    state_dir: str = ".workflow-legion-state",
    max_turns: int = 12,
    poll_interval_seconds: float = 5.0,
    run_id: str | None = None,
    stop_after_complete: bool = True,
    single_pass: bool = False,
    settings_obj: Settings = settings,
) -> AutonomousBandRuntime:
    registry = build_band_remote_agent_registry(settings_obj)
    state_store = AutonomousStateStore(state_dir)
    resolved_run_id = run_id or uuid4().hex[:8]
    provider_mode = "deterministic" if dry_run else getattr(
        settings_obj,
        "autonomous_agent_provider_mode",
        "auto",
    )
    reasoning_provider = AutonomousReasoningProvider(
        provider_mode=provider_mode,
        settings_obj=settings_obj,
    )

    if dry_run:
        state = AutonomousRunState(
            incident_id=incident_id,
            run_id=resolved_run_id,
            max_turns=max_turns,
        )
        event_source = ScriptedBandEventSource(
            [build_dry_run_start_event(registry, incident_id)]
        )
        messenger = DryRunBandMessenger(registry)
        return AutonomousBandRuntime(
            registry=registry,
            event_source=event_source,
            messenger=messenger,
            reasoning_provider=reasoning_provider,
            state=state,
            state_store=state_store,
            max_turns=max_turns,
            run_id=resolved_run_id,
            stop_after_complete=stop_after_complete,
            settings_obj=settings_obj,
        )

    receive_key = _live_receive_api_key(settings_obj, registry)
    if not settings_obj.band_chat_id:
        raise BandConfigurationError("Band chat ID is not configured.")
    if not receive_key:
        raise BandConfigurationError(
            "No Band API key is configured for live receive polling."
        )

    return AutonomousBandRuntime(
        registry=registry,
        event_source=LiveBandEventSource(
            base_url=settings_obj.band_base_url,
            chat_id=settings_obj.band_chat_id,
            agent_api_key=receive_key,
            poll_interval_seconds=poll_interval_seconds,
            single_pass=single_pass,
        ),
        messenger=LiveBandMessenger(settings_obj, registry),
        reasoning_provider=reasoning_provider,
        state_store=state_store,
        max_turns=max_turns,
        run_id=resolved_run_id,
        stop_after_complete=stop_after_complete,
        settings_obj=settings_obj,
    )


def _live_receive_api_key(
    settings_obj: Settings,
    registry: dict[str, BandRemoteAgent],
) -> str | None:
    return (
        registry["triage"].agent_api_key
        or settings_obj.band_api_key
    )


def _extract_message_list(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]

    if not isinstance(payload, dict):
        return []

    data = payload.get("data", payload)
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        for key in ("messages", "items", "results"):
            value = data.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]

    for key in ("messages", "items", "results"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]

    return []


def _event_from_band_payload(
    payload: dict[str, Any],
    chat_id: str,
) -> BandMessageEvent:
    message = payload.get("message") if isinstance(payload.get("message"), dict) else payload
    content = str(message.get("content", ""))
    mentions = message.get("mentions") or payload.get("mentions") or []
    mention_handles = []
    if isinstance(mentions, list):
        for mention in mentions:
            if isinstance(mention, dict) and mention.get("handle"):
                mention_handles.append(str(mention["handle"]))

    author = (
        _nested_value(message, "author", "handle")
        or _nested_value(message, "sender", "handle")
        or _nested_value(message, "agent", "handle")
        or _nested_value(payload, "author", "handle")
        or _nested_value(payload, "sender", "handle")
        or _nested_value(payload, "agent", "handle")
    )

    return BandMessageEvent(
        message_id=str(message.get("id") or payload.get("id") or uuid4().hex),
        content=content,
        author_handle=str(author) if author else None,
        mention_handles=tuple(mention_handles),
        chat_id=chat_id,
        raw=payload,
    )


def _nested_value(payload: dict[str, Any], key: str, nested_key: str) -> Any:
    value = payload.get(key)
    if isinstance(value, dict):
        return value.get(nested_key)
    return None
