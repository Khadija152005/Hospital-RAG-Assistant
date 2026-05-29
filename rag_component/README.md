# 🏥 Hospital RAG — Intelligent Technical Troubleshooting

Biomedical engineering assistant that answers questions about hospital device manuals using RAG (Retrieval-Augmented Generation).

## Devices Covered
- **BeneFusion VP3** Vet Infusion Pump (Mindray)
- **MAC 2000** ECG Analysis System (GE Healthcare)
- **Fresenius 4008S** Hemodialysis System

## Stack (All Free)
| Tool | Purpose |
|------|---------|
| LangChain | Framework |
| `all-MiniLM-L6-v2` (HuggingFace) | Embeddings — local, no API key |
| Neon + pgvector | Vector store — shared with team |
| Groq API (Llama 3.1 70B) | LLM — free tier |

---

## Setup (Do This Once)

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Get your free Groq API key
Go to https://console.groq.com → sign up → copy your key (takes 2 min)

### 3. Set up environment variables
```bash
cp .env.example .env
# Edit .env and fill in GROQ_API_KEY and NEON_CONNECTION_STRING
```

### 4. Enable pgvector on Neon
Open your Neon dashboard → SQL Editor → run:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### 5. Add your PDF manuals
```
data/manuals/BeneFusion_VP3.pdf
data/manuals/MAC_2000.pdf
data/manuals/Fresenius_4008S.pdf
```

### 6. Run ingestion (ONE TIME only)
```bash
python run_ingestion.py
```
This loads PDFs → chunks → embeds → stores in Neon. Takes ~5 minutes.

---

## Usage

### Interactive CLI
```bash
python main.py
```

### Run all tests
```bash
python test_queries.py           # full test (all 25+ queries)
python test_queries.py --quick   # quick test (1 per category)
python test_queries.py --search  # test retrieval only (no LLM)
```

### Use in code (routing agent integration)
```python
from main import handle_technical_query

answer = handle_technical_query(
    "What does [Occlusion] alarm mean?",
    asset_id="INF-001"   # optional
)
print(answer)
```

---

## Rebuild Vector Store
Only needed if you add new manuals or change chunking settings:
```bash
python run_ingestion.py --rebuild
```
