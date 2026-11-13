import streamlit as st
from agents.viva_agent import generate_questions, evaluate_answer
from services.report_service import build_report


def render(paper):
    st.title("Viva Practice")
    st.caption("Questions are generated from this paper, then each answer receives paper-grounded feedback.")
    state=st.session_state
    with st.sidebar:
        pass
    difficulty=st.selectbox("Difficulty",["Easy","Intermediate","Difficult"],index=["Easy","Intermediate","Difficult"].index(state.selected_difficulty),key="viva_difficulty")
    state.selected_difficulty=difficulty
    count=st.selectbox("Questions in session",[3,5,8],index=1)
    if st.button("Start Viva",type="primary"):
        try:
            with st.spinner("Preparing paper-grounded questions…"):
                questions=generate_questions(paper["id"],paper["name"],difficulty,count)
            state.viva_session={"doc_id":paper["id"],"paper_name":paper["name"],"questions":questions,"index":0,"results":[]}
            st.rerun()
        except Exception as exc: st.error(str(exc))
    session=state.get("viva_session")
    if not session or session.get("doc_id")!=paper["id"]: return
    questions=session["questions"]; i=session["index"]
    st.progress(min(i/len(questions),1.0),text="Question {} of {}".format(min(i+1,len(questions)),len(questions)))
    if i>=len(questions):
        st.success("Viva complete. Final score: {:.1f} / 10".format(sum(r["evaluation"]["score"] for r in session["results"])/len(session["results"])))
        if st.button("Create session report"):
            try: state.viva_report=build_report(session["paper_name"],session["results"])
            except Exception as exc: st.error(str(exc))
        if state.get("viva_report"):
            st.download_button("Download report (.xlsx)",state.viva_report,file_name="ScholarFlow-viva-report.xlsx",mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        st.markdown("### Performance overview")
        for result in session["results"]:
            with st.expander("{:.1f}/10 · {}".format(result["evaluation"]["score"],result["question"])):
                st.write(result["evaluation"]["feedback"])
                if result["evaluation"].get("missing_concepts"): st.write("Review: "+", ".join(result["evaluation"]["missing_concepts"]))
        return
    question=questions[i]
    st.markdown('<div class="card"><span class="pill">{}</span><h3>{}</h3></div>'.format(difficulty,question["question"]),unsafe_allow_html=True)
    with st.form("answer_form_{}_{}".format(session["doc_id"],i)):
        answer=st.text_area("Your answer",height=160,placeholder="Explain your answer in your own words…")
        submitted=st.form_submit_button("Submit answer",type="primary")
    if submitted:
        if not answer.strip(): st.warning("Write an answer before submitting.")
        else:
            try:
                with st.spinner("Evaluating correctness, relevance and completeness…"):
                    evaluation=evaluate_answer(session["doc_id"],question["question"],question["model_answer"],answer)
                session["results"].append({"question":question["question"],"answer":answer,"evaluation":evaluation})
                st.rerun()
            except Exception as exc: st.error(str(exc))
    if i<len(session["results"]):
        result=session["results"][i]
        st.metric("Answer score", "{:.1f} / 10".format(result["evaluation"]["score"]))
        st.write(result["evaluation"]["feedback"])
        a,b,c=st.columns(3); a.metric("Correctness",result["evaluation"]["correctness"]); b.metric("Relevance",result["evaluation"]["relevance"]); c.metric("Completeness",result["evaluation"]["completeness"])
        if result["evaluation"].get("missing_concepts"): st.warning("Missing concepts: "+", ".join(result["evaluation"]["missing_concepts"]))
        with st.expander("Model answer"): st.write(question["model_answer"])
        if st.button("Next question",type="primary",key="next_"+str(i)):
            session["index"]+=1; st.rerun()
