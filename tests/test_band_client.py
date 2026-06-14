import asyncio
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.services.band_client import BandClient  # noqa: E402


class BandClientTests(unittest.TestCase):
    def test_send_text_message_omits_mentions_when_no_handles_are_required(self) -> None:
        _FakeAsyncClient.last_json = None
        client = BandClient("https://band.example/api", "agent-token")

        with patch("app.services.band_client.httpx.AsyncClient", _FakeAsyncClient):
            result = asyncio.run(
                client.send_text_message(
                    chat_id="chat",
                    content="Final commander decision.",
                    mention_handles=[],
                )
            )

        self.assertTrue(result.delivered)
        self.assertEqual(
            _FakeAsyncClient.last_json,
            {"message": {"content": "Final commander decision."}},
        )

    def test_send_text_message_resolves_mentions_and_makes_them_visible(self) -> None:
        _FakeAsyncClient.last_json = None
        _FakeAsyncClient.participants = [
            {
                "id": "compliance-participant",
                "handle": "redhood/workflow-compliance-agent",
                "name": "Workflow Compliance Agent",
            }
        ]
        client = BandClient("https://band.example/api", "agent-token")

        with patch("app.services.band_client.httpx.AsyncClient", _FakeAsyncClient):
            result = asyncio.run(
                client.send_text_message(
                    chat_id="chat",
                    content="Final commander decision.",
                    mention_handles=["redhood/workflow-compliance-agent"],
                )
            )

        self.assertTrue(result.delivered)
        self.assertEqual(
            _FakeAsyncClient.last_json,
            {
                "message": {
                    "content": (
                        "@redhood/workflow-compliance-agent "
                        "Final commander decision."
                    ),
                    "mentions": [
                        {
                            "id": "compliance-participant",
                            "handle": "redhood/workflow-compliance-agent",
                            "name": "Workflow Compliance Agent",
                        }
                    ],
                }
            },
        )

    def test_failed_send_returns_status_only_detail(self) -> None:
        _FakeAsyncClient.next_response = _FakeResponse(
            status_code=422,
            text="raw diagnostic body",
        )
        client = BandClient("https://band.example/api", "agent-token")

        with patch("app.services.band_client.httpx.AsyncClient", _FakeAsyncClient):
            result = asyncio.run(
                client.send_text_message(
                    chat_id="chat",
                    content="Final commander decision.",
                    mention_handles=[],
                )
            )

        self.assertFalse(result.delivered)
        self.assertEqual(result.status_code, 422)
        self.assertEqual(result.detail, "Band rejected the message with status 422.")


class _FakeResponse:
    def __init__(
        self,
        status_code: int = 201,
        text: str = "",
        payload=None,
    ) -> None:
        self.status_code = status_code
        self.text = text
        self._payload = payload if payload is not None else {}

    @property
    def is_success(self) -> bool:
        return 200 <= self.status_code < 300

    def json(self):
        return self._payload

    def raise_for_status(self) -> None:
        return None


class _FakeAsyncClient:
    last_json = None
    next_response = _FakeResponse()
    participants = []

    def __init__(self, timeout) -> None:
        self.timeout = timeout

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback) -> None:
        return None

    async def post(self, url, headers, json):
        _FakeAsyncClient.last_json = json
        response = _FakeAsyncClient.next_response
        _FakeAsyncClient.next_response = _FakeResponse()
        return response

    async def get(self, url, headers):
        return _FakeResponse(payload={"data": list(_FakeAsyncClient.participants)})


if __name__ == "__main__":
    unittest.main()
