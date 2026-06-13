from __future__ import annotations

import asyncio
import re
from collections import deque
from collections.abc import AsyncIterator, Callable
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
    BandConfigurationError,
    BandDeliveryResult,
    extract_mention_handles,
)
from app.services.incident_repository import incident_repository


AUTO_START_PATTERN = re.compile(r"\bAUTO:START\s+([A-Za-z0-9_.-]+)\b", re.IGNORECASE)
RUN_MARKER_PATTERN = re.compile(
    r"\[WL-AUTO:(?P<incident>[A-Za-z0-9_.-]+):(?P<role>[a-z_]+):(?P<run>[A-Za-z0-9_.-]+)\]"
)
BAND_INTERNAL_MENTION_PATTERN = re.compile(r"@\[\[([^\]\r\n]+)\]\]")
MENTION_METADATA_FIELDS = (
    "id",
    "agent_id",
    "agentId",
    "handle",
    "name",
    "display_name",
    "displayName",
    "text",
    "label",
    "mention",
    "value",
)
MENTION_METADATA_PRINT_FIELDS = (
    "handle",
    "name",
    "display_name",
    "displayName",
    "text",
    "label",
)


@dataclass(frozen=True)
class BandMessageEvent:
    message_id: str
    content: str
    author_handle: str | None = None
    author_display: str | None = None
    author_id: str | None = None
    created_at: str | None = None
    mention_handles: tuple[str, ...] = ()
    mention_metadata: tuple[dict[str, str], ...] = ()
    chat_id: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def normalized_mentions(self) -> tuple[str, ...]:
        handles = list(self.mention_handles)
        handles.extend(extract_mention_handles(self.content))
        handles.extend(_extract_band_internal_mentions(self.content))
        for mention in self.mention_metadata:
            for field_name in MENTION_METADATA_FIELDS:
                value = mention.get(field_name)
                if value:
                    handles.append(value)
        return tuple(_normalize_mention_candidates(handles))


@dataclass(frozen=True)
class SentBandMessage:
    message_id: str
    role: str
    content: str
    mention_handles: tuple[str, ...]
    delivery: BandDeliveryResult


@dataclass(frozen=True)
class ReceiveBatchItem:
    event: BandMessageEvent
    seen_before: bool


@dataclass(frozen=True)
class ReceiveBatch:
    items: tuple[ReceiveBatchItem, ...]
    order_strategy: str

    @property
    def events(self) -> tuple[BandMessageEvent, ...]:
        return tuple(item.event for item in self.items)

    @property
    def new_items(self) -> tuple[ReceiveBatchItem, ...]:
        return tuple(item for item in self.items if not item.seen_before)

    @property
    def seen_count(self) -> int:
        return len(self.items) - len(self.new_items)


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
        message_limit: int = 5,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.chat_id = chat_id
        self.agent_api_key = agent_api_key
        self.poll_interval_seconds = poll_interval_seconds
        self.single_pass = single_pass
        self.message_limit = max(1, message_limit)
        self.debug_callback: Callable[[ReceiveBatch], None] | None = None
        self._seen_message_ids: set[str] = set()

    async def events(self) -> AsyncIterator[BandMessageEvent]:
        while True:
            polled_events = await self.poll_once()
            batch = self.build_receive_batch(polled_events)
            if self.debug_callback:
                self.debug_callback(batch)

            for item in batch.items:
                if item.seen_before:
                    continue
                event = item.event
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

    async def poll_once(self) -> list[BandMessageEvent]:
        headers = {"X-API-Key": self.agent_api_key}
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(
                f"{self.base_url}/agent/chats/{self.chat_id}/messages",
                headers=headers,
                params={"limit": self.message_limit, "order": "desc"},
            )
            if response.status_code in (400, 422):
                response = await client.get(
                    f"{self.base_url}/agent/chats/{self.chat_id}/messages",
                    headers=headers,
                    params={"limit": self.message_limit},
                )

        response.raise_for_status()
        payload = response.json()
        messages = _extract_message_list(payload)
        events = [_event_from_band_payload(message, self.chat_id) for message in messages]
        return _order_events_for_processing(events)

    async def _poll_once(self) -> list[BandMessageEvent]:
        return await self.poll_once()

    def build_receive_batch(self, events: list[BandMessageEvent]) -> ReceiveBatch:
        batch_seen: set[str] = set()
        items: list[ReceiveBatchItem] = []
        for event in events:
            seen_before = (
                event.message_id in self._seen_message_ids
                or event.message_id in batch_seen
            )
            items.append(ReceiveBatchItem(event=event, seen_before=seen_before))
            batch_seen.add(event.message_id)

        return ReceiveBatch(
            items=tuple(items),
            order_strategy=_event_order_strategy(events),
        )


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
        internal_handoff_queue_enabled: bool | None = None,
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
        self.debug_receive = False
        self.include_seen_debug = False
        self.internal_handoff_queue_enabled = (
            isinstance(event_source, LiveBandEventSource)
            if internal_handoff_queue_enabled is None
            else internal_handoff_queue_enabled
        )
        self._internal_events: deque[BandMessageEvent] = deque()
        self._internal_event_counter = 0

    def enable_receive_debug(
        self,
        enabled: bool = True,
        include_seen_debug: bool = False,
    ) -> None:
        self.debug_receive = enabled
        self.include_seen_debug = include_seen_debug
        if isinstance(self.event_source, LiveBandEventSource):
            self.event_source.debug_callback = (
                self.print_receive_diagnostics if enabled else None
            )

    def print_startup_receive_diagnostics(self) -> None:
        receive_key = _live_receive_api_key(self.settings, self.registry)
        poll_interval = getattr(self.event_source, "poll_interval_seconds", None)
        message_limit = getattr(self.event_source, "message_limit", None)
        print(
            "[debug-receive] config "
            f"band_chat_configured={bool(self.settings.band_chat_id)} "
            f"band_room_configured={bool(self.settings.band_room_id)} "
            f"receive_key_configured={bool(receive_key)}"
        )
        print(
            "[debug-receive] "
            f"active_event_source={type(self.event_source).__name__} "
            f"poll_interval={poll_interval if poll_interval is not None else 'n/a'} "
            f"message_limit={message_limit if message_limit is not None else 'n/a'} "
            f"include_seen_debug={self.include_seen_debug} "
            f"internal_handoff_queue={self.internal_handoff_queue_enabled} "
            f"run_id={self.run_id or 'pending'}"
        )

    def print_receive_diagnostics(
        self,
        batch_or_events: ReceiveBatch | list[BandMessageEvent],
    ) -> None:
        batch = _coerce_receive_batch(batch_or_events)
        print(
            "[debug-receive] "
            f"received_message_count={len(batch.items)} "
            f"new_message_count={len(batch.new_items)} "
            f"seen_message_count={batch.seen_count} "
            f"batch_order_strategy={batch.order_strategy}"
        )
        show_batch_details = bool(batch.new_items) or self.include_seen_debug
        if batch.items and show_batch_details:
            print(
                "[debug-receive] "
                "batch_message_ids="
                + ", ".join(item.event.message_id for item in batch.items)
            )
            print(
                "[debug-receive] "
                "batch_seen_order="
                + ", ".join(
                    f"{item.event.message_id}:"
                    f"{'seen' if item.seen_before else 'new'}"
                    for item in batch.items
                )
            )
            print(
                "[debug-receive] "
                "batch_author_order="
                + " | ".join(
                    f"{item.event.message_id}:"
                    f"{self._author_kind(item.event)}:"
                    f"{_safe_author_summary(item.event)}"
                    for item in batch.items
                )
            )
            agent_authored_count = sum(
                1
                for item in batch.items
                if self._author_kind(item.event).startswith("agent:")
            )
            known_human_count = sum(
                1
                for item in batch.items
                if self._author_kind(item.event) == "human_or_external"
            )
            if agent_authored_count == 0:
                print(
                    "[debug-receive] "
                    "diagnostic=No agent-authored messages visible in receive batch"
                )
                if known_human_count == len(batch.items):
                    print(
                        "[debug-receive] "
                        "diagnostic=Latest batch contains only human-authored messages"
                    )
        elif batch.items:
            print(
                "[debug-receive] "
                f"all_seen_batch_suppressed={len(batch.items)} "
                "use --include-seen-debug to print raw batch ordering"
            )

        if batch.seen_count and not self.include_seen_debug:
            print(
                "[debug-receive] "
                f"seen_messages_suppressed={batch.seen_count} "
                "use --include-seen-debug to print them"
            )

        visible_items = (
            batch.items if self.include_seen_debug else batch.new_items
        )
        for item in visible_items:
            event = item.event
            diagnosis = self.diagnose_event_match(event)
            author = _safe_author_summary(event)
            mentions = _safe_mention_metadata_summary(event)
            print(
                "[debug-receive] "
                f"message_id={event.message_id} "
                f"seen_status={'seen' if item.seen_before else 'new'} "
                f"author_kind={self._author_kind(event)} "
                f"author={author} "
                f"created_at={event.created_at or 'unknown'}"
            )
            print(
                "[debug-receive] "
                f"content_preview={_preview_text(event.content, 180)!r}"
            )
            internal_mention_count = len(_extract_band_internal_mentions(event.content))
            if internal_mention_count:
                print(
                    "[debug-receive] "
                    f"band_internal_mentions_detected={internal_mention_count}"
                )
            if mentions:
                print(f"[debug-receive] mention_metadata={mentions}")
            if diagnosis["matched"]:
                print(
                    "[debug-receive] "
                    "matched_any_role=True "
                    f"matched_roles={', '.join(diagnosis['roles'])}"
                )
            else:
                print(
                    "[debug-receive] "
                    f"matched_any_role=False not_matched={diagnosis['reason']}"
                )

    async def dump_recent_messages(
        self,
        message_limit: int = 5,
    ) -> list[BandMessageEvent]:
        events = await self._read_recent_events(message_limit)
        self.print_receive_diagnostics(events)
        return events

    async def _read_recent_events(
        self,
        message_limit: int,
    ) -> list[BandMessageEvent]:
        if isinstance(self.event_source, LiveBandEventSource):
            original_limit = self.event_source.message_limit
            self.event_source.message_limit = max(1, message_limit)
            try:
                return await self.event_source.poll_once()
            finally:
                self.event_source.message_limit = original_limit

        events: list[BandMessageEvent] = []
        async for event in self.event_source.events():
            events.append(event)
            if len(events) >= max(1, message_limit):
                break
        return events

    def diagnose_event_match(self, event: BandMessageEvent) -> dict[str, Any]:
        matched_roles: list[str] = []
        mentioned_non_matches: list[str] = []

        for role in ROLE_DEFINITIONS:
            reason = self._role_event_non_match_reason(event, role)
            if reason is None:
                matched_roles.append(role)
            elif self._event_mentions_role(event, role):
                mentioned_non_matches.append(reason)

        if matched_roles:
            return {"matched": True, "roles": matched_roles, "reason": None}

        if mentioned_non_matches:
            return {
                "matched": False,
                "roles": [],
                "reason": "; ".join(dict.fromkeys(mentioned_non_matches)),
            }

        return {
            "matched": False,
            "roles": [],
            "reason": "no recognized role mention",
        }

    def _author_kind(self, event: BandMessageEvent) -> str:
        for role in ROLE_DEFINITIONS:
            if self._authored_by_role(event, role):
                return f"agent:{role}"
        if event.author_handle or event.author_display or event.author_id:
            return "human_or_external"
        return "unknown"

    async def run_until_complete(self) -> AutonomousRunState:
        async for event in self.event_source.events():
            await self.handle_event(event)

            if self._should_stop_after_event():
                break

            await self._drain_internal_events()

            if self._should_stop_after_event():
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
            if self._role_event_non_match_reason(event, role) is None:
                roles.append(role)

        return roles

    def _event_mentions_role(self, event: BandMessageEvent, role: str) -> bool:
        aliases = set(self._role_mention_aliases(role))
        if aliases.intersection(event.normalized_mentions):
            return True
        return _content_has_visible_role_mention(event.content, aliases)

    def _role_mention_aliases(self, role: str) -> tuple[str, ...]:
        agent = self.registry[role]
        definition = ROLE_DEFINITIONS[role]
        role_label = role.replace("_", " ")
        aliases = [
            agent.handle,
            f"@{agent.handle}",
            agent.agent_id or "",
            agent.display_name,
            f"@{agent.display_name}",
            definition.display_name,
            f"@{definition.display_name}",
            role_label,
            f"{role_label} agent",
        ]
        return tuple(_normalize_mention_candidates(aliases))

    def _role_event_non_match_reason(
        self,
        event: BandMessageEvent,
        role: str,
    ) -> str | None:
        if not self._event_mentions_role(event, role):
            return f"no recognized mention for {role}"
        if self._authored_by_role(event, role):
            return f"message was authored by {role}"

        if role == "triage":
            incident_id = parse_auto_start(event.content)
            if not incident_id:
                return "triage mention did not include AUTO:START incident token"
            if self.state and incident_id != self.state.incident_id:
                return "AUTO:START incident did not match active incident"
            return None

        if self.state is None:
            return "no active run state yet"
        if not self._event_matches_run(event):
            return "run marker missing or mismatched"
        return None

    def _authored_by_role(self, event: BandMessageEvent, role: str) -> bool:
        aliases = set(self._role_mention_aliases(role))
        author_values = [event.author_handle, event.author_display, event.author_id]
        return any(
            _normalize_mention_candidate(value) in aliases
            for value in author_values
            if value
        )

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
        if not sent_message.delivery.delivered:
            self.state_store.save(self.state)
            return

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
        self._enqueue_internal_handoff(role, sent_message)

    async def _drain_internal_events(self) -> None:
        while self._internal_events and not self._should_stop_after_event():
            await self.handle_event(self._internal_events.popleft())

    def _enqueue_internal_handoff(
        self,
        role: str,
        sent_message: SentBandMessage,
    ) -> None:
        if not self.internal_handoff_queue_enabled:
            return
        if not sent_message.delivery.delivered:
            return
        if not sent_message.mention_handles:
            return
        if self.state is None:
            return

        self._internal_event_counter += 1
        self._internal_events.append(
            BandMessageEvent(
                message_id=(
                    f"internal:{self.state.run_id}:"
                    f"{role}:{self._internal_event_counter}"
                ),
                content=sent_message.content,
                author_handle=self.registry[role].handle,
                mention_handles=sent_message.mention_handles,
            )
        )

    def _should_stop_after_event(self) -> bool:
        if self.state is None:
            return False
        if self.stop_after_complete and self.state.status == "complete":
            return True
        if self.state.turn_count >= self.state.max_turns:
            self.state.status = "max_turns_exceeded"
            self.state_store.save(self.state)
            return True
        return False


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
    message_limit: int = 5,
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
            message_limit=message_limit,
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
    content = str(_first_value(message, "content", "text", "body") or "")
    mention_metadata = tuple(_extract_mention_metadata(message, payload))
    mention_handles = [
        mention["handle"]
        for mention in mention_metadata
        if mention.get("handle")
    ]

    author = (
        _first_value(message, "author_handle", "authorHandle", "sender_handle")
        or _nested_value(message, "author", "handle")
        or _nested_value(message, "sender", "handle")
        or _nested_value(message, "agent", "handle")
        or _first_value(payload, "author_handle", "authorHandle", "sender_handle")
        or _nested_value(payload, "author", "handle")
        or _nested_value(payload, "sender", "handle")
        or _nested_value(payload, "agent", "handle")
    )
    author_display = (
        _first_value(message, "author_name", "authorName", "sender_name")
        or _nested_first_value(message, "author", "name", "display_name", "displayName")
        or _nested_first_value(message, "sender", "name", "display_name", "displayName")
        or _nested_first_value(message, "agent", "name", "display_name", "displayName")
        or _first_value(payload, "author_name", "authorName", "sender_name")
        or _nested_first_value(payload, "author", "name", "display_name", "displayName")
        or _nested_first_value(payload, "sender", "name", "display_name", "displayName")
        or _nested_first_value(payload, "agent", "name", "display_name", "displayName")
    )
    author_id = (
        _first_value(
            message,
            "author_id",
            "authorId",
            "sender_id",
            "senderId",
            "agent_id",
            "agentId",
        )
        or _nested_first_value(message, "author", "id", "agent_id", "agentId")
        or _nested_first_value(message, "sender", "id", "agent_id", "agentId")
        or _nested_first_value(message, "agent", "id", "agent_id", "agentId")
        or _first_value(
            payload,
            "author_id",
            "authorId",
            "sender_id",
            "senderId",
            "agent_id",
            "agentId",
        )
        or _nested_first_value(payload, "author", "id", "agent_id", "agentId")
        or _nested_first_value(payload, "sender", "id", "agent_id", "agentId")
        or _nested_first_value(payload, "agent", "id", "agent_id", "agentId")
    )
    created_at = (
        _first_value(message, "created_at", "createdAt", "timestamp", "time")
        or _first_value(payload, "created_at", "createdAt", "timestamp", "time")
    )

    return BandMessageEvent(
        message_id=str(
            _first_value(message, "id", "message_id", "messageId")
            or _first_value(payload, "id", "message_id", "messageId")
            or uuid4().hex
        ),
        content=content,
        author_handle=str(author) if author else None,
        author_display=str(author_display) if author_display else None,
        author_id=str(author_id) if author_id else None,
        created_at=str(created_at) if created_at else None,
        mention_handles=tuple(mention_handles),
        mention_metadata=mention_metadata,
        chat_id=chat_id,
        raw=payload,
    )


