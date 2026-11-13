"""Downloadable viva performance reports."""
from io import BytesIO
import pandas as pd
from services.pdf_service import record_activity


def build_report(paper_name, results):
    if not results:
        raise ValueError("This viva session has no submitted answers yet.")
    rows = []
    for i, result in enumerate(results, 1):
        rows.append({"Question": i, "Prompt": result["question"], "Score / 10": result["evaluation"]["score"], "Correctness": result["evaluation"]["correctness"], "Relevance": result["evaluation"]["relevance"], "Completeness": result["evaluation"]["completeness"], "Feedback": result["evaluation"]["feedback"]})
    scores = [r["Score / 10"] for r in rows]
    strengths = list(dict.fromkeys(s for r in results for s in r["evaluation"].get("strengths", [])))
    weak = list(dict.fromkeys(s for r in results for s in r["evaluation"].get("missing_concepts", [])))
    out = BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        pd.DataFrame([{"Research paper": paper_name, "Questions attempted": len(rows), "Overall score / 10": round(sum(scores) / len(scores), 2), "Strengths": "; ".join(strengths), "Weak areas": "; ".join(weak), "Suggested improvements": "Review the weak areas and use evidence from the paper when explaining your answers.", "Recommended topics": "; ".join(weak)}]).to_excel(writer, sheet_name="Summary", index=False)
        pd.DataFrame(rows).to_excel(writer, sheet_name="Question details", index=False)
    record_activity("Viva completed", paper_name)
    return out.getvalue()
