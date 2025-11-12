from fastapi import FastAPI
from pydantic import BaseModel
from langchain_community.llms import Ollama
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document

print("--- Backend Server is starting up... ---")

# === 1. Initialize AI Tools ===
llm = Ollama(model="tinyllama")
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
print("✅ AI Tools Initialized.")

# === 2. Create FastAPI App ===
app = FastAPI(title="Disciplined AI SOAP Note Generator")

class TranscriptRequest(BaseModel):
    content: str

# === 3. Helper Function for Chained Prompts ===
def generate_section(section_name: str, context: str) -> str:
    """
    A helper function to generate a single section of the SOAP note.
    This uses a specific prompt for each section.
    """
    prompt = f"""
[INST]
You are a medical scribe. Based ONLY on the provided CONTEXT, extract the information for the "{section_name}" section of a SOAP note.
- Do NOT add any extra titles, labels, or explanations.
- If no information is found for this section in the context, write "Not mentioned in transcript."

CONTEXT:
{context}

EXTRACTED {section_name.upper()} INFORMATION:
[/INST]
"""
    print(f"-> Generating section: {section_name}...")
    response = llm.invoke(prompt)
    return response.strip()

# === 4. The Main API Endpoint ===
@app.post("/generate-soap-note/")
def generate_note(request: TranscriptRequest):
    print(f"\n--- Received new request. ---")
    
    # --- RAG Steps (Retrieval) ---
    vector_store = Chroma.from_texts(
        texts=[request.content], 
        embedding=embeddings, 
        collection_name="temp_collection"
    )
    retriever = vector_store.as_retriever()
    relevant_docs = retriever.get_relevant_documents(request.content) # Use the whole transcript to find context
    context_for_llm = "\n\n".join([doc.page_content for doc in relevant_docs])
    print("Retrieved relevant context for the LLM.")
    
    # --- Chained Prompting Steps (Generation) ---
    # We call the LLM multiple times, once for each section.
    subjective_content = generate_section("Subjective (Patient's complaints and history)", context_for_llm)
    objective_content = generate_section("Objective (Doctor's observations and vitals)", context_for_llm)
    assessment_content = generate_section("Assessment (The diagnosis)", context_for_llm)
    plan_content = generate_section("Plan (The treatment and next steps)", context_for_llm)
    
    # --- Final Assembly ---
    # We combine the results into a clean, final SOAP note.
    final_soap_note = f"""
**Subjective:**
{subjective_content}

**Objective:**
{objective_content}

**Assessment:**
{assessment_content}

**Plan:**
{plan_content}
"""
    
    # Clean up the temporary vector store
    vector_store.delete_collection()
    
    print("--- Request complete. Returning structured SOAP note. ---")
    return {"soap_note": final_soap_note}