def _extract_mention_metadata(
    message: dict[str, Any],
    payload: dict[str, Any],
) -> list[dict[str, str]]:
    mentions = message.get("mentions") or payload.get("mentions") or []
    safe_mentions: list[dict[str, str]] = []

    if not isinstance(mentions, list):
        return safe_mentions

    for mention in mentions:
        if not isinstance(mention, dict):
            continue

        safe: dict[str, str] = {}
        for field_name in MENTION_METADATA_FIELDS:
            value = mention.get(field_name)
            if value is not None and str(value).strip():
                safe[field_name] = str(value)

        for nested_key in ("user", "agent", "participant"):
            nested = mention.get(nested_key)
            if not isinstance(nested, dict):
                continue
            for source_key, target_key in (
                ("id", "id"),
                ("agent_id", "agent_id"),
                ("agentId", "agentId"),
                ("handle", "handle"),
                ("name", "name"),
                ("display_name", "display_name"),
                ("displayName", "displayName"),
            ):
                value = nested.get(source_key)
                if value is not None and str(value).strip():
                    safe.setdefault(target_key, str(value))

        if safe:
            safe_mentions.append(safe)

    return safe_mentions


def _nested_value(payload: dict[str, Any], key: str, nested_key: str) -> Any:
    value = payload.get(key)
    if isinstance(value, dict):
        return value.get(nested_key)
    return None


