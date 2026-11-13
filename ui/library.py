import streamlit as st
from services.pdf_service import ingest_pdf, list_papers, delete_paper, PAPERS_DIR


def render():
    st.title("Research Library")
    st.caption("Upload and manage paper PDFs. Text is indexed per paper for grounded retrieval.")
    upload = st.file_uploader("Upload a research paper", type=["pdf"], key="paper_upload")
    if upload is not None and st.button("Process paper", type="primary"):
        try:
            with st.spinner("Extracting pages, generating embeddings, and indexing in ChromaDB…"):
                result = ingest_pdf(upload.name, upload.getvalue())
            st.session_state.selected_doc_id = result["id"]
            st.success("{} is ready ({} pages, {} indexed chunks).".format(result["name"],result["page_count"],result["chunk_count"]))
        except Exception as exc: st.error(str(exc))
    papers = list_papers()
    if not papers:
        st.info("No papers yet. Upload a PDF above to begin.")
        return
    st.markdown("### Your papers")
    for paper in papers:
        with st.container(border=True):
            left, mid, right = st.columns([5,2,2])
            with left:
                st.markdown("**{}**".format(paper["name"]))
                st.caption("Uploaded {} · {} pages · {} chunks".format(paper["uploaded_at"][:10],paper["page_count"],paper["chunk_count"]))
                if paper.get("error"): st.error(paper["error"])
            with mid:
                st.markdown("`{}`".format(paper["status"]))
                if st.button("{} Select".format("✓" if st.session_state.selected_doc_id == paper["id"] else ""),key="select_"+paper["id"]):
                    st.session_state.selected_doc_id=paper["id"]
                    st.rerun()
            with right:
                path=PAPERS_DIR/(paper["id"]+".pdf")
                if path.exists(): st.download_button("Open / download PDF",path.read_bytes(),file_name=paper["name"],mime="application/pdf",key="pdf_"+paper["id"])
                if st.button("Delete",key="delete_"+paper["id"]):
                    delete_paper(paper["id"])
                    if st.session_state.selected_doc_id==paper["id"]: st.session_state.selected_doc_id=None
                    st.rerun()
