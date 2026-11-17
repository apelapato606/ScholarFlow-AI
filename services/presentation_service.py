"""Create editable, themed PowerPoint files from AI-generated outlines."""
from io import BytesIO

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt

from services.pdf_service import record_activity


STYLE_ACADEMIC = "Academic Professional"
STYLE_MODERN = "Modern Creative"
STYLE_INFOGRAPHIC = "Visual Infographic"
PRESENTATION_STYLES = (STYLE_ACADEMIC, STYLE_MODERN, STYLE_INFOGRAPHIC)

# Colors are plain RGB so every element remains editable in PowerPoint.
THEMES = {
    STYLE_ACADEMIC: {
        "background": (255, 255, 255), "cover": (255, 255, 255), "ink": (31, 41, 55),
        "heading": (25, 49, 92), "accent": (91, 103, 190), "secondary": (230, 235, 246),
        "muted": (103, 116, 138), "font": "Aptos", "title_font": "Aptos Display",
    },
    STYLE_MODERN: {
        "background": (23, 20, 52), "cover": (20, 17, 48), "ink": (241, 239, 255),
        "heading": (255, 255, 255), "accent": (157, 119, 255), "secondary": (48, 40, 86),
        "muted": (190, 181, 222), "font": "Aptos", "title_font": "Aptos Display",
    },
    STYLE_INFOGRAPHIC: {
        "background": (246, 251, 252), "cover": (13, 75, 112), "ink": (30, 57, 70),
        "heading": (13, 75, 112), "accent": (14, 158, 164), "secondary": (220, 242, 242),
        "muted": (89, 119, 130), "font": "Aptos", "title_font": "Aptos Display",
    },
}


def _rgb(value):
    return RGBColor(*value)


def _add_text(slide, text, x, y, w, h, theme, size=20, bold=False, color=None,
              font=None, align=PP_ALIGN.LEFT):
    shape = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    frame = shape.text_frame
    frame.clear()
    frame.word_wrap = True
    frame.margin_left = Inches(0.02)
    frame.margin_right = Inches(0.02)
    frame.margin_top = Inches(0.01)
    frame.margin_bottom = Inches(0.01)
    para = frame.paragraphs[0]
    para.text = str(text)
    para.alignment = align
    para.font.name = font or theme["font"]
    para.font.size = Pt(size)
    para.font.bold = bold
    para.font.color.rgb = _rgb(color or theme["ink"])
    return shape


def _add_rect(slide, x, y, w, h, color, radius=False):
    shape_kind = MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE
    shape = slide.shapes.add_shape(shape_kind, Inches(x), Inches(y), Inches(w), Inches(h))
    shape.fill.solid()
    shape.fill.fore_color.rgb = _rgb(color)
    shape.line.fill.background()
    if radius:
        shape.adjustment = 0.12
    return shape


def _set_background(slide, color):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = _rgb(color)


def _add_footer(slide, paper_name, index, total, theme):
    _add_text(slide, "SCHOLARFLOW AI  ·  {}  ·  {:02d} / {:02d}".format(paper_name[:48], index + 1, total),
              0.7, 7.12, 11.9, 0.2, theme, size=9, color=theme["muted"])


def _add_academic_title(slide, title, theme, cover=False):
    _add_text(slide, title, 0.85, 0.72 if cover else 0.48, 11.7, 1.25 if cover else 0.72,
              theme, size=31 if cover else 27, bold=True, color=theme["heading"], font=theme["title_font"])
    _add_rect(slide, 0.88, 2.05 if cover else 1.38, 0.9, 0.07, theme["accent"])


def _add_modern_title(slide, title, theme, cover=False):
    # Solid editable shapes create the impression of layered violet gradients.
    _add_rect(slide, 10.3, 0, 3.04, 7.5, theme["secondary"])
    _add_rect(slide, 11.45, 0, 1.89, 7.5, theme["accent"])
    _add_text(slide, title, 0.9, 0.9 if cover else 0.55, 10.2, 1.35 if cover else 0.9,
              theme, size=34 if cover else 28, bold=True, color=theme["heading"], font=theme["title_font"])
    _add_rect(slide, 0.92, 2.3 if cover else 1.55, 1.15, 0.07, theme["accent"])


def _add_infographic_title(slide, title, theme, cover=False):
    _add_rect(slide, 0, 0, 0.22, 7.5, theme["accent"])
    _add_text(slide, title, 0.78, 0.62, 11.7, 1.1, theme, size=31 if cover else 27,
              bold=True, color=RGBColor(255, 255, 255) if cover else theme["heading"], font=theme["title_font"])
    _add_rect(slide, 0.8, 1.85 if cover else 1.48, 1.05, 0.07, theme["accent"])


def _is_process_slide(title):
    keywords = ("method", "approach", "pipeline", "framework", "architecture", "process", "workflow", "algorithm")
    return any(word in title.lower() for word in keywords)


def _add_bullet_list(slide, bullets, theme, modern=False, cover=False):
    # Keep a readable, editable text layout and avoid clipping long outlines.
    usable = bullets
    if not usable:
        usable = ["Key details are described in the source paper."]
    y = 2.45 if cover else 1.85
    row_h = (4.15 if cover else 4.75) / len(usable)
    font_size = 19 if len(usable) <= 4 else (16 if len(usable) <= 6 else (13 if len(usable) <= 10 else 10))
    for idx, text in enumerate(usable):
        if modern:
            _add_rect(slide, 0.86, y + 0.08, 0.12, 0.48, theme["accent"])
            tx, tw = 1.18, 9.75
        else:
            _add_rect(slide, 0.9, y + 0.13, 0.14, 0.14, theme["accent"], radius=True)
            tx, tw = 1.25, 10.8
        _add_text(slide, text, tx, y, tw, row_h, theme, size=font_size)
        y += row_h


