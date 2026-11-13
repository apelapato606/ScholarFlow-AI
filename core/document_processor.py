"""PDF text extraction and page-aware chunking."""
import hashlib
import re
import fitz
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


def extract_pdf(data):
    try:
        pdf = fitz.open(stream=data, filetype="pdf")
    except Exception as exc:
        raise ValueError("This file could not be opened as a PDF. Please upload a valid, unencrypted research paper.") from exc
    pages = []
    try:
        if pdf.is_encrypted:
            raise ValueError("Encrypted PDFs are not supported. Please upload an unlocked copy.")
        for index, page in enumerate(pdf):
            text = re.sub(r"\s+", " ", page.get_text("text")).strip()
            if text:
                pages.append((index + 1, text))
    finally:
        pdf.close()
    if not pages or sum(len(text) for _, text in pages) < 100:
        raise ValueError("No readable research text was found. This PDF may be scanned; OCR is not currently supported.")
    return pages


def make_chunks(pages, chunk_size=1100, overlap=180):
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=overlap, separators=["\n\n", ". ", " ", ""])
    docs = []
    for page_number, text in pages:
        for part, chunk in enumerate(splitter.split_text(text)):
            docs.append(Document(page_content=chunk, metadata={"page": page_number, "part": part}))
    return docs


def document_id(data):
    return hashlib.sha256(data).hexdigest()[:24]
