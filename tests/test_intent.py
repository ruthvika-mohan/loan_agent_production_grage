from app.domain.intent import classify_intent
from app.models import Intent


def test_classifies_human_handoff() -> None:
    intent, confidence = classify_intent("Can I speak to a representative?")
    assert intent == Intent.HUMAN_HANDOFF
    assert confidence > 0.7


def test_classifies_loan_status() -> None:
    intent, confidence = classify_intent("What is the status of my application?")
    assert intent == Intent.LOAN_STATUS
    assert confidence > 0.7


def test_clarifies_unknown_request() -> None:
    intent, confidence = classify_intent("Tell me a joke")
    assert intent == Intent.CLARIFY
    assert confidence < 0.5

