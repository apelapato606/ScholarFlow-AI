"""Shared grounded LCEL execution utilities."""
import json
from core.llm import invoke_lcel
from core.rag_pipeline import retrieve, format_context


def get_context(doc_id, query, k=7):
    docs = retrieve(doc_id, query, k=k)
    if not docs:
        raise RuntimeError("No relevant indexed text was found for this request.")
    return docs, format_context(docs)


def invoke_grounded(prompt, doc_id, query, variables, temperature=0.2):
    _, context = get_context(doc_id, query)
    payload = dict(variables)
    payload["context"] = context
    return invoke_lcel(prompt, payload, temperature=temperature)


def parse_json(text):
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0]
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("The AI returned an unexpected format. Please retry.")
    return json.loads(text[start:end + 1])
