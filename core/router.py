"""Intent classification and agent routing."""
from core.prompts import ROUTER_PROMPT
from core.llm import invoke_lcel

KEYWORDS = {
    "summarise": ("summar", "abstract", "overview", "explain this paper"),
    "concepts": ("concept", "term", "methodolog", "algorithm", "contribution", "technology"),
    "presentation": ("slide", "presentation", "powerpoint", "ppt"),
    "viva_evaluation": ("evaluate my answer", "grade my answer", "score my answer", "evaluate my viva answer"),
    "viva_questions": ("viva", "practice question", "quiz", "question me"),
}


def detect_intent(request, llm=None):
    text = request.lower()
    for intent, words in KEYWORDS.items():
        if any(word in text for word in words):
            return intent
    try:
        if llm is not None:
            label = (ROUTER_PROMPT | llm).invoke({"request": request}).content.strip().lower()
        else:
            label = invoke_lcel(ROUTER_PROMPT, {"request": request}, temperature=0).strip().lower()
        if label in {"summarise", "concepts", "presentation", "viva_questions", "viva_evaluation", "question_answer"}:
            return label
    except Exception:
        pass
    return "question_answer"
