import streamlit as st
from agents.slide_generator import generate_outline
from services.presentation_service import create_pptx


def render(paper):
    st.title("Presentation Studio")
    st.caption("Generate a paper-grounded slide outline and download a real editable PowerPoint file.")
    count=st.select_slider("Number of slides",options=[5,8,10,12],value=8)
    if st.button("Generate presentation",type="primary"):
        try:
            with st.spinner("Researching the paper and drafting slides…"):
                outline=generate_outline(paper["id"],paper["name"],count)
                deck=create_pptx(outline,paper["name"])
            st.session_state.last_deck=deck
            st.session_state.last_deck_name=paper["name"]
            st.session_state.last_outline=outline
            st.success("Presentation ready.")
        except Exception as exc: st.error(str(exc))
    if st.session_state.get("last_deck") and st.session_state.get("last_deck_name")==paper["name"]:
        st.download_button("Download PowerPoint (.pptx)",st.session_state.last_deck,file_name="ScholarFlow-{}.pptx".format(paper["name"].rsplit(".",1)[0][:60]),mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",type="primary")
        for i,slide in enumerate(st.session_state.get("last_outline",{}).get("slides",[]),1):
            with st.expander("Slide {} · {}".format(i,slide["title"])):
                for bullet in slide.get("bullets",[]): st.markdown("- "+bullet)
