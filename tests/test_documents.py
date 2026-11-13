import unittest
import fitz
from core.document_processor import extract_pdf, make_chunks, document_id

class DocumentTests(unittest.TestCase):
    def test_extract_and_chunk(self):
        doc=fitz.open(); page=doc.new_page(); page.insert_text((72,72),"Research text "*40)
        data=doc.tobytes(); doc.close()
        pages=extract_pdf(data); chunks=make_chunks(pages)
        self.assertEqual(pages[0][0],1)
        self.assertTrue(chunks)
        self.assertEqual(chunks[0].metadata["page"],1)
        self.assertEqual(document_id(data),document_id(data))
    def test_invalid_pdf(self):
        with self.assertRaises(ValueError): extract_pdf(b"not a pdf")
