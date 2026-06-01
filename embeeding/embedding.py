from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma # type: ignore
from langchain_text_splitters import RecursiveCharacterTextSplitter # type: ignore
from pathlib import Path
from langchain_community.embeddings import OllamaEmbeddings
from langchain_core.documents import Document
import pickle

from pathlib import Path

OLLAMA_MODEL = "nomic-embed-text"


BASE_DIR = Path(__file__).resolve().parent.parent

DATA_FOLDERS = [
    BASE_DIR / "data" / "skin_disease",
    BASE_DIR / "data" / "general_disease",
    BASE_DIR / "data" / "heart_disease",
    BASE_DIR / "data" / "respiratory",
    BASE_DIR / "data" / "neurological",
    BASE_DIR / "data" / "mental_health",
    BASE_DIR / "data" / "cancer",
    BASE_DIR / "data" / "eye_disease",
    BASE_DIR / "data" / "pediatric_disease",
    BASE_DIR / "data" / "blood_disease",
]

def get_embeddings():
    return OllamaEmbeddings(model=OLLAMA_MODEL)

def parse_txt_file(file_path):
     text = Path(file_path).read_text(encoding="utf-8")
     raw_sections = text.split("\n\n---\n\n")
     docs = []
     for section in raw_sections:
        section = section.strip()
        if not section:
            continue
        lines = section.split("\n")
        metadata = {}
        content_lines = []
        for line in lines:
            if line.startswith("[DISEASE:"):
                metadata["disease"] = line.replace("[DISEASE:", "").replace("]", "").strip()
            elif line.startswith("[CATEGORY:"):
                metadata["category"] = line.replace("[CATEGORY:", "").replace("]", "").strip()
            elif line.startswith("[TYPE:"):
                metadata["type"] = line.replace("[TYPE:", "").replace("]", "").strip()
            elif line.startswith("[LANGUAGE:"):
                metadata["language"] = line.replace("[LANGUAGE:", "").replace("]", "").strip()
            elif line.startswith("[SOURCE:"):
                metadata["source"] = line.replace("[SOURCE:", "").replace("]", "").strip()
            else:
                content_lines.append(line)
        content = "\n".join(content_lines).strip()
        if content and metadata:
            docs.append(Document(page_content=content, metadata=metadata))
    
     return docs
   
def chunk_docs(docs, chunk_size=1000, chunk_overlap=100):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    chunked = []
    for doc in docs:
        splits = splitter.split_text(doc.page_content)
        for i, chunk in enumerate(splits):
            chunked.append(Document(
                page_content=chunk,
                metadata={**doc.metadata, "chunk": i}
            ))
    return chunked
 
def load_all_chunks():
    all_chunks = {}
    for cat_folder in DATA_FOLDERS:
        folder = Path(cat_folder)
        if not folder.exists():
            print(f"[Skip] Folder not found: {cat_folder}")
            continue
        txt_files = list(folder.glob("*.txt"))
        if not txt_files:
            print(f"[Skip] No .txt files in: {cat_folder}")
            continue
        cat_name = folder.name
        all_docs = []
        for txt_file in txt_files:
            print(f"  [Parse] {txt_file}")
            docs = parse_txt_file(txt_file)
            all_docs.extend(docs)
        chunked = chunk_docs(all_docs)
        print(f"  [{cat_name}] {len(all_docs)} docs -> {len(chunked)} chunks")
        all_chunks[cat_name] = chunked
    return all_chunks