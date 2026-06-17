from app.models import LoanRecord, LoanStatus


class LoanRepository:
    def __init__(self) -> None:
        self._loans = {
            "12345": LoanRecord(
                loan_id="12345",
                applicant_name="Ruthvika Mohan",
                phone_last4="7788",
                status=LoanStatus.UNDER_REVIEW,
                expected_date="2026-06-20",
                emi_amount=18450.0,
                emi_due_day=5,
                payoff_amount=812500.0,
            ),
            "67890": LoanRecord(
                loan_id="67890",
                applicant_name="Aarav Sharma",
                phone_last4="4421",
                status=LoanStatus.DOCUMENTS_REQUIRED,
                expected_date=None,
                required_documents=["latest bank statement", "salary slip", "PAN card copy"],
                emi_amount=9600.0,
                emi_due_day=10,
                payoff_amount=421200.0,
            ),
        }

    def get(self, loan_id: str) -> LoanRecord | None:
        return self._loans.get(loan_id)

    def get_by_phone_last4(self, phone_last4: str) -> LoanRecord | None:
        matches = [loan for loan in self._loans.values() if loan.phone_last4 == phone_last4]
        if len(matches) != 1:
            return None
        return matches[0]

    def verify_identity(self, loan_id: str, phone_last4: str) -> bool:
        loan = self.get(loan_id)
        if not loan:
            return False
        verified = loan.phone_last4 == phone_last4
        loan.identity_verified = verified
        return verified

    def status_payload(self, loan_id: str) -> dict:
        loan = self.get(loan_id)
        if not loan:
            return {"found": False, "message": "No loan application was found for that ID."}

        return {
            "found": True,
            "loan_id": loan.loan_id,
            "status": loan.status.value,
            "expected_date": loan.expected_date,
            "required_documents": loan.required_documents,
        }

    def emi_payload(self, loan_id: str) -> dict:
        loan = self.get(loan_id)
        if not loan:
            return {"found": False, "message": "No EMI schedule was found for that ID."}

        return {
            "found": True,
            "loan_id": loan.loan_id,
            "emi_amount": loan.emi_amount,
            "emi_due_day": loan.emi_due_day,
            "payoff_amount": loan.payoff_amount,
        }


loan_repository = LoanRepository()
