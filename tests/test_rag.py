import unittest
from io import BytesIO
from pptx import Presentation
from services.presentation_service import create_pptx
from services.report_service import build_report

class ExportTests(unittest.TestCase):
    def test_pptx_is_openable(self):
        data=create_pptx({"title":"Research","slides":[{"title":"Finding","bullets":["A real result"]}]},"paper.pdf")
        prs=Presentation(BytesIO(data))
        self.assertEqual(len(prs.slides),1)
        self.assertTrue(any("Finding" in shape.text for shape in prs.slides[0].shapes if shape.has_text_frame))
    def test_report_is_xlsx(self):
        data=build_report("paper.pdf",[{"question":"Why?","evaluation":{"score":8,"correctness":8,"relevance":8,"completeness":8,"feedback":"Good","strengths":["Clear"],"missing_concepts":[]}}])
        self.assertTrue(data.startswith(b"PK"))
