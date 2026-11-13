"""Create actual editable PowerPoint files."""
from io import BytesIO
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt
from services.pdf_service import record_activity

NAVY = RGBColor(25, 27, 56)
VIOLET = RGBColor(108, 75, 211)


def create_pptx(outline, paper_name):
    try:
        prs = Presentation()
        prs.core_properties.title = outline.get("title", paper_name)
        prs.core_properties.subject = "ScholarFlow AI research presentation"
        prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
        for index, item in enumerate(outline["slides"]):
            slide = prs.slides.add_slide(prs.slide_layouts[6])
            bg = slide.background.fill
            bg.solid()
            bg.fore_color.rgb = NAVY if index == 0 else RGBColor(250, 249, 255)
            title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.55), Inches(11.8), Inches(0.9))
            p = title_box.text_frame.paragraphs[0]
            p.text = item.get("title", "Research Overview")
            p.font.name, p.font.size, p.font.bold = "Aptos Display", Pt(30), True
            p.font.color.rgb = RGBColor(255, 255, 255) if index == 0 else NAVY
            accent = slide.shapes.add_shape(1, Inches(0.8), Inches(1.52), Inches(1.0), Inches(0.06))
            accent.fill.solid(); accent.fill.fore_color.rgb = VIOLET; accent.line.fill.background()
            box = slide.shapes.add_textbox(Inches(1.0), Inches(2.0), Inches(11.2), Inches(4.8))
            tf = box.text_frame; tf.word_wrap = True
            for bullet_index, bullet in enumerate(item.get("bullets", [])):
                para = tf.paragraphs[0] if bullet_index == 0 else tf.add_paragraph()
                para.text = bullet
                para.level = 0
                para.font.name, para.font.size = "Aptos", Pt(22)
                para.font.color.rgb = RGBColor(255, 255, 255) if index == 0 else RGBColor(56, 53, 77)
                para.space_after = Pt(18)
            footer = slide.shapes.add_textbox(Inches(0.8), Inches(7.05), Inches(11.8), Inches(0.2))
            fp = footer.text_frame.paragraphs[0]; fp.text = "SCHOLARFLOW AI  •  {}  •  {}".format(paper_name[:55], index + 1)
            fp.font.size = Pt(9); fp.font.color.rgb = RGBColor(192, 187, 218) if index == 0 else RGBColor(132, 126, 153)
        out = BytesIO(); prs.save(out); out.seek(0)
        record_activity("Presentation generated", paper_name)
        return out.getvalue()
    except Exception as exc:
        raise RuntimeError("PowerPoint generation failed: {}".format(exc)) from exc
