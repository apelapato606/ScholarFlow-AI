from agents.base import invoke_grounded
from core.prompts import SUMMARY_PROMPT


def summarize(doc_id, title):
    return invoke_grounded(SUMMARY_PROMPT, doc_id, "Summarize the research paper and identify its problem, objectives, method, findings, and conclusion.", {"title": title, "question": "Create a structured research paper summary."})
