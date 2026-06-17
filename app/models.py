from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class LoanStatus(StrEnum):
    RECEIVED = "Received"
    UNDER_REVIEW = "Under Review"
    DOCUMENTS_REQUIRED = "Documents Required"
    APPROVED = "Approved"
    FUNDED = "Funded"
    DECLINED = "Declined"


class Intent(StrEnum):
    LOAN_STATUS = "loan_status"
    EMI_SCHEDULE = "emi_schedule"
    DOCUMENT_REQUIREMENTS = "document_requirements"
    HUMAN_HANDOFF = "human_handoff"
    END_CALL = "end_call"
    IDENTITY_VERIFICATION = "identity_verification"
    CLARIFY = "clarify"
    UNSUPPORTED = "unsupported"


class LoanRecord(BaseModel):
    loan_id: str
    applicant_name: str
    phone_last4: str
    status: LoanStatus
    expected_date: str | None = None
    required_documents: list[str] = Field(default_factory=list)
    emi_amount: float | None = None
    emi_due_day: int | None = None
    payoff_amount: float | None = None
    identity_verified: bool = False


class AgentRequest(BaseModel):
    text: str
    loan_id: str | None = None
    phone_last4: str | None = None
    session_id: str = "demo"


class SpeechRequest(BaseModel):
    text: str


class AgentResponse(BaseModel):
    intent: Intent
    text: str
    confidence: float
    needs_handoff: bool = False
    tool_result: dict[str, Any] = Field(default_factory=dict)


class ToolLoanStatusRequest(BaseModel):
    loan_id: str


class ToolEmiRequest(BaseModel):
    loan_id: str


class ToolVerifyIdentityRequest(BaseModel):
    loan_id: str
    phone_last4: str


class ToolHumanHandoffRequest(BaseModel):
    loan_id: str | None = None
    reason: str = "customer_requested"
