import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import httpx


MENTION_HANDLE_PATTERN = re.compile(r"@([A-Za-z0-9_.\-/]+)")


class BandConfigurationError(RuntimeError):
    pass


@dataclass(frozen=True)
class BandDeliveryResult:
    delivered: bool
    detail: str
    status_code: int | None = None


def normalize_mention_handle(handle: str) -> str:
    return handle.strip().removeprefix("@").lower()


def normalize_mention_handles(handles: Sequence[str] | None) -> list[str]:
    normalized: list[str] = []

    for handle in handles or []:
        clean = normalize_mention_handle(str(handle))
        if clean and clean not in normalized:
            normalized.append(clean)

    return normalized


def extract_mention_handles(content: str) -> list[str]:
    return normalize_mention_handles(MENTION_HANDLE_PATTERN.findall(content))


class BandClient:
    def __init__(self, base_url: str, agent_api_key: str | None) -> None:
        self._base_url = base_url.rstrip("/")
        self._agent_api_key = agent_api_key

    @property
    def configured(self) -> bool:
        return bool(self._base_url and self._agent_api_key)

    def _headers(self) -> dict[str, str]:
        if not self._agent_api_key:
            raise BandConfigurationError("Band agent API key is not configured.")

        return {
            "X-API-Key": self._agent_api_key,
            "Content-Type": "application/json",
        }

    async def get_current_agent_profile(self) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{self._base_url}/agent/me",
                headers=self._headers(),
            )

        response.raise_for_status()
        return response.json()

    async def get_chat_participants(self, chat_id: str) -> list[dict[str, Any]]:
        if not chat_id:
            raise BandConfigurationError("Band chat ID is not configured.")

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{self._base_url}/agent/chats/{chat_id}/participants",
                headers=self._headers(),
            )

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise BandConfigurationError(
                f"Band participant lookup failed with status {response.status_code}: "
                f"{response.text}"
            ) from exc

        payload = response.json()
        participants = payload.get("data", [])

        if isinstance(participants, dict):
            participants = participants.get("participants", [])

        if not isinstance(participants, list):
            raise BandConfigurationError("Band participants response was not a list.")

        return participants

    async def send_text_message(
        self,
        chat_id: str,
        content: str,
        mention_handles: list[str] | None = None,
    ) -> BandDeliveryResult:
        if not chat_id:
            raise BandConfigurationError("Band chat ID is not configured.")
        if not content.strip():
            raise ValueError("Band message content cannot be empty.")

        handles = normalize_mention_handles(
            mention_handles
            if mention_handles is not None
            else extract_mention_handles(content)
        )
        mentions = await self._resolve_mentions(chat_id, handles) if handles else []
        message_content = self._ensure_visible_mentions(content, mentions)

        payload = {
            "message": {
                "content": message_content,
                "mentions": mentions,
            }
        }

        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                f"{self._base_url}/agent/chats/{chat_id}/messages",
                headers=self._headers(),
                json=payload,
            )

        if response.is_success:
            return BandDeliveryResult(
                delivered=True,
                detail="Message delivered to Band.",
                status_code=response.status_code,
            )

        return BandDeliveryResult(
            delivered=False,
            detail=f"Band rejected the message: {response.text}",
            status_code=response.status_code,
        )

    async def _resolve_mentions(
        self,
        chat_id: str,
        mention_handles: list[str],
    ) -> list[dict[str, str]]:
        participants = await self.get_chat_participants(chat_id)
        by_handle = {
            normalize_mention_handle(str(participant.get("handle", ""))): participant
            for participant in participants
            if participant.get("handle")
        }

        mentions: list[dict[str, str]] = []

        for handle in mention_handles:
            participant = by_handle.get(normalize_mention_handle(handle))

            if not participant:
                available = ", ".join(sorted(by_handle.keys())) or "none"
                raise BandConfigurationError(
                    f"Band mention handle not found: {handle}. "
                    f"Available handles: {available}"
                )

            mentions.append(
                {
                    "id": self._required_participant_value(participant, "id"),
                    "handle": self._required_participant_value(
                        participant,
                        "handle",
                    ).removeprefix("@"),
                    "name": self._required_participant_value(participant, "name"),
                }
            )

        return mentions

    def _required_participant_value(
        self,
        participant: dict[str, Any],
        field_name: str,
    ) -> str:
        value = participant.get(field_name)
        if value is None or str(value).strip() == "":
            raise BandConfigurationError(
                f"Band participant was missing required field: {field_name}"
            )

        return str(value)

    def _ensure_visible_mentions(
        self,
        content: str,
        mentions: list[dict[str, str]],
    ) -> str:
        message_content = content.strip()

        for mention in reversed(mentions):
            handle = mention["handle"]
            visible_token = f"@{handle}"

            if not self._has_visible_mention(message_content, handle):
                message_content = f"{visible_token} {message_content}"

        return message_content

    def _has_visible_mention(self, content: str, handle: str) -> bool:
        escaped_handle = re.escape(handle)
        pattern = rf"(?<![A-Za-z0-9_.\-/])@{escaped_handle}(?![A-Za-z0-9_.\-/])"
        return re.search(pattern, content, flags=re.IGNORECASE) is not None
