from agents.base import get_context, parse_json
from core.llm import invoke_lcel
from core.prompts import SLIDE_PROMPT


def generate_outline(doc_id, title, count):
    _, context = get_context(doc_id, "paper contributions methodology results conclusion objectives")
    raw = invoke_lcel(SLIDE_PROMPT, {"title": title, "count": count, "context": context}, temperature=0.25)
    data = parse_json(raw)
    slides = data.get("slides", [])
    if len(slides) != count:
        raise ValueError("The generated outline did not contain exactly {} slides. Please retry.".format(count))
    return data
