# 🏥 Hospital AI Central

Welcome to **Hospital AI Central** — a comprehensive AI-powered hospital infrastructure management platform designed to support clinical engineers, biomedical engineers, and healthcare organizations through intelligent assistance, analytics, and future-ready hospital management services.

The platform combines multiple AI modules into one centralized system, including **Retrieval-Augmented Generation (RAG)** for medical manuals and **Conversational Analytics** for natural language database querying.

---

# 🌟 Key Features

## 🤖 Intelligent RAG Assistant
- Chat with medical device manuals using natural language.
- Supports devices such as:
  - BeneFusion VP3
  - MAC 2000
  - Fresenius 4008S
- Generates grounded troubleshooting and calibration instructions.
- Answers are generated only from uploaded manuals to minimize hallucinations.

---

## 📊 Conversational Analytics
- Query hospital databases using natural language.
- Converts English questions into SQL automatically.
- Executes only safe read-only SQL queries.
- Returns human-readable answers together with query results.
- SQL validation prevents unsafe statements.
- Powered by LangChain + Google Gemini + PostgreSQL.

Example Questions:

- Which medical device has the highest downtime?
- Count assets by department.
- Top 5 assets by maintenance cost.
- Which spare parts are below the reorder level?

---

## 🌍 Multilingual Support
- Supports Arabic and English.
- User questions are translated automatically when required.
- Final answers are returned in the user's language.

---

## 📄 Advanced PDF Processing
- PyMuPDF text extraction
- OCR support for scanned manuals
- pdfplumber parsing
- Character-level extraction
- Automatic chunking & embedding

---

## 🎨 Modern Web Dashboard
- Landing Page
- RAG Assistant Dashboard
- Dark Mode
- Responsive Design
- API Settings Panel
- Source citations
- Mobile Friendly UI

---

# 🛠 Technology Stack

| Component | Technology |
|------------|------------|
| Backend | FastAPI |
| Frontend | HTML / CSS / JavaScript |
| RAG Framework | LangChain |
| Conversational Analytics | LangChain SQL + Google Gemini |
| Embeddings | all-MiniLM-L6-v2 |
| Database | PostgreSQL + pgvector |
| ORM | SQLAlchemy |
| LLM Providers | Groq + Google Gemini |
| Environment | Python |

---

# 📂 Project Structure

```text
Hospital-RAG-Assistant/
│
├── app.py
├── requirements.txt
├── README.md
│
├── website/
│   ├── index.html
│   ├── rag.html
│   ├── styles.css
│   └── script.js
│
├── rag_component/
│   ├── config.py
│   ├── ingestion/
│   ├── retrieval/
│   └── ...
│
├── conversational_analytics/
│   ├── app/
│   ├── docs/
│   ├── tests/
│   ├── .env.example
│   └── README.md
│
└── agentic_module/
```

---

# 🚀 Installation

Clone the repository

```bash
git clone <repository-url>
cd Hospital-RAG-Assistant
```

Install dependencies

```bash
pip install -r requirements.txt
```

---

# ⚙ Configuration

Create a `.env` file and configure:

```ini
GROQ_API_KEY=YOUR_GROQ_KEY

GOOGLE_API_KEY=YOUR_GEMINI_KEY

NEON_CONNECTION_STRING=YOUR_DATABASE

PGHOST=
PGDATABASE=
PGUSER=
PGPASSWORD=
```

---

# ▶ Running the Application

```bash
python app.py
```

or

```bash
uvicorn app:app --reload
```

Open

```
http://localhost:8000
```

Swagger Documentation

```
http://localhost:8000/docs
```

---

# 📡 API Endpoints

## RAG Assistant

### POST

```
/api/chat
```

Example

```json
{
    "question":"How do I calibrate MAC 2000?"
}
```

---

## Settings

### POST

```
/api/settings
```

Example

```json
{
    "groq_api_key":"YOUR_KEY"
}
```

---

## Conversational Analytics

### Health Check

```
GET /analytics/health
```

---

### Ask Analytics

```
POST /analytics/ask
```

Example

```json
{
    "question":"Which medical device has the highest downtime?"
}
```

---

# 📚 Adding New Medical Manuals

1. Copy PDF into

```
rag_component/data/manuals
```

2. Update

```
config.py
```

3. Run

```bash
python run_ingestion.py
```

---

# 🔒 Security

- Read-only SQL execution
- SQL validation before execution
- Environment variables for API keys
- No destructive SQL statements are allowed

---

# 🚀 Future Work

- Inventory Management
- Predictive Maintenance
- Asset Tracking
- Preventive Maintenance Scheduling
- Multi-Agent AI
- Dashboard Analytics
- Authentication & Authorization

---

# 👨‍💻 Team

Developed as a Graduation / AI Project for intelligent hospital infrastructure management using modern Generative AI technologies.

---

# 📄 License

This project is intended for educational and research purposes.
