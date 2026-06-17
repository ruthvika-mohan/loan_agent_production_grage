# BFSI Loan Voice Agent

Reliability-first voice agent for loan status, EMI answers, document requirements, and human handoff. The project is shaped for an ElevenLabs Deployment Strategist style demo: deterministic backend tools, auditable state-machine responses, ElevenLabs speech output, and Twilio-ready telephony hooks.

## What It Demonstrates

- FastAPI backend for enterprise voice workflows
- Deterministic loan status state machine to reduce hallucination risk
- ElevenLabs streaming text-to-speech endpoint
- Browser speech demo with interruption via Stop
- ElevenLabs Agent server tools:
  - `get_loan_status`
  - `get_emi_schedule`
  - `verify_identity`
  - `transfer_to_human`
- Twilio inbound webhook and Media Streams skeleton
- Test coverage for intent routing, handoff, identity failure, and status answers

## Architecture

```text
Browser or Twilio
    |
    v
FastAPI Backend
    |
    v
Intent Classifier -> State Machine -> Tool Layer
    |                                |
    v                                v
ElevenLabs TTS                 Mock Loan Repository
    |
    v
Audio response / human handoff
```

For production, replace the mock repository with real loan APIs and configure ElevenLabs Agents to call the `/tools/*` endpoints.

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
uvicorn app.main:app --reload
```

Open `http://localhost:8000`.

Demo loan records:

- Loan ID `12345`, phone last 4 `7788`
- Loan ID `67890`, phone last 4 `4421`

Without `ELEVENLABS_API_KEY`, the browser demo falls back to browser speech synthesis so you can still test the conversation flow locally.

## ElevenLabs Setup

For TTS-only mode:

1. Add `ELEVENLABS_API_KEY` to `.env`.
2. Optionally change `ELEVENLABS_VOICE_ID`.
3. Run the app and click `Speak` or `Send`.

For ElevenLabs Agents:

1. Create an agent in ElevenLabs.
2. Add server tools that POST to your public backend URL:
   - `POST /tools/get_loan_status`
   - `POST /tools/get_emi_schedule`
   - `POST /tools/verify_identity`
   - `POST /tools/transfer_to_human`
3. Add header `x-agent-tool-secret: <AGENT_TOOL_SHARED_SECRET>`.
4. Give the agent instructions to answer only from tool results and transfer when confidence is low, identity fails, or the customer asks for a specialist.

Example tool input:

```json
{
  "loan_id": "12345"
}
```

Example loan status output:

```json
{
  "found": true,
  "loan_id": "12345",
  "status": "Under Review",
  "expected_date": "2026-06-20",
  "required_documents": []
}
```

## Twilio Setup

Set `PUBLIC_BASE_URL` to your public tunnel or deployment URL, then configure your Twilio voice webhook:

```text
POST https://your-domain.example/twilio/inbound
```

The webhook returns TwiML that connects the call to `/twilio/media`. The WebSocket handler is intentionally a skeleton so you can plug in ElevenLabs Conversational AI or a streaming STT -> LLM -> TTS pipeline.

## Reliability Controls

- Unknown requests trigger clarification.
- Unsupported operations offer human transfer.
- Identity verification failure escalates to handoff.
- Loan facts are returned from tools, not generated freely.
- Tool endpoints use a shared secret header for agent calls.

## Tests

```bash
pytest
```

