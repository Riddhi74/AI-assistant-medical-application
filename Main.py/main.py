from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from pathlib import Path
from typing import Optional
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent / "embeeding"))
sys.path.append(str(Path(__file__).resolve().parent.parent / "LLM"))

from LLM import load_llm

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

CHROMA_BASE_DIR = Path(__file__).resolve().parent.parent / "chroma_db"

print("Loading embeddings...")
embeddings = OllamaEmbeddings(model="nomic-embed-text")

print("Loading LLM...")
llm = load_llm()


class ChatRequest(BaseModel):
    query: str
    category: Optional[str] = None


def search(query, category=None, top_k=3):
    if category:
        chroma_path = CHROMA_BASE_DIR / category
        if not chroma_path.exists():
            return []
        vectorstore = Chroma(
            persist_directory=str(chroma_path),
            embedding_function=embeddings,
            collection_name=category,
        )
        return vectorstore.similarity_search(query, k=top_k)

    docs = []
    for cat_path in CHROMA_BASE_DIR.iterdir():
        if not cat_path.is_dir():
            continue
        vectorstore = Chroma(
            persist_directory=str(cat_path),
            embedding_function=embeddings,
            collection_name=cat_path.name,
        )
        docs.extend(vectorstore.similarity_search(query, k=1))
    return docs[:top_k]


def build_prompt(query, docs):
    context = "\n\n".join([
        f"Disease: {d.metadata.get('disease', 'Unknown')}\n{d.page_content}"
        for d in docs
    ])
    return f"""You are a helpful medical assistant. Answer using only the context below.
Be concise and clear. If unsure, say so.

Context:
{context}

Question: {query}
Answer:"""


def stream_response(query, docs):
    prompt = build_prompt(query, docs)
    for chunk in llm.stream(prompt):
        yield chunk


@app.post("/chat")
def chat(req: ChatRequest):
    docs = search(req.query, req.category)

    if not docs:
        return {"answer": "No relevant information found. Try rephrasing or selecting a specific category."}

    return StreamingResponse(
        stream_response(req.query, docs),
        media_type="text/plain"
    )


@app.get("/")
def root():
    return {"status": "Atom AI running", "model": "phi3:mini"}