def _nested_first_value(
    payload: dict[str, Any],
    key: str,
    *nested_keys: str,
) -> Any:
    value = payload.get(key)
    if not isinstance(value, dict):
        return None
    return _first_value(value, *nested_keys)


def _first_value(payload: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = payload.get(key)
        if value is not None and str(value).strip():
            return value
    return None


def _normalize_mention_candidates(values: list[str] | tuple[str, ...]) -> list[str]:
    normalized: list[str] = []

    for value in values:
        clean = _normalize_mention_candidate(value)
        if clean and clean not in normalized:
            normalized.append(clean)

    return normalized


def _normalize_mention_candidate(value: str) -> str:
    clean = str(value).strip().removeprefix("@").strip().lower()
    if clean.startswith("[[") and clean.endswith("]]"):
        clean = clean[2:-2].strip()
    return re.sub(r"\s+", " ", clean)


def _coerce_receive_batch(
    batch_or_events: ReceiveBatch | list[BandMessageEvent],
) -> ReceiveBatch:
    if isinstance(batch_or_events, ReceiveBatch):
        return batch_or_events

    events = _order_events_for_processing(batch_or_events)
    return ReceiveBatch(
        items=tuple(
            ReceiveBatchItem(event=event, seen_before=False)
            for event in events
        ),
        order_strategy=_event_order_strategy(events),
    )


def _order_events_for_processing(
    events: list[BandMessageEvent],
) -> list[BandMessageEvent]:
    if _can_sort_by_created_at(events):
        return sorted(events, key=lambda event: event.created_at or "")
    return list(events)


def _event_order_strategy(events: list[BandMessageEvent]) -> str:
    if not events:
        return "empty"
    if _can_sort_by_created_at(events):
        return "created_at_ascending"
    return "response_order"


def _can_sort_by_created_at(events: list[BandMessageEvent]) -> bool:
    return bool(events) and all(event.created_at for event in events)


def _extract_band_internal_mentions(content: str) -> list[str]:
    return _normalize_mention_candidates(
        BAND_INTERNAL_MENTION_PATTERN.findall(content)
    )


def _content_has_visible_role_mention(content: str, aliases: set[str]) -> bool:
    normalized_content = re.sub(r"\s+", " ", content.strip().lower())

    for alias in aliases:
        escaped = re.escape(alias)
        if re.search(
            rf"(?<![A-Za-z0-9_.\-/])@{escaped}(?![A-Za-z0-9_.\-/])",
            normalized_content,
        ):
            return True
        if " " in alias and re.match(
            rf"^{escaped}(?![A-Za-z0-9_.\-/])",
            normalized_content,
        ):
            return True

    return False


def _safe_author_summary(event: BandMessageEvent) -> str:
    parts = []
    if event.author_display:
        parts.append(f"display={_preview_text(event.author_display, 80)}")
    if event.author_handle:
        parts.append(f"handle={_preview_text(event.author_handle, 80)}")
    return ", ".join(parts) if parts else "unknown"


def _safe_mention_metadata_summary(event: BandMessageEvent) -> str | None:
    if not event.mention_metadata:
        return None

    summaries: list[str] = []
    for mention in event.mention_metadata:
        fields = []
        for field_name in MENTION_METADATA_PRINT_FIELDS:
            value = mention.get(field_name)
            if value:
                fields.append(f"{field_name}={_preview_text(value, 80)}")
        summaries.append("{" + ", ".join(fields) + "}" if fields else "{fields_present}")

    return f"count={len(event.mention_metadata)} " + " ".join(summaries)


def _preview_text(value: str, max_chars: int) -> str:
    redacted = re.sub(
        r"(?i)\b(api[_-]?key|token|authorization)\s*[:=]\s*\S+",
        r"\1=[REDACTED]",
        str(value),
    )
    redacted = re.sub(
        r"(?i)\bbearer\s+[A-Za-z0-9._\-/]+",
        "Bearer [REDACTED]",
        redacted,
    )
    clean = re.sub(r"\s+", " ", redacted).strip()
    if len(clean) <= max_chars:
        return clean
    return clean[: max_chars - 3] + "..."
