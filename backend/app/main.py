from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.core.settings import settings
from app.models.incident import IncidentState
from app.services.band_client import (
    BandClient,
    BandConfigurationError,
    BandDeliveryResult,
    extract_mention_handles,
    normalize_mention_handles,
)
from app.services.deterministic_agents import run_deterministic_workflow
from app.services.final_report import build_final_report
from app.services.incident_repository import DEMO_INCIDENT_ID, incident_repository


class StartIncidentRequest(BaseModel):
    reset: bool = True
    post_to_band: bool = False


class TestBandMessageRequest(BaseModel):
    content: str = "Workflow Legion test: Triage Agent online."
    mention_handles: list[str] | None = None


class WorkflowRunResponse(BaseModel):
    incident: IncidentState
    band_delivery: list[BandDeliveryResult]


app = FastAPI(
    title="Workflow Legion API",
    description="Band-native cyber incident command room backend.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "workflow-legion-api",
        "band_configured": bool(
            settings.band_chat_id and settings.band_triage_agent_api_key
        ),
    }


@app.get("/api/incidents/wl-inc-001")
def get_demo_incident():
    incident = incident_repository.get(DEMO_INCIDENT_ID)
    if incident is None:
        raise HTTPException(status_code=404, detail="Demo incident not found.")

    return incident


@app.post("/api/incidents/wl-inc-001/reset")
def reset_demo_incident():
    return incident_repository.reset_demo()


@app.post("/api/incidents/wl-inc-001/start", response_model=WorkflowRunResponse)
async def start_demo_incident(request: StartIncidentRequest):
    incident = (
        incident_repository.reset_demo()
        if request.reset
        else incident_repository.get(DEMO_INCIDENT_ID)
    )

    if incident is None:
        raise HTTPException(status_code=404, detail="Demo incident not found.")

    incident.status = "running"
    incident_repository.upsert(incident)

    findings = run_deterministic_workflow(
        incident,
        threat_handle=settings.band_threat_intel_handle,
        forensics_handle=settings.band_forensics_handle,
        compliance_handle=settings.band_compliance_handle,
        commander_handle=settings.band_commander_handle,
    )

    report = build_final_report(incident, findings)
    completed_incident = incident_repository.replace_findings(
        incident.incident_id,
        findings,
        report,
    )

    if completed_incident is None:
        raise HTTPException(status_code=404, detail="Demo incident not found.")

    band_delivery: list[BandDeliveryResult] = []

    if request.post_to_band:
        band_delivery = await _post_workflow_to_band(
            [finding.band_message for finding in findings]
        )

    return WorkflowRunResponse(
        incident=completed_incident,
        band_delivery=band_delivery,
    )


@app.get("/api/incidents/wl-inc-001/report")
def get_demo_incident_report():
    incident = incident_repository.get(DEMO_INCIDENT_ID)

    if incident is None:
        raise HTTPException(status_code=404, detail="Demo incident not found.")

    if incident.final_report is None:
        raise HTTPException(
            status_code=404,
            detail="Final report has not been generated yet.",
        )

    return incident.final_report


@app.post("/api/band/test-message", response_model=BandDeliveryResult)
async def send_band_test_message(request: TestBandMessageRequest):
    client = _build_triage_band_client()

    try:
        return await client.send_text_message(
            _required_band_chat_id(),
            request.content,
            mention_handles=_band_message_mention_handles(
                request.content,
                request.mention_handles,
            ),
        )
    except BandConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


def _build_triage_band_client() -> BandClient:
    return BandClient(
        base_url=settings.band_base_url,
        agent_api_key=settings.band_triage_agent_api_key,
    )


def _required_band_chat_id() -> str:
    if not settings.band_chat_id:
        raise BandConfigurationError("Band chat ID is not configured.")

    return settings.band_chat_id


def _default_band_mention_handles() -> list[str]:
    raw_handles = settings.band_default_mention_handles or "redhood"
    return normalize_mention_handles(raw_handles.split(","))


def _band_message_mention_handles(
    message: str,
    explicit_handles: list[str] | None = None,
) -> list[str]:
    if explicit_handles is not None:
        return normalize_mention_handles(explicit_handles)

    return extract_mention_handles(message) or _default_band_mention_handles()


async def _post_workflow_to_band(messages: list[str]) -> list[BandDeliveryResult]:
    client = _build_triage_band_client()
    chat_id = _required_band_chat_id()
    delivery: list[BandDeliveryResult] = []

    try:
        for message in messages:
            delivery.append(
                await _send_workflow_message_to_band(client, chat_id, message)
            )
    except BandConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return delivery


async def _send_workflow_message_to_band(
    client: BandClient,
    chat_id: str,
    message: str,
) -> BandDeliveryResult:
    mention_handles = _band_message_mention_handles(message)

    try:
        return await client.send_text_message(
            chat_id,
            message,
            mention_handles=mention_handles,
        )
    except BandConfigurationError as exc:
        default_handles = _default_band_mention_handles()
        if mention_handles == default_handles:
            raise

        # Keep the demo honest: role handoff text stays visible, but the
        # mention payload falls back until those remote agents join the room.
        fallback_result = await client.send_text_message(
            chat_id,
            message,
            mention_handles=default_handles,
        )
        if fallback_result.delivered:
            return BandDeliveryResult(
                delivered=True,
                detail=(
                    f"{fallback_result.detail} Used default mention handles because "
                    f"workflow role mention resolution failed: {exc}"
                ),
                status_code=fallback_result.status_code,
            )

        return fallback_result
