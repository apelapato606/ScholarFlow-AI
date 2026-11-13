from agents.base import get_context, parse_json
from core.llm import invoke_lcel
from core.prompts import VIVA_QUESTION_PROMPT, EVALUATE_PROMPT


def generate_questions(doc_id, title, difficulty="Intermediate", count=5):
    _, context = get_context(doc_id, "research question methods contribution results limitations future work")
    raw = invoke_lcel(VIVA_QUESTION_PROMPT, {"title": title, "difficulty": difficulty, "count": count, "context": context}, temperature=0.35)
    questions = parse_json(raw).get("questions", [])
    if not questions:
        raise ValueError("No viva questions were generated. Please retry.")
    return questions[:count]


def evaluate_answer(doc_id, question, model_answer, answer):
    _, context = get_context(doc_id, question + " " + answer)
    raw = invoke_lcel(EVALUATE_PROMPT, {"context": context, "question": question, "model_answer": model_answer, "answer": answer}, temperature=0.1)
    result = parse_json(raw)
    for key in ("correctness", "relevance", "completeness", "score"):
        result[key] = max(0.0, min(10.0, float(result[key])))
    return result
