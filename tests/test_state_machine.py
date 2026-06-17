from app.domain.loans import LoanRepository
from app.domain.state_machine import LoanVoiceStateMachine
from app.models import AgentRequest


def test_returns_loan_status_without_hallucination() -> None:
    machine = LoanVoiceStateMachine(LoanRepository())
    response = machine.handle(
        AgentRequest(text="What's the status of my loan?", loan_id="12345", phone_last4="7788")
    )

    assert response.tool_result["status"] == "Under Review"
    assert "2026-06-20" in response.text
    assert "anything else" in response.text
    assert not response.needs_handoff


def test_transfers_when_customer_asks_for_human() -> None:
    machine = LoanVoiceStateMachine(LoanRepository())
    response = machine.handle(AgentRequest(text="Can I speak to a human?", loan_id="12345"))

    assert response.needs_handoff
    assert response.tool_result["transfer"] is True


def test_identity_failure_escalates() -> None:
    machine = LoanVoiceStateMachine(LoanRepository())
    response = machine.handle(
        AgentRequest(text="What's my loan status?", loan_id="12345", phone_last4="0000")
    )

    assert response.needs_handoff
    assert response.tool_result["identity_verified"] is False


def test_infers_loan_from_caller_phone_context() -> None:
    machine = LoanVoiceStateMachine(LoanRepository())
    response = machine.handle(AgentRequest(text="What's my loan status?", phone_last4="7788"))

    assert response.tool_result["loan_id"] == "12345"
    assert "caller details" in response.text


def test_explicit_goodbye_ends_call() -> None:
    machine = LoanVoiceStateMachine(LoanRepository())
    response = machine.handle(AgentRequest(text="Goodbye", loan_id="12345"))

    assert response.intent == "end_call"
    assert response.tool_result["end_call"] is True
