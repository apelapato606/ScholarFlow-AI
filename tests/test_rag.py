import unittest
from io import BytesIO

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE

from services.presentation_service import (
    PRESENTATION_STYLES,
    STYLE_ACADEMIC,
    STYLE_INFOGRAPHIC,
    create_pptx,
)
from services.report_service import build_report


class ExportTests(unittest.TestCase):
    def test_pptx_is_openable(self):
        data = create_pptx({"title": "Research", "slides": [{"title": "Finding", "bullets": ["A real result"]}]}, "paper.pdf")
        prs = Presentation(BytesIO(data))
        self.assertEqual(len(prs.slides), 1)
        self.assertTrue(any("Finding" in shape.text for shape in prs.slides[0].shapes if shape.has_text_frame))

    def test_all_styles_and_slide_counts_generate_openable_decks(self):
        for style in PRESENTATION_STYLES:
            for count in (5, 8, 10, 12):
                outline = {
                    "title": "Paper-specific research title",
                    "slides": [
                        {"title": "Methodology and pipeline" if index == 1 else "Research finding {}".format(index + 1),
                         "bullets": ["Paper-derived step or finding {}.{}".format(index + 1, item + 1) for item in range(3)]}
                        for index in range(count)
                    ],
                }
                prs = Presentation(BytesIO(create_pptx(outline, "research-paper.pdf", style=style)))
                self.assertEqual(len(prs.slides), count, (style, count))
                self.assertTrue(any("Research finding" in shape.text or "Methodology" in shape.text
                                    for shape in prs.slides[1].shapes if shape.has_text_frame))
                self.assertTrue(prs.core_properties.subject.endswith(style))

    def test_infographic_method_slide_contains_editable_diagram(self):
        outline = {"title": "Research", "slides": [
            {"title": "Overview", "bullets": ["Summary"]},
            {"title": "Methodology", "bullets": ["Collect data", "Process data", "Evaluate model"]},
        ]}
        prs = Presentation(BytesIO(create_pptx(outline, "paper.pdf", STYLE_INFOGRAPHIC)))
        self.assertTrue(any(shape.shape_type == 1 and shape.auto_shape_type == MSO_SHAPE.CHEVRON
                            for shape in prs.slides[1].shapes))

    def test_omitted_style_keeps_academic_default(self):
        outline = {"title": "Research", "slides": [{"title": "Finding", "bullets": ["Evidence"]}]}
        default = Presentation(BytesIO(create_pptx(outline, "paper.pdf")))
        explicit = Presentation(BytesIO(create_pptx(outline, "paper.pdf", STYLE_ACADEMIC)))
        self.assertEqual(default.slides[0].background.fill.fore_color.rgb,
                         explicit.slides[0].background.fill.fore_color.rgb)

    def test_report_is_xlsx(self):
        data = build_report("paper.pdf", [{"question": "Why?", "evaluation": {"score": 8, "correctness": 8,
            "relevance": 8, "completeness": 8, "feedback": "Good", "strengths": ["Clear"], "missing_concepts": []}}])
        self.assertTrue(data.startswith(b"PK"))
