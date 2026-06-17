import json
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles

from app.config import Settings, get_settings
from app.domain.loans import loan_repository
from app.domain.state_machine import LoanVoiceStateMachine
from app.models import (
    AgentRequest,
    ToolEmiRequest,
    ToolHumanHandoffRequest,
    ToolLoanStatusRequest,
    ToolVerifyIdentityRequest,
)
from app.services.elevenlabs import ElevenLabsTTS
from app.services.twilio import build_media_stream_twiml

app = FastAPI(title="BFSI Loan Voice Agent", version="0.1.0")
state_machine = LoanVoiceStateMachine(loan_repository)

app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    with open("app/static/index.html", encoding="utf-8") as handle:
        return handle.read()


@app.get("/health")
async def health(settings: Annotated[Settings, Depends(get_settings)]) -> dict:
    return {
        "ok": True,
        "elevenlabs_tts_configured": bool(settings.elevenlabs_api_key),
    }


@app.post("/api/conversation")
async def conversation(request: AgentRequest) -> dict:
    return state_machine.handle(request).model_dump()


@app.post("/api/voice/synthesize")
async def synthesize(request: AgentRequest, settings: Annotated[Settings, Depends(get_settings)]) -> Response:
    response = state_machine.handle(request)
    tts = ElevenLabsTTS(settings)
    if not tts.configured:
        return JSONResponse(
            status_code=503,
            content={
                "error": "ElevenLabs is not configured. Set ELEVENLABS_API_KEY or use the browser speech fallback.",
                "agent_response": response.model_dump(),
            },
        )

    return StreamingResponse(tts.stream_speech(response.text), media_type="audio/mpeg")


def require_tool_secret(x_agent_tool_secret: str | None, settings: Settings) -> None:
    if settings.agent_tool_shared_secret and x_agent_tool_secret != settings.agent_tool_shared_secret:
        raise HTTPException(status_code=401, detail="Invalid agent tool secret.")


@app.post("/tools/get_loan_status")
async def get_loan_status_tool(
    request: ToolLoanStatusRequest,
    settings: Annotated[Settings, Depends(get_settings)],
    x_agent_tool_secret: Annotated[str | None, Header()] = None,
) -> dict:
    require_tool_secret(x_agent_tool_secret, settings)
    return loan_repository.status_payload(request.loan_id)


@app.post("/tools/get_emi_schedule")
async def get_emi_schedule_tool(
    request: ToolEmiRequest,
    settings: Annotated[Settings, Depends(get_settings)],
    x_agent_tool_secret: Annotated[str | None, Header()] = None,
) -> dict:
    require_tool_secret(x_agent_tool_secret, settings)
    return loan_repository.emi_payload(request.loan_id)


@app.post("/tools/verify_identity")
async def verify_identity_tool(
    request: ToolVerifyIdentityRequest,
    settings: Annotated[Settings, Depends(get_settings)],
    x_agent_tool_secret: Annotated[str | None, Header()] = None,
) -> dict:
    require_tool_secret(x_agent_tool_secret, settings)
    verified = loan_repository.verify_identity(request.loan_id, request.phone_last4)
    return {"identity_verified": verified}


@app.post("/tools/transfer_to_human")
async def transfer_to_human_tool(
    request: ToolHumanHandoffRequest,
    settings: Annotated[Settings, Depends(get_settings)],
    x_agent_tool_secret: Annotated[str | None, Header()] = None,
) -> dict:
    require_tool_secret(x_agent_tool_secret, settings)
    return {
        "transfer": True,
        "queue": "loan_specialist",
        "loan_id": request.loan_id,
        "reason": request.reason,
    }


@app.post("/twilio/inbound")
async def twilio_inbound(settings: Annotated[Settings, Depends(get_settings)]) -> Response:
    return Response(build_media_stream_twiml(settings.public_base_url), media_type="application/xml")


@app.websocket("/twilio/media")
async def twilio_media(websocket: WebSocket) -> None:
    await websocket.accept()
    await websocket.send_json({"event": "ready", "message": "Twilio media stream connected."})
    try:
        while True:
            raw = await websocket.receive_text()
            event = json.loads(raw)
            if event.get("event") == "stop":
                await websocket.close()
                return
    except WebSocketDisconnect:
        return

