# --- Imports and Initializations (Steps 1 & 2) ---
from langchain_community.llms import Ollama
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import TextLoader
# NOTE: We are not using RetrievalQA chain directly anymore for the final call
# from langchain.chains import RetrievalQA 

print("--- RAG Engine Test Script (Smart Prompt Version) ---")

llm = Ollama(model="tinyllama")
embeddings = OllamaEmbeddings(model="tinyllama")
vector_store = Chroma(collection_name="rag_test_collection", embedding_function=embeddings)

# --- Data Loading and Storing (Steps 3 & 4) ---
loader = TextLoader('./sample.txt')
documents = loader.load()
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = text_splitter.split_documents(documents)
vector_store.add_documents(chunks)
print("✅ Text has been processed and stored in the vector database.")

# --- Step 5: The "Retrieval" Step ---
# Instead of a full chain, we only use the "retriever" part for now.
# This will find the most relevant chunks based on a query.
retriever = vector_store.as_retriever()
query_for_retrieval = "What did the patient complain about, what did the doctor observe, what is the diagnosis and what is the treatment plan?"
relevant_docs = retriever.get_relevant_documents(query_for_retrieval)

# Combine the content of the relevant documents into a single string.
context_for_llm = "\n\n".join([doc.page_content for doc in relevant_docs])
print("✅ Retrieved relevant context from the transcript.")

# --- Step 6: The "Smart" Prompt Engineering Step ---
# This is where we build a powerful, structured prompt.
prompt_template = f"""
You are an expert medical assistant. Your task is to generate a structured SOAP note from the provided context.
The context is a transcript of a doctor-patient conversation.

**INSTRUCTIONS:**
- You MUST generate a note with ONLY these four sections: Subjective, Objective, Assessment, Plan.
- Do NOT add any extra explanation or introductory sentences.
- Base your answers STRICTLY on the information given in the context below.

**CONTEXT FROM TRANSCRIPT:**
---
{context_for_llm}
---

**GENERATED SOAP NOTE:**
"""

print("\n🤔 Sending the Smart Prompt to the LLM...")
print("⏳ Generating the structured note... (This might take 10-20 seconds)")

# --- Step 7: Final LLM Call and Result ---
# We call the LLM directly with our powerful, custom prompt.
final_response = llm.invoke(prompt_template)

print("\n" + "="*30)
print("🎉 Final Structured Result:")
print(final_response)
print("="*30)

# --- Clean up ---
vector_store.delete_collection()
print("\n✅ Test complete. Collection cleaned up.")