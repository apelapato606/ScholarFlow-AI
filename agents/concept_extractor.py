from agents.base import invoke_grounded
from core.prompts import CONCEPT_PROMPT


def explore(doc_id, title, question):
    return invoke_grounded(CONCEPT_PROMPT, doc_id, question, {"title": title, "question": question})
