from app.domain.intent import classify_intent
from app.domain.loans import LoanRepository
from app.models import AgentRequest, AgentResponse, Intent


class LoanVoiceStateMachine:
    def __init__(self, loans: LoanRepository) -> None:
        self.loans = loans
        self.follow_up = " Is there anything else I can help you with?"

    def handle(self, request: AgentRequest) -> AgentResponse:
        intent, confidence = classify_intent(request.text)

        loan_id = request.loan_id
        inferred_loan = None
        if not loan_id and request.phone_last4:
            inferred_loan = self.loans.get_by_phone_last4(request.phone_last4)
            if inferred_loan:
                loan_id = inferred_loan.loan_id

        if confidence < 0.5:
            return AgentResponse(
                intent=Intent.CLARIFY,
                confidence=confidence,
                text=(
                    "I can help with loan status, EMI information, required documents, "
                    "or connecting you to a loan specialist. What would you like to do?"
                ),
            )

        if intent == Intent.END_CALL:
            return AgentResponse(
                intent=intent,
                confidence=confidence,
                tool_result={"end_call": True},
                text="Thank you for calling. Goodbye.",
            )

        if intent == Intent.HUMAN_HANDOFF:
            return AgentResponse(
                intent=intent,
                confidence=confidence,
                needs_handoff=True,
                tool_result={"transfer": True, "queue": "loan_specialist", "loan_id": loan_id},
                text=(
                    "Certainly. I am transferring you to a loan specialist. "
                    "Please stay on the line while I connect you."
                ),
            )

        if not loan_id:
            return AgentResponse(
                intent=intent,
                confidence=0.6,
                text=(
                    "I can help with that. Please say your loan application ID, "
                    "or enter it on the screen before continuing."
                ),
            )

        if request.phone_last4 and not self.loans.verify_identity(loan_id, request.phone_last4):
            return AgentResponse(
                intent=Intent.IDENTITY_VERIFICATION,
                confidence=0.75,
                text="I could not verify that phone number against the loan application. I can try again or transfer you to a specialist.",
                needs_handoff=True,
                tool_result={"identity_verified": False},
            )

        if intent == Intent.LOAN_STATUS:
            payload = self.loans.status_payload(loan_id)
            if not payload["found"]:
                return self._not_found(intent, confidence)

            if payload["status"] == "Documents Required":
                docs = ", ".join(payload["required_documents"])
                text = f"I found your application. It is waiting on these documents: {docs}."
            elif payload["expected_date"]:
                text = f"I found your application. It is currently {payload['status']}. We expect the next decision by {payload['expected_date']}."
            else:
                text = f"I found your application. It is currently {payload['status']}."
            if inferred_loan:
                text = "I found your application from the caller details. " + text
            text += self.follow_up
            return AgentResponse(intent=intent, confidence=confidence, text=text, tool_result=payload)

        if intent == Intent.EMI_SCHEDULE:
            payload = self.loans.emi_payload(loan_id)
            if not payload["found"]:
                return self._not_found(intent, confidence)

            text = (
                f"Your EMI is {payload['emi_amount']:.0f}, due on day {payload['emi_due_day']} of each month. "
                f"The current payoff amount is {payload['payoff_amount']:.0f}."
            )
            text += self.follow_up
            return AgentResponse(intent=intent, confidence=confidence, text=text, tool_result=payload)

        if intent == Intent.DOCUMENT_REQUIREMENTS:
            payload = self.loans.status_payload(loan_id)
            if not payload["found"]:
                return self._not_found(intent, confidence)

            docs = payload["required_documents"]
            text = "There are no pending document requirements for your application."
            if docs:
                text = "The pending documents are " + ", ".join(docs) + "."
            text += self.follow_up
            return AgentResponse(intent=intent, confidence=confidence, text=text, tool_result=payload)

        return AgentResponse(
            intent=Intent.UNSUPPORTED,
            confidence=0.5,
            needs_handoff=True,
            text="I cannot complete that request in the automated system. I can connect you to a loan specialist.",
        )

    @staticmethod
    def _not_found(intent: Intent, confidence: float) -> AgentResponse:
        return AgentResponse(
            intent=intent,
            confidence=confidence,
            needs_handoff=True,
            text="I could not find a loan application with that ID. I can transfer you to a specialist to look it up another way.",
            tool_result={"found": False},
        )