def _add_process_visual(slide, bullets, theme):
    """Render a simple editable flow diagram from generated bullets."""
    steps = bullets[:4]
    if len(steps) < 2:
        return False
    _add_text(slide, "PROCESS OVERVIEW", 0.85, 1.72, 4.2, 0.26, theme, size=10, bold=True, color=theme["muted"])
    count = len(steps)
    start_x, gap, box_w = 0.85, 0.22, (11.65 - 0.22 * (count - 1)) / count
    for i, text in enumerate(steps):
        x = start_x + i * (box_w + gap)
        _add_rect(slide, x, 2.15, box_w, 2.55, theme["secondary"], radius=True)
        circle = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x + 0.12), Inches(2.3), Inches(0.43), Inches(0.43))
        circle.fill.solid(); circle.fill.fore_color.rgb = _rgb(theme["accent"]); circle.line.fill.background()
        tf = circle.text_frame; tf.clear(); tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]; p.text = str(i + 1); p.alignment = PP_ALIGN.CENTER
        p.font.name = theme["font"]; p.font.bold = True; p.font.size = Pt(13); p.font.color.rgb = RGBColor(255, 255, 255)
        _add_text(slide, text, x + 0.13, 2.9, box_w - 0.26, 1.45, theme, size=14, bold=True)
        if i < count - 1:
            connector = slide.shapes.add_shape(MSO_SHAPE.CHEVRON, Inches(x + box_w + 0.04), Inches(3.12), Inches(0.17), Inches(0.38))
            connector.fill.solid(); connector.fill.fore_color.rgb = _rgb(theme["accent"]); connector.line.fill.background()
    remaining = bullets[4:]
    if remaining:
        details = "\n".join("• {}".format(text) for text in remaining)
        _add_text(slide, details, 0.9, 4.95, 11.4, 1.75, theme, size=11 if len(remaining) <= 5 else 9)
    return True


def _add_infographic_bullets(slide, title, bullets, theme):
    if _is_process_slide(title) and _add_process_visual(slide, bullets, theme):
        return
    # Information cards provide a visual hierarchy without fabricating chart values.
    items = bullets or ["Key details are described in the source paper."]
    cols = 3 if len(items) > 4 else (2 if len(items) > 2 else 1)
    rows = (len(items) + cols - 1) // cols
    card_w = 3.63 if cols == 3 else (5.55 if cols == 2 else 11.2)
    card_h = min(1.95, 4.35 / rows)
    for idx, text in enumerate(items):
        col, row = idx % cols, idx // cols
        x, y = 0.84 + col * (3.88 if cols == 3 else 5.83), 1.9 + row * (card_h + 0.2)
        _add_rect(slide, x, y, card_w, card_h, theme["secondary"], radius=True)
        _add_rect(slide, x, y, 0.12, card_h, theme["accent"])
        _add_text(slide, "{:02d}".format(idx + 1), x + 0.28, y + 0.18, 0.65, 0.42, theme,
                  size=17, bold=True, color=theme["accent"])
        _add_text(slide, text, x + 0.82, y + 0.17, card_w - 1.02, card_h - 0.3, theme,
                  size=15 if len(items) <= 4 else (12 if len(items) <= 8 else 10))


def create_pptx(outline, paper_name, style=STYLE_ACADEMIC):
    """Create a PPTX; style is optional to preserve existing callers."""
    try:
        style = style if style in THEMES else STYLE_ACADEMIC
        theme = THEMES[style]
        prs = Presentation()
        prs.core_properties.title = outline.get("title", paper_name)
        prs.core_properties.subject = "ScholarFlow AI research presentation · {}".format(style)
        prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
        slides = outline["slides"]
        for index, item in enumerate(slides):
            slide = prs.slides.add_slide(prs.slide_layouts[6])
            cover = index == 0
            _set_background(slide, theme["cover"] if style == STYLE_MODERN or cover else theme["background"])

            if style == STYLE_ACADEMIC:
                _add_academic_title(slide, item.get("title", "Research Overview"), theme, cover)
                _add_bullet_list(slide, item.get("bullets", []), theme, cover=cover)
            elif style == STYLE_MODERN:
                _add_modern_title(slide, item.get("title", "Research Overview"), theme, cover)
                _add_bullet_list(slide, item.get("bullets", []), theme, modern=True, cover=cover)
            else:
                _add_infographic_title(slide, item.get("title", "Research Overview"), theme, cover)
                _add_infographic_bullets(slide, item.get("title", ""), item.get("bullets", []), theme)

            if cover:
                # Paper title is generated from the uploaded paper's outline, not template filler.
                _add_text(slide, paper_name, 0.88, 6.68, 10.8, 0.24, theme, size=10, color=theme["muted"])
            _add_footer(slide, paper_name, index, len(slides), theme)

        out = BytesIO()
        prs.save(out)
        out.seek(0)
        record_activity("Presentation generated", paper_name)
        return out.getvalue()
    except Exception as exc:
        raise RuntimeError("PowerPoint generation failed: {}".format(exc)) from exc
