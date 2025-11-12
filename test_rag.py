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
You are a highly skilled medical scribe. Your task is to meticulously create a clinical SOAP note from the provided CONTEXT.

**CONTEXT FROM TRANSCRIPT:**
---
{context_for_llm}
---

**TASK & RULES:**
1.  Analyze the CONTEXT and generate a SOAP note with four sections: (Subjective), (Objective), (Assessment), and (Plan).
2.  The (Subjective) section should detail the patient's complaints and reported history, structured by body system (e.g., Eyes:, Heart:, etc.).
3.  The (Objective) section should list the doctor's physical examination findings, starting with Vitals.
4.  The (Assessment) section MUST list the diagnoses with their corresponding ICD-10 codes if mentioned in the context.
5.  The (Plan) section must be structured by diagnosis, detailing the management plan for each.
6.  The output must be professional, concise, and based STRICTLY on the information within the CONTEXT. Do not invent any information.
7.  Do not add any introductory or concluding phrases. Start directly with "(Subjective)" and end after the plan.

**EXAMPLE OUTPUT FORMAT:**
(Subjective)
Patient: [Patient's name if available]
[Patient's description and primary complaint...]
Eyes: [Details about vision...]
Heart: [Details about heart history...]

(Objective)
On examination:
Vitals: [Pulse, BP, Temp, etc.]
Head: [Exam findings...]
Eyes: [Exam findings...]

(Assessment)
[ICD-10 Code] - [Diagnosis Name]

(Plan)
[Diagnosis Name] (ICD-10: [Code])
[Details of the plan for this diagnosis...]

**START OF SOAP NOTE GENERATION:**
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