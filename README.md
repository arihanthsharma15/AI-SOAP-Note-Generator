# 🤖 AI SOAP Note Generator

A full-stack RAG application that generates clinical SOAP notes from transcripts using a **100% locally-run LLM**, ensuring complete data privacy.

This project was built to run efficiently on standard hardware, demonstrating a robust AI pipeline even with resource constraints.

---

### ✨ **Core Features**
-   **Private by Design:** Uses **Ollama** to run the `tinyllama` model locally. No patient data ever leaves your machine.
-   **RAG-Powered:** Implements a **LangChain**-based RAG pipeline with **ChromaDB** to ensure factual, context-aware note generation and reduce LLM hallucination.
-   **Full-Stack Architecture:** A decoupled frontend (**Streamlit**) and a high-performance backend (**FastAPI**).

---

### 🛠️ **Tech Stack**
-   **AI/RAG:** LangChain, Ollama, ChromaDB, HuggingFace Embeddings
-   **Backend:** FastAPI
-   **Frontend:** Streamlit

---

### 🚀 **How to Run**

**1. Setup:**
```bash
# Clone the repo
git clone https://github.com/arihanthsharma15/AI-SOAP-Note-Generator.git
cd AI-SOAP-Note-Generator

# Create env & install dependencies
conda create -n soap_env python=3.9 -y
conda activate soap_env
pip install -r requirements.txt

# Download the lightweight LLM
ollama run tinyllama
```

**2. Launch (in two terminals):**
```bash
# Terminal 1: Start the Backend
uvicorn main:app --reload

# Terminal 2: Start the Frontend
streamlit run ui.py
```

---
