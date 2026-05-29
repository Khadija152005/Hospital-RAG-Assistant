"""
retrieval/chain.py
─────────────────────────────────────────────────────────────────────
Step 6: Build the full RAG chain (Retriever + LLM + Prompt).

Flow:
    question → retriever finds top 5 chunks → chunks + question
    sent to Groq (Llama 3.1 70B) → structured answer returned

The system prompt enforces:
    - Answer only from the provided manual context
    - Use numbered steps for procedures
    - Include cause + solution for error codes
    - Honest "not found" response when context doesn't contain the answer
─────────────────────────────────────────────────────────────────────
"""

from langchain_groq import ChatGroq
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from retrieval.retriever import get_retriever, detect_manual_from_query
from config import GROQ_API_KEY, GROQ_MODEL, LLM_TEMPERATURE


# ─────────────────────────────────────────────────────────────────
# SYSTEM PROMPT
# ─────────────────────────────────────────────────────────────────
SYSTEM_PROMPT_TEMPLATE = """You are an expert biomedical engineering assistant for a hospital.
Your role is to help clinical and biomedical engineers with technical questions about medical devices.

You have access to the official manuals of the following devices:
- BeneFusion VP3 Vet Infusion Pump (Mindray Scientific)
- MAC 2000 ECG Analysis System (GE Healthcare)
- Fresenius 4008S Hemodialysis System (Fresenius Medical Care)

STRICT RULES:
1. Answer ONLY based on the context provided below from the device manuals.
2. If the answer cannot be found in the provided context, respond with:
   "This information was not found in the available manuals. Please refer to the complete manual or contact the manufacturer's technical support."
3. For error codes and alarms, ALWAYS structure your answer as:
   - What it means
   - Why it happens (cause)
   - How to fix it (step-by-step)
4. For procedures and maintenance tasks, use numbered steps.
5. Be precise and technical — the user is a qualified biomedical engineer.
6. If the answer applies to a specific device, clearly state which device.
7. Do NOT make up information or fill gaps with general knowledge.

Context from device manuals:
─────────────────────────────
{context}
─────────────────────────────

Engineer's Question: {question}

Answer:"""

PROMPT = PromptTemplate(
    template=SYSTEM_PROMPT_TEMPLATE,
    input_variables=["context", "question"],
)


# ─────────────────────────────────────────────────────────────────
# LLM SETUP
# ─────────────────────────────────────────────────────────────────
def get_llm():
    """Initialize the Groq LLM (Llama 3.1 70B - free tier)."""
    if not GROQ_API_KEY:
        raise ValueError(
            "\n[ERROR] GROQ_API_KEY not found in .env file."
            "\nGet your free key at: https://console.groq.com"
        )
    return ChatGroq(
        model=GROQ_MODEL,
        api_key=GROQ_API_KEY,
        temperature=LLM_TEMPERATURE,
    )


# ─────────────────────────────────────────────────────────────────
# CHAIN BUILDER
# ─────────────────────────────────────────────────────────────────
def build_qa_chain(manual_filter: dict = None):
    """
    Build the full RetrievalQA chain.

    Args:
        manual_filter: optional metadata filter to restrict which
                       manual is searched. If None, searches all 3.

    Returns:
        A LangChain RetrievalQA chain ready to invoke.
    """
    llm       = get_llm()
    retriever = get_retriever(filter=manual_filter)

    chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",           # "stuff" = concatenate all chunks into context
        retriever=retriever,
        chain_type_kwargs={"prompt": PROMPT},
        return_source_documents=True, # so we can show which chunks were used
    )
    return chain


# ─────────────────────────────────────────────────────────────────
# MAIN ASK FUNCTION
# ─────────────────────────────────────────────────────────────────
def ask(question: str, manual_filter: dict = None) -> dict:
    """
    Ask a question and get a grounded answer from the manuals.

    This is the main function used by main.py and the routing agent.

    Args:
        question     : engineer's natural language question
        manual_filter: optional dict to restrict which manual to search.
                       If None, auto-detects from question text.
                       If still None after auto-detect, searches all 3 manuals.

    Returns:
        dict with keys:
            "question"  : original question
            "answer"    : generated answer string
            "sources"   : list of dicts describing chunks used
            "filter_used": which filter was applied (or None)
    """
    # Auto-detect manual from question if no filter provided
    if manual_filter is None:
        manual_filter = detect_manual_from_query(question)

    chain  = build_qa_chain(manual_filter)
    result = chain.invoke({"query": question})

    # Format source information
    sources = []
    for doc in result.get("source_documents", []):
        sources.append({
            "manual":       doc.metadata.get("source_manual", "Unknown"),
            "device_type":  doc.metadata.get("device_type", "Unknown"),
            "page":         doc.metadata.get("page", "?"),
            "section_type": doc.metadata.get("section_type", "Unknown"),
            "preview":      doc.page_content[:200].replace("\n", " ") + "...",
        })

    return {
        "question":    question,
        "answer":      result["result"],
        "sources":     sources,
        "filter_used": manual_filter,
    }
