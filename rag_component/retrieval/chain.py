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
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
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
def build_qa_chain():
    """
    Build the LCEL chain: prompt | llm | output parser.
    The retriever is intentionally kept outside the chain so we can
    capture the source documents separately and return them.

    Returns:
        A runnable LCEL chain that accepts {"context": str, "question": str}
        and returns a plain string answer.
    """
    llm = get_llm()
    return PROMPT | llm | StrOutputParser()


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
            "question"   : original question
            "answer"     : generated answer string
            "sources"    : list of dicts describing chunks used
            "filter_used": which filter was applied (or None)
    """
    # Auto-detect manual from question if no filter provided
    if manual_filter is None:
        manual_filter = detect_manual_from_query(question)

    # Step 1: retrieve relevant chunks (kept separate to capture source docs)
    retriever = get_retriever(filter=manual_filter)
    docs      = retriever.invoke(question)

    # Step 2: build context string from retrieved chunks
    context = "\n\n".join(doc.page_content for doc in docs)

    # Step 3: run the LCEL chain → plain string answer
    chain  = build_qa_chain()
    answer = chain.invoke({"context": context, "question": question})

    # Step 4: format source information for the caller
    sources = []
    for doc in docs:
        sources.append({
            "manual":       doc.metadata.get("source_manual", "Unknown"),
            "device_type":  doc.metadata.get("device_type", "Unknown"),
            "page":         doc.metadata.get("page", "?"),
            "section_type": doc.metadata.get("section_type", "Unknown"),
            "preview":      doc.page_content[:200].replace("\n", " ") + "...",
        })

    return {
        "question":    question,
        "answer":      answer,
        "sources":     sources,
        "filter_used": manual_filter,
    }