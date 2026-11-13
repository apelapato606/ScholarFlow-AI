"""Document persistence, PDF processing, metadata, and library queries."""
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from core.document_processor import extract_pdf, make_chunks, document_id
from core.rag_pipeline import index_document, delete_index

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "scholarflow.db"
PAPERS_DIR = DATA_DIR / "papers"


def _connect():
    DATA_DIR.mkdir(exist_ok=True)
    con = sqlite3.connect(str(DB_PATH))
    con.row_factory = sqlite3.Row
    con.execute("CREATE TABLE IF NOT EXISTS papers (id TEXT PRIMARY KEY, name TEXT NOT NULL, uploaded_at TEXT NOT NULL, status TEXT NOT NULL, page_count INTEGER DEFAULT 0, chunk_count INTEGER DEFAULT 0, error TEXT DEFAULT '')")
    con.execute("CREATE TABLE IF NOT EXISTS activity (id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL, detail TEXT NOT NULL, created_at TEXT NOT NULL)")
    con.commit()
    return con


def record_activity(kind, detail):
    with _connect() as con:
        con.execute("INSERT INTO activity(kind,detail,created_at) VALUES(?,?,?)", (kind, detail, datetime.now().isoformat(timespec="seconds")))


def ingest_pdf(name, data):
    if not name.lower().endswith(".pdf") or not data.startswith(b"%PDF"):
        raise ValueError("Upload a valid .pdf file.")
    doc_id = document_id(data)
    con = _connect()
    existing = con.execute("SELECT * FROM papers WHERE id=?", (doc_id,)).fetchone()
    if existing and existing["status"] == "Ready":
        con.close()
        return dict(existing)
    con.execute("INSERT OR REPLACE INTO papers(id,name,uploaded_at,status,error) VALUES(?,?,?,?,?)", (doc_id, name, datetime.now().isoformat(timespec="seconds"), "Processing", ""))
    con.commit()
    con.close()
    try:
        pages = extract_pdf(data)
        chunks = make_chunks(pages)
        count = index_document(doc_id, chunks)
        with _connect() as con:
            con.execute("UPDATE papers SET status='Ready',page_count=?,chunk_count=?,error='' WHERE id=?", (len(pages), count, doc_id))
        PAPERS_DIR.mkdir(parents=True, exist_ok=True)
        (PAPERS_DIR / (doc_id + ".pdf")).write_bytes(data)
        record_activity("Paper uploaded", name)
        return get_paper(doc_id)
    except Exception as exc:
        with _connect() as con:
            con.execute("UPDATE papers SET status='Failed',error=? WHERE id=?", (str(exc), doc_id))
        raise


def list_papers():
    with _connect() as con:
        return [dict(row) for row in con.execute("SELECT * FROM papers ORDER BY uploaded_at DESC")]


def get_paper(doc_id):
    with _connect() as con:
        row = con.execute("SELECT * FROM papers WHERE id=?", (doc_id,)).fetchone()
        return dict(row) if row else None


def delete_paper(doc_id):
    paper = get_paper(doc_id)
    if not paper:
        return
    delete_index(doc_id)
    try:
        (PAPERS_DIR / (doc_id + ".pdf")).unlink()
    except FileNotFoundError:
        pass
    with _connect() as con:
        con.execute("DELETE FROM papers WHERE id=?", (doc_id,))
    record_activity("Paper deleted", paper["name"])


def stats():
    with _connect() as con:
        docs = con.execute("SELECT COUNT(*) FROM papers WHERE status='Ready'").fetchone()[0]
        decks = con.execute("SELECT COUNT(*) FROM activity WHERE kind='Presentation generated'").fetchone()[0]
        vivas = con.execute("SELECT COUNT(*) FROM activity WHERE kind='Viva completed'").fetchone()[0]
        recent = [dict(row) for row in con.execute("SELECT * FROM activity ORDER BY id DESC LIMIT 8")]
    return {"documents": docs, "presentations": decks, "vivas": vivas, "recent": recent}
