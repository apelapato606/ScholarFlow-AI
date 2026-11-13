import streamlit as st
from services.pdf_service import list_papers, stats


def render():
    totals = stats()
    st.markdown('<div class="hero"><div class="eyebrow">Your research workspace</div><h1>Turn dense papers into clear ideas.</h1><p>Read smarter, explore concepts, build presentations, and practise your viva.</p></div>', unsafe_allow_html=True)
    papers = list_papers()
    a,b,c = st.columns(3)
    a.metric("Papers processed", totals["documents"])
    b.metric("Presentations generated", totals["presentations"])
    c.metric("Viva sessions completed", totals["vivas"])
    st.markdown("### Your AI research team")
    cols = st.columns(4)
    cards = [("✧", "Summarizer", "Structured paper briefs"), ("⌕", "Concept Explorer", "Terms, methods and contributions"), ("▤", "Presentation Studio", "Export a polished PPTX"), ("◎", "Viva Practice", "Practice and get feedback")]
    for col, (icon,title,desc) in zip(cols,cards):
        with col: st.markdown('<div class="card agent-card"><span class="agent-icon">{}</span><h3>{}</h3><div class="small-muted">{}</div></div>'.format(icon,title,desc), unsafe_allow_html=True)
    st.markdown("### Recently uploaded")
    if not papers:
        st.info("Your library is empty. Use **Research Library** to add a PDF paper.")
    else:
        for paper in papers[:4]:
            st.markdown('<div class="card"><b>{}</b><br><span class="small-muted">{} · {} pages · {} chunks</span> <span class="pill">{}</span></div>'.format(paper["name"],paper["uploaded_at"][:10],paper["page_count"],paper["chunk_count"],paper["status"]), unsafe_allow_html=True)
    st.markdown("### Recent activity")
    if totals["recent"]:
        for event in totals["recent"][:5]:
            st.markdown("- **{}** — {} · {}".format(event["kind"],event["detail"],event["created_at"][:16]))
    else: st.caption("Your research activity will appear here.")
