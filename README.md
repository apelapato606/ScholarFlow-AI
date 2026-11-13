# ScholarFlow AI

ScholarFlow AI is a Streamlit research workspace that ingests academic PDFs, retrieves paper-specific passages, and routes requests to four focused AI agents: Summarizer, Concept Extractor, Slide Generator, and Viva Practice. It uses Groq through LangChain LCEL, HuggingFace sentence-transformer embeddings, persistent ChromaDB, PyMuPDF, python-pptx, and Pandas.

## Features

- Upload, validate, select, download, and delete research PDFs.
- Extract page-aware text, split into overlapping chunks, embed with `sentence-transformers/all-MiniLM-L6-v2`, and index in a separate persistent Chroma collection for each paper.
- Retrieve relevant passages from the selected paper only; answers include page references where available.
- Structured paper summaries and concept/methodology exploration.
- Intent detection routes requests to specialized summarization, concept, presentation, viva question, viva evaluation, or paper Q&A workflows.
- Generate 5, 8, 10, or 12 slide outlines and download genuine editable PPTX files.
- Practice easy, intermediate, and difficult viva questions; receive correctness, relevance, and completeness scores plus feedback.
- Download viva session reports as Excel workbooks with summary and per-question details.
- SQLite-backed library/activity counts, session-based conversation history, selected paper, difficulty, and viva state.

## Technology and architecture

`app.py` provides the Streamlit navigation. `core/document_processor.py` extracts and chunks PDF text. `services/pdf_service.py` manages local paper metadata and indexing lifecycle. `core/rag_pipeline.py` creates/reuses isolated Chroma collections and performs similarity search with HuggingFace embeddings. `core/prompts.py` contains explicit system/user prompts. Each module in `agents/` owns its task and calls an LCEL chain (`ChatPromptTemplate | ChatGroq`); `core/router.py` classifies user intent and the UI dispatches to the corresponding agent. Presentation and report output are generated with python-pptx and Pandas.

The router uses transparent keyword rules for common requests and can use the configured LLM as a fallback for ambiguous text. Every substantive answer path retrieves selected-paper context first. The model is instructed to report insufficient evidence instead of inventing paper facts. Private chain-of-thought is not requested or shown.

## Requirements

- Python 3.10 or newer for local setup. For Community Cloud, select Python 3.12 in Advanced settings (the current Cloud default).
- A Groq API key for language-model features.
- Internet access on first run to download Python packages and the HuggingFace embedding model.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## API key setup

Option 1, environment variable:

```bash
export GROQ_API_KEY="gsk_your_key_here"   # Windows PowerShell: $env:GROQ_API_KEY="gsk_your_key_here"
```

Option 2, Streamlit secrets:

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Edit `.streamlit/secrets.toml` and put your key in `GROQ_API_KEY`. The file is ignored by Git. The shared LangChain Groq client defaults to production model `openai/gpt-oss-120b`; an optional `GROQ_MODEL` setting can override it for all agents together. The Settings page includes **Test Groq connection**, which sends a minimal live generation request and reports authentication, model, rate-limit, and network errors clearly.

## Run

```bash
streamlit run app.py
```

Open the local URL printed by Streamlit, go to **Research Library**, upload a text-based PDF, and select it in the sidebar. First embedding use downloads the sentence-transformer model and may take a few minutes. Set `SCHOLARFLOW_CHROMA_DIR` to move the persistent vector store.

## Deploy to Streamlit Community Cloud

1. Push the reviewed project to GitHub only after confirming that `.gitignore` excludes local secrets and data. This project folder currently has no Git repository initialized.
2. In Streamlit Community Cloud, create an app from the repository and set the entrypoint to `app.py` at the repository root.
3. In Advanced settings, select Python 3.12.
4. In the app's **Secrets** field, enter the secret in TOML format:

```toml
GROQ_API_KEY = "gsk_your_key_here"
GROQ_MODEL = "openai/gpt-oss-120b"
```

`GROQ_MODEL` is optional; the app uses `openai/gpt-oss-120b` by default. Never commit the real key or copy the local `.streamlit/secrets.toml` into the repository. Use the Settings page's **Test Groq connection** button after deployment.

### Important deployment limitations

- The app has no sign-in or per-user document isolation. In one public Cloud instance, the uploaded-paper library, downloads, local SQLite records, and Chroma index are shared across visitors. Visitors may see or delete papers uploaded by other visitors. Do not use this deployment for private or confidential papers until account-level isolation and access controls are implemented.
- Community Cloud's local filesystem is ephemeral. Uploaded papers, SQLite metadata, and the Chroma index can disappear when the app restarts or is redeployed. The current implementation does not use durable external storage.
- The first paper upload downloads the sentence-transformer model and initializes CPU embeddings. This adds build/runtime download time and memory use; a resource-limited instance may run slowly or fail while loading the embedding model.

## Workflow

1. Validate PDF signature, extract readable text by page with PyMuPDF, and split into overlapping chunks.
2. Generate local HuggingFace sentence embeddings and store chunks in a document-specific persistent Chroma collection.
3. Detect request intent and route to the appropriate specialized agent.
4. Similarity-search only the selected paper's collection and pass retrieved page-labelled context to its LCEL prompt/model chain.
5. Render the answer, build real PPTX files with python-pptx, and produce downloadable XLSX viva reports with Pandas.

## Data and privacy

In local development, uploaded PDFs, Chroma data, and SQLite metadata are stored under `data/` by default. The local data directory, PDFs, generated exports, virtual environments, and secret files are excluded by `.gitignore`. On Community Cloud, this storage is shared by the app instance and is not durable; see the deployment limitations above. Paper excerpts used to answer requests are sent to Groq for model inference. Review your institution's and provider's data policies before uploading confidential material. Remove local user data by deleting the corresponding paper in the Research Library and, if needed, the local `data/` directory.

## Screenshots

Add genuine screenshots after running the app, with example files under `docs/screenshots/`. Suggested captures: overview, research library with a sample paper, concept exploration with citations, generated slide outline, viva evaluation and report. Do not include API keys or private papers in screenshots.

## Tests

Run the included focused tests with:

```bash
python -m unittest discover -s tests -v
```

The tests cover PDF validation/text extraction/chunk metadata, intent routing, Groq model configuration/error mapping, and PowerPoint/report file signatures. End-to-end model and embedding calls require network access and configured service dependencies. The Settings page can perform a live Groq connection check.

## Limitations

- Scanned PDFs without embedded text are detected and rejected; OCR is not implemented.
- Embeddings run locally on CPU by default; first run requires model download and can be slow on modest hardware.
- Groq quotas, model availability, network access, and service-side response formats can affect AI requests.
- Viva and conversation state are session-based. On a local machine, document metadata and indexes persist across app restarts; on Community Cloud, its local filesystem is temporary, so these files may be lost.
