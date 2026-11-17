import streamlit as st
from agents.slide_generator import generate_outline
from services.presentation_service import (
    PRESENTATION_STYLES,
    STYLE_ACADEMIC,
    STYLE_INFOGRAPHIC,
    STYLE_MODERN,
    create_pptx,
)


STYLE_DESCRIPTIONS = {
    STYLE_ACADEMIC: "Formal, structured layouts with navy headings and a white background.",
    STYLE_MODERN: "A dark navy and violet theme for visually engaging project demonstrations.",
    STYLE_INFOGRAPHIC: "Blue, teal and white visual layouts with diagrams where useful.",
}

STYLE_PREVIEWS = {
    STYLE_ACADEMIC: ("#ffffff", "#19315c", "#5b67be"),
    STYLE_MODERN: ("#171434", "#ffffff", "#9d77ff"),
    STYLE_INFOGRAPHIC: ("#f6fbfc", "#0d4b70", "#0e9ea4"),
}


def _style_card(style, selected):
    background, heading, accent = STYLE_PREVIEWS[style]
    border = accent if selected else "#e5e2ef"
    title_color = heading
    lines = "".join(
        '<div style="height:5px;width:{}%;margin:7px 0;background:{};border-radius:4px;opacity:{}"></div>'.format(
            width, heading, "0.72" if i == 0 else "0.35"
        ) for i, width in enumerate((65, 88, 74))
    )
    st.markdown(
        '<div style="height:82px;background:{};border:2px solid {};border-radius:11px;padding:11px 13px;margin-bottom:10px;box-shadow:0 5px 15px #28204a12">'
        '<div style="height:8px;width:52%;background:{};border-radius:5px;margin-bottom:12px"></div>{}'
        '<div style="height:5px;width:24%;background:{};border-radius:5px;margin-top:10px"></div></div>'
        '<div style="font-weight:700;color:#f3f1fb;margin-bottom:4px">{}</div>'
        '<div style="font-size:13px;color:#aaa8bf;min-height:56px">{}</div>'.format(
            background, border, title_color, lines, accent, style, STYLE_DESCRIPTIONS[style]
        ),
        unsafe_allow_html=True,
    )


def _choose_style():
    if "presentation_style" not in st.session_state:
        st.session_state.presentation_style = STYLE_ACADEMIC
    st.markdown("#### Choose a design style")
    columns = st.columns(3)
    for column, style in zip(columns, PRESENTATION_STYLES):
        with column:
            _style_card(style, st.session_state.presentation_style == style)
            label = "Selected ✓" if st.session_state.presentation_style == style else "Select style"
            if st.button(label, key="presentation_style_" + style.lower().replace(" ", "_"),
                         type="primary" if st.session_state.presentation_style == style else "secondary",
                         use_container_width=True):
                st.session_state.presentation_style = style
                st.rerun()
    return st.session_state.presentation_style


def render(paper):
    st.title("Presentation Studio")
    st.caption("Generate a paper-grounded slide outline and download a real editable PowerPoint file.")
    style = _choose_style()
    count=st.select_slider("Number of slides",options=[5,8,10,12],value=8)
    if st.button("Generate presentation",type="primary"):
        try:
            with st.spinner("Researching the paper and drafting slides…"):
                outline=generate_outline(paper["id"],paper["name"],count)
                deck=create_pptx(outline,paper["name"],style=style)
            st.session_state.last_deck=deck
            st.session_state.last_deck_name=paper["name"]
            st.session_state.last_deck_style=style
            st.session_state.last_outline=outline
            st.success("Presentation ready.")
        except Exception as exc: st.error(str(exc))
    if st.session_state.get("last_deck") and st.session_state.get("last_deck_name")==paper["name"]:
        style_slug = st.session_state.get("last_deck_style", STYLE_ACADEMIC).lower().replace(" ", "-")
        st.download_button("Download PowerPoint (.pptx)",st.session_state.last_deck,file_name="ScholarFlow-{}-{}.pptx".format(paper["name"].rsplit(".",1)[0][:50], style_slug),mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",type="primary")
        for i,slide in enumerate(st.session_state.get("last_outline",{}).get("slides",[]),1):
            with st.expander("Slide {} · {}".format(i,slide["title"])):
                for bullet in slide.get("bullets",[]): st.markdown("- "+bullet)
