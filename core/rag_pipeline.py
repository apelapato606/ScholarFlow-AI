"""Persistent Chroma RAG isolated by document ID."""
import os
from pathlib import Path

CHROMA_DIR = os.getenv("SCHOLARFLOW_CHROMA_DIR", str(Path(__file__).resolve().parents[1] / "data" / ".chroma"))


def _embeddings():
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
        return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2", model_kwargs={"device": "cpu"}, encode_kwargs={"normalize_embeddings": True})
    except Exception as exc:
        raise RuntimeError("Could not load the HuggingFace sentence-transformer model. Check the install and network access, then retry.") from exc


def _collection_name(doc_id):
    return "paper_" + "".join(c for c in doc_id.lower() if c.isalnum())[:48]


def index_document(doc_id, chunks):
    try:
        from langchain_chroma import Chroma
    except ImportError:
        try:
            from langchain_community.vectorstores import Chroma
        except ImportError as exc:
            raise RuntimeError("Chroma integration missing. Install langchain-chroma.") from exc
    try:
        store = Chroma(collection_name=_collection_name(doc_id), embedding_function=_embeddings(), persist_directory=CHROMA_DIR)
        if store._collection.count() == 0:
            ids = ["{}-{}".format(doc_id, i) for i in range(len(chunks))]
            store.add_documents(chunks, ids=ids)
        return store._collection.count()
    except Exception as exc:
        if isinstance(exc, RuntimeError):
            raise
        raise RuntimeError("Could not index this paper in ChromaDB: {}".format(exc)) from exc


def retrieve(doc_id, query, k=5):
    if not query.strip():
        return []
    try:
        from langchain_chroma import Chroma
    except ImportError:
        from langchain_community.vectorstores import Chroma
    try:
        store = Chroma(collection_name=_collection_name(doc_id), embedding_function=_embeddings(), persist_directory=CHROMA_DIR)
        return store.similarity_search(query, k=k)
    except Exception as exc:
        raise RuntimeError("Could not retrieve paper context from ChromaDB: {}".format(exc)) from exc


def delete_index(doc_id):
    try:
        from langchain_chroma import Chroma
        store = Chroma(collection_name=_collection_name(doc_id), embedding_function=_embeddings(), persist_directory=CHROMA_DIR)
        store.delete_collection()
    except Exception:
        pass


def format_context(docs):
    return "\n\n".join("[p. {}] {}".format(d.metadata.get("page", "?"), d.page_content) for d in docs)
