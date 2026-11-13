import streamlit as st
from agents.summarizer import summarize
from agents.concept_extractor import explore
from agents.slide_generator import generate_outline
from agents.viva_agent import generate_questions, evaluate_answer
from agents.base import invoke_grounded
from core.prompts import QA_PROMPT
from core.router import detect_intent
from core.memory import add_turn
from services.presentation_service import create_pptx


def _route_request(request, paper):
    intent=detect_intent(request)
    if intent=="summarise":
        return intent,summarize(paper["id"],paper["name"])
    if intent=="concepts":
        return intent,explore(paper["id"],paper["name"],request)
    if intent=="presentation":
        outline=generate_outline(paper["id"],paper["name"],8)
        deck=create_pptx(outline,paper["name"])
        st.session_state.last_deck=deck
        st.session_state.last_deck_name=paper["name"]
        st.session_state.last_outline=outline
        return intent,"I generated an 8-slide presentation outline grounded in the paper. Download the editable PowerPoint below."
    if intent=="viva_questions":
        questions=generate_questions(paper["id"],paper["name"],st.session_state.selected_difficulty,5)
        st.session_state.assistant_viva_questions=questions
        return intent,"Generated 5 {} viva questions from the selected paper. Expand the question set below to review model answers.".format(st.session_state.selected_difficulty.lower())
    if intent=="viva_evaluation":
        session=st.session_state.get("viva_session")
        if not session or session.get("doc_id")!=paper["id"]:
            return intent,"Start a Viva Practice session first, then submit your answer there for evaluation."
        index=min(session.get("index",0),len(session.get("questions",[]))-1)
        if index<0:
            return intent,"Start a Viva Practice session first, then submit your answer there for evaluation."
        question=session["questions"][index]
        answer=request.split(":",1)[1].strip() if ":" in request else request
        evaluation=evaluate_answer(paper["id"],question["question"],question["model_answer"],answer)
        return intent,"**Score: {:.1f}/10**\n\n{}\n\nMissing concepts: {}".format(evaluation["score"],evaluation["feedback"],", ".join(evaluation.get("missing_concepts",[])) or "None identified")
    return intent,invoke_grounded(QA_PROMPT,paper["id"],request,{"title":paper["name"],"question":request})


def render(paper):
    st.title("Paper Assistant")
    st.caption("Ask in natural language. The intent router selects a specialist agent, and retrieval stays within the selected paper.")
    with st.expander("What can I ask?"):
        st.write("Summarize this paper; explain a concept or method; make a presentation; generate viva questions; or ask a question about the paper. To evaluate a viva answer, start Viva Practice and submit it there, or ask ‘evaluate my answer: …’ while a viva session is active.")
    for turn in st.session_state.conversation:
        if turn.get("doc_id") != paper["id"]: continue
        with st.chat_message("user"): st.write(turn["question"])
        with st.chat_message("assistant"): st.markdown(turn["answer"])
    request=st.chat_input("Ask about {}…".format(paper["name"]))
    if request:
        try:
            with st.spinner("Detecting intent and grounding the response in this paper…"):
                intent,answer=_route_request(request,paper)
            add_turn(request,answer,paper["id"])
            st.rerun()
        except Exception as exc: st.error(str(exc))
    if st.session_state.get("assistant_viva_questions"):
        with st.expander("Generated viva questions and model answers"):
            for i,item in enumerate(st.session_state.assistant_viva_questions,1):
                st.markdown("**{}. {}**\n\nModel answer: {}".format(i,item["question"],item["model_answer"]))
    if st.session_state.get("last_deck") and st.session_state.get("last_deck_name")==paper["name"]:
        st.download_button("Download generated PowerPoint (.pptx)",st.session_state.last_deck,file_name="ScholarFlow-assistant-slides.pptx",mime="application/vnd.openxmlformats-officedocument.presentationml.presentation")
    if st.button("Generate structured summary",type="primary",key="standalone_summary"):
        try:
            with st.spinner("Summarizing retrieved paper sections…"): st.markdown(summarize(paper["id"],paper["name"]))
        except Exception as exc: st.error(str(exc))
