import streamlit as st
from pathlib import Path
from core.memory import init_memory
from core.llm import get_api_key, get_model_name, test_groq_connection
from services.pdf_service import list_papers
from ui import dashboard, library, assistant, presentation, viva

st.set_page_config(page_title="ScholarFlow AI",page_icon="✧",layout="wide",initial_sidebar_state="auto")
st.markdown(Path(__file__).parent.joinpath("ui/styles.css").read_text(),unsafe_allow_html=True)
init_memory()

NAVIGATION_ICONS = {
    "Overview": "◫", "Research Library": "▤", "Paper Assistant": "✧",
    "Concept Explorer": "⌕", "Presentation Studio": "▣", "Viva Practice": "◎",
    "Session Reports": "▥", "Settings": "⚙",
}

with st.sidebar:
    st.markdown("<div style='padding:15px 6px 20px'><div style='font-size:12px;letter-spacing:.15em;color:#bcb0ff;font-weight:700'>✧ SCHOLARFLOW</div><div style='font-size:21px;font-weight:800;font-family:Manrope;margin-top:4px'>Research, clarified.</div></div>",unsafe_allow_html=True)
    pages=["Overview","Research Library","Paper Assistant","Concept Explorer","Presentation Studio","Viva Practice","Session Reports","Settings"]
    page=st.radio("Workspace",pages,format_func=lambda section:"{}  {}".format(NAVIGATION_ICONS[section],section),label_visibility="collapsed")
    st.markdown("---")
    papers=list_papers()
    ready=[p for p in papers if p["status"]=="Ready"]
    selected=next((p for p in ready if p["id"]==st.session_state.selected_doc_id),None)
    if not selected and ready:
        selected=ready[0]; st.session_state.selected_doc_id=selected["id"]
    st.caption("ACTIVE PAPER")
    if ready:
        selected_id=st.selectbox("Select paper",[p["id"] for p in ready],index=next((i for i,p in enumerate(ready) if p["id"]==selected["id"]),0),format_func=lambda doc_id: next((p["name"] for p in ready if p["id"]==doc_id),doc_id),label_visibility="collapsed",key="active_paper_select")
        selected=next(p for p in ready if p["id"]==selected_id)
        st.session_state.selected_doc_id=selected["id"]
    else:
        st.caption("Upload a PDF to begin")
    st.markdown("<div style='padding:10px 5px;color:#aaa5c6;font-size:11px'>GROQ · LANGCHAIN · CHROMA</div>",unsafe_allow_html=True)

if page=="Overview": dashboard.render()
elif page=="Research Library": library.render()
elif page in ("Paper Assistant","Concept Explorer"):
    if selected:
        if page=="Concept Explorer":
            st.title("Concept Explorer")
            st.caption("Explore technical language, methods, algorithms, technologies, contributions, and results from your selected paper.")
            with st.form("concept_form"):
                concept_query=st.text_input("What would you like to understand?",placeholder="Explain the paper's main methodology in simple language")
                go=st.form_submit_button("Explore concept",type="primary")
            if go:
                if concept_query:
                    try:
                        from agents.concept_extractor import explore
                        with st.spinner("Retrieving relevant sections and explaining…"): result=explore(selected["id"],selected["name"],concept_query)
                        st.markdown(result)
                        st.session_state.conversation.append({"question":concept_query,"answer":result,"doc_id":selected["id"]})
                    except Exception as exc: st.error(str(exc))
                else: st.warning("Enter a concept or question first.")
            with st.expander("Recent exploration in this session"):
                for turn in st.session_state.conversation:
                    if turn.get("doc_id")==selected["id"]:
                        st.markdown("**{}**\n\n{}".format(turn["question"],turn["answer"]))
        else: assistant.render(selected)
    else: st.info("Upload and select a paper in Research Library to use the assistant.")
elif page=="Presentation Studio":
    presentation.render(selected) if selected else st.info("Upload and select a paper to generate a presentation.")
elif page=="Viva Practice":
    viva.render(selected) if selected else st.info("Upload and select a paper to start viva practice.")
elif page=="Session Reports":
    st.title("Session Reports")
    report=st.session_state.get("viva_report")
    session=st.session_state.get("viva_session")
    if report:
        st.success("Your latest viva report is ready.")
        st.download_button("Download viva report (.xlsx)",report,file_name="ScholarFlow-viva-report.xlsx",mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",type="primary")
    elif session and session.get("index",0)>=len(session.get("questions",[])) and session.get("results"):
        st.info("Viva session complete. Generate its report from Viva Practice.")
    else: st.info("Completed viva reports will appear here after a session report is generated.")
    if session and session.get("results"):
        scores=[r["evaluation"]["score"] for r in session["results"]]
        st.markdown("### Current session")
        st.write("Paper: **{}** · Questions attempted: **{}** · Average: **{:.1f}/10**".format(session["paper_name"],len(scores),sum(scores)/len(scores)))
elif page=="Settings":
    st.title("Settings")
    st.markdown("### Model connection")
    if get_api_key(): st.success("Groq API key is configured. Selected model: {}".format(get_model_name()))
    else: st.warning("Groq API key is not configured. AI features require your own key; no mock responses are used.")
    if st.button("Test Groq connection", type="primary", disabled=not bool(get_api_key())):
        with st.spinner("Checking the configured model with a live Groq request…"):
            try:
                response = test_groq_connection()
                st.success("Connection succeeded with {}.".format(get_model_name()))
                st.caption("Model response: {}".format(response[:240]))
            except Exception as exc:
                st.error(str(exc))
    st.markdown("Set `GROQ_API_KEY` in your environment, or add `GROQ_API_KEY = \"gsk_…\"` to `.streamlit/secrets.toml`. You can copy `.streamlit/secrets.toml.example` as a starting point.")
    st.markdown("### Local data")
    st.write("PDFs, SQLite metadata, and the persistent Chroma index are stored under `data/`. These files are excluded from Git.")
