# ==============================================================================
# main.py - FINAL VERSION FOR PHASE 2
# AI (RAG + Chained Prompting) + Database + Security
# ==============================================================================

# --- Part 1: Imports ---
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base

# Security Imports
from passlib.hash import argon2
from jose import JWTError, jwt
from datetime import datetime, timedelta

# AI/RAG Imports
from langchain_community.llms import Ollama
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
#from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

print("--- Backend Server is starting up... ---")

# --- Part 2: Database Configuration ---
DATABASE_URL = "postgresql://postgres:password@host.docker.internal/soap_notes_db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Part 3: Database Models (The Blueprints) ---
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    notes = relationship("Note", back_populates="owner", cascade="all, delete-orphan")

class Note(Base):
    __tablename__ = "notes"
    id = Column(Integer, primary_key=True, index=True)
    transcript_text = Column(Text, nullable=False)
    soap_note_content = Column(Text, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="notes")

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Part 4: Security & JWT Configuration ---
SECRET_KEY = "a_very_secret_and_long_random_string_for_jwt"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login/")

# --- Part 5: AI Tools Initialization (Global Objects) ---
llm = Ollama(model="tinyllama")
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
print("✅ AI Tools Initialized.")

# --- Part 6: Pydantic Schemas (The "Forms") ---
class UserCreate(BaseModel):
    email: str
    password: str

class UserDisplay(BaseModel):
    id: int
    email: str

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    
class NoteCreate(BaseModel):
    transcript_text: str

class NoteDisplay(BaseModel):
    id: int
    soap_note_content: str

    class Config:
        from_attributes = True

# --- Part 7: FastAPI App & Endpoints ---
app = FastAPI(title="MedNotes.ai - RAG-Powered & Secure")

# --- Security Helper Functions & Auth Endpoints ---
def verify_password(plain_password, hashed_password): return argon2.verify(plain_password, hashed_password)
def create_access_token(data: dict):
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = data.copy()
    to_encode.update({"exp": expire})
    return  jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None: raise credentials_exception
    except JWTError: raise credentials_exception
    user = db.query(User).filter(User.email == email).first()
    if user is None: raise credentials_exception
    return user

@app.post("/register/", response_model=UserDisplay, tags=["Authentication"])
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user: raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = argon2.hash(user.password)
    new_user = User(email=user.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/login/", response_model=Token, tags=["Authentication"])
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

# --- Main AI Endpoint ---

def generate_section_with_rag(section_name: str, context: str) -> str:
    """Helper function to generate a single, focused section of the SOAP note."""
    prompt = f"[INST]Based ONLY on the CONTEXT, extract information for the '{section_name}' section. If no information is found, write 'Not mentioned in transcript.'. CONTEXT: {context} EXTRACTED '{section_name.upper()}' INFORMATION:[/INST]"
    print(f"-> Generating section: {section_name}...")
    response = llm.invoke(prompt)
    return response.strip()

@app.post("/notes/generate/", response_model=NoteDisplay, tags=["SOAP Notes"])
def generate_and_save_soap_note(note_request: NoteCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Performs a full RAG pipeline and then uses chained prompting for structured output."""
    print(f"\n--- New RAG request from user: {current_user.email} ---")
    
    try:
        # RAG - Step 1: Ingest & Retrieve
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        docs = [Document(page_content=note_request.transcript_text)]
        chunks = text_splitter.split_documents(docs)
        
        vector_store = Chroma.from_documents(documents=chunks, embedding=embeddings)
        retriever = vector_store.as_retriever()
        
        context_for_llm = "\n\n".join([doc.page_content for doc in retriever.get_relevant_documents(note_request.transcript_text)])
        print("✅ Retrieved relevant context using RAG.")

        # RAG - Step 2: Chained Generation
        subjective = generate_section_with_rag("Subjective (Patient's complaints)", context_for_llm)
        objective = generate_section_with_rag("Objective (Doctor's observations)", context_for_llm)
        assessment = generate_section_with_rag("Assessment (The diagnosis)", context_for_llm)
        plan = generate_section_with_rag("Plan (The treatment)", context_for_llm)
        
        # Assemble the final note
        final_soap_note = f"**Subjective:**\n{subjective}\n\n**Objective:**\n{objective}\n\n**Assessment:**\n{assessment}\n\n**Plan:**\n{plan}"
        
        # Save to Database
        new_note = Note(transcript_text=note_request.transcript_text, soap_note_content=final_soap_note, owner_id=current_user.id)
        db.add(new_note)
        db.commit()
        db.refresh(new_note)
        
        print(f"✅ Note saved to DB with ID: {new_note.id}")
        return new_note

    except Exception as e: 
        print(f"!!! AN ERROR OCCURRED: {e} !!!")
        raise HTTPException(status_code=500, detail="An internal error occurred during AI processing.")