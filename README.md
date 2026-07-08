# 🏥 Hospital AI Central

Welcome to **Hospital AI Central** — a comprehensive hospital infrastructure management platform designed to empower clinical and biomedical engineering teams with instant, AI-driven technical support. 

This repository contains both the overarching Web Dashboard and the core RAG (Retrieval-Augmented Generation) Assistant that allows engineers to query complex medical device manuals in natural language.

---

## 🌟 Key Features

1. **Intelligent RAG Assistant:**
   - Chat with medical device manuals (e.g., BeneFusion VP3, MAC 2000, Fresenius 4008S).
   - Generates grounded, step-by-step troubleshooting and calibration instructions.
   - Refuses to hallucinate: strictly relies on the provided PDFs.

2. **Multilingual Support (Native Arabic & More):**
   - Ask questions in Arabic or any other language! 
   - A lightweight LLM translation node intercepts the query, translates it to English, searches the English vector database, and dynamically translates the final answer back to your native language.

3. **Advanced PDF Ingestion & OCR:**
   - Capable of reading complex, badly-formatted PDFs.
   - Implements **PyMuPDF** for character-level coordinate extraction (fixes concatenated word issues).
   - Implements **Tesseract OCR (pdf2image)** fallback for image-based PDFs (e.g., scanned troubleshooting tables).

4. **Beautiful Modern UI:**
   - **Landing Page:** Highlights current and future platform capabilities (Analytics, Inventory).
   - **RAG Dashboard:** Interactive chat interface with citations, source tracking, and smooth mobile-responsive layouts.
   - **Dark Mode:** Fully supported with `localStorage` persistence.
   - **Settings Panel:** Dynamically update your API keys directly from the UI without restarting the server.

---

## 🛠️ Architecture & Tech Stack

| Component | Technology | Description |
|-----------|------------|-------------|
| **Backend API** | FastAPI | Hosts the web server and serves the REST endpoints (`/api/chat`, `/api/settings`). |
| **Frontend** | HTML/CSS/JS | Vanilla web stack with a custom Glassmorphic design and FontAwesome icons. |
| **LLM Framework**| LangChain | Manages the RAG pipeline, prompting, and output parsing. |
| **Embeddings** | `all-MiniLM-L6-v2` | Fast, local HuggingFace embedding model (no API key required). |
| **Database** | Neon + `pgvector` | PostgreSQL cloud database with native vector similarity search. |
| **Inference** | Groq API (Llama 3) | Blazing fast LLM inference (Free Tier) for translation and generation. |

### Directory Structure
```text
Hospital-RAG-Assistant/
├── app.py                      # Main FastAPI server entry point
├── requirements.txt            # Python dependencies
├── website/                    # Frontend UI assets
│   ├── index.html              # Landing Page
│   ├── rag.html                # RAG Assistant Dashboard
│   ├── styles.css              # Custom styling (Light & Dark modes)
│   └── script.js               # Frontend logic and API calls
└── rag_component/              # Core RAG backend logic
    ├── .env                    # Environment variables (API keys, DB connection)
    ├── config.py               # Central configuration loader
    ├── ingestion/              # Scripts to chunk and embed PDFs (pdfplumber, PyMuPDF, OCR)
    └── retrieval/              # Semantic search and LangChain generation logic
```

---

## 🚀 Setup & Installation (One-Time)

### 1. Install Dependencies
Make sure you have Python 3 installed, then run:
```bash
pip install -r requirements.txt
```
*(Note: If you plan to rebuild the vector database using OCR, you will also need to install [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) and [Poppler](http://blog.alivate.com.au/poppler-windows/) on your system.)*

### 2. Configure Environment Variables
Inside the `rag_component/` folder, create or edit the `.env` file:
```ini
GROQ_API_KEY=gsk_your_free_groq_api_key_here
NEON_CONNECTION_STRING=postgresql://username:password@your-neon-host.aws.neon.tech/hospital_rag
```
*(You can also update the Groq API key directly via the Settings gear icon in the Web UI!)*

### 3. Run the Server
Launch the FastAPI application from the **root directory**:
```bash
python app.py
```
### 4. Open the Dashboard
Open your browser and navigate to:
👉 **[http://localhost:8000](http://localhost:8000)**

---

## 📚 Database Ingestion (For Admins)
If you need to add new medical manuals to the database:
1. Place the PDF in `rag_component/data/manuals/`.
2. Update the `MANUALS` dictionary in `rag_component/config.py`.
3. Run the ingestion script:
```bash
cd rag_component
python run_ingestion.py
```
This script will extract the text (using OCR if necessary), chunk it, embed it using HuggingFace, and push the vectors to your Postgres database. Takes ~5 minutes depending on the PDF size.
