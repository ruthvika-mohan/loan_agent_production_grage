from app.models import Intent


INTENT_KEYWORDS: list[tuple[Intent, tuple[str, ...]]] = [
    (Intent.HUMAN_HANDOFF, ("representative", "human", "agent", "specialist", "transfer", "call back")),
    (Intent.EMI_SCHEDULE, ("emi", "payment", "installment", "due", "payoff", "balance")),
    (Intent.DOCUMENT_REQUIREMENTS, ("document", "documents", "upload", "statement", "salary slip", "pan")),
    (Intent.LOAN_STATUS, ("status", "application", "approved", "underwriting", "review", "decision")),
    (Intent.IDENTITY_VERIFICATION, ("verify", "identity", "otp", "last four")),
]


def classify_intent(text: str) -> tuple[Intent, float]:
    normalized = text.lower()
    scores: dict[Intent, int] = {}
    for intent, keywords in INTENT_KEYWORDS:
        scores[intent] = sum(1 for keyword in keywords if keyword in normalized)

    best_intent = max(scores, key=scores.get)
    best_score = scores[best_intent]

    if best_score == 0:
        return Intent.CLARIFY, 0.35

    confidence = min(0.95, 0.55 + best_score * 0.18)
    return best_intent, confidence

