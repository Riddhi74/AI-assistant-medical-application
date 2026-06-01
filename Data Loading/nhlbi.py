import re
import bs4
import requests
from pathlib import Path
from langchain_core.documents import Document # type: ignore
from langchain_community.document_loaders import WebBaseLoader #type:ignore
import os
os.environ["USER_AGENT"]="Mozilla/5.0"

def url_filter(href):
    if href and "nhlbi.nih.gov/health/" in href:
        return True
    return False

category_url = {

    "heart_disease": {
        "base_index": "https://www.nhlbi.nih.gov/health-topics/all-topics",
        "url_filter": url_filter,
        "priority": [
            "https://www.nhlbi.nih.gov/health/heart-failure",
            "https://www.nhlbi.nih.gov/health/atrial-fibrillation",
            "https://www.nhlbi.nih.gov/health/coronary-heart-disease",
            "https://www.nhlbi.nih.gov/health/cardiomyopathy",
            "https://www.nhlbi.nih.gov/health/heart-valve-disease",
            "https://www.nhlbi.nih.gov/health/high-blood-pressure",
            "https://www.nhlbi.nih.gov/health/metabolic-syndrome",
            "https://www.nhlbi.nih.gov/health/sudden-cardiac-arrest",
            "https://www.nhlbi.nih.gov/health/heart-attack",
            "https://www.nhlbi.nih.gov/health/arrhythmia",
            "https://www.nhlbi.nih.gov/health/cholesterol",
            "https://www.nhlbi.nih.gov/health/peripheral-artery-disease",
            "https://www.nhlbi.nih.gov/health/stroke",
            "https://www.nhlbi.nih.gov/health/congenital-heart-defects",
            "https://www.nhlbi.nih.gov/health/pericarditis",
            "https://www.nhlbi.nih.gov/health/endocarditis",
            "https://www.nhlbi.nih.gov/health/myocarditis",
        ],
        "source_type": "nhlbi_heart",
        "base_domain": "https://www.nhlbi.nih.gov",
    },

    "respiratory": {
        "base_index": "https://www.nhlbi.nih.gov/health-topics/all-topics",
        "url_filter": url_filter,
        "priority": [
            "https://www.nhlbi.nih.gov/health/asthma",
            "https://www.nhlbi.nih.gov/health/copd",
            "https://www.nhlbi.nih.gov/health/sleep-apnea",
            "https://www.nhlbi.nih.gov/health/pulmonary-hypertension",
            "https://www.nhlbi.nih.gov/health/pulmonary-embolism",
            "https://www.nhlbi.nih.gov/health/sarcoidosis",
            "https://www.nhlbi.nih.gov/health/cystic-fibrosis",
            "https://www.nhlbi.nih.gov/health/bronchiectasis",
            "https://www.nhlbi.nih.gov/health/idiopathic-pulmonary-fibrosis",
            "https://www.nhlbi.nih.gov/health/pneumonia",
            "https://www.nhlbi.nih.gov/health/pleural-disorders",
        ],
        "source_type": "nhlbi_respiratory",
        "base_domain": "https://www.nhlbi.nih.gov",
    },

    "blood_disease": {
        "base_index": "https://www.nhlbi.nih.gov/health-topics/all-topics",
        "url_filter": url_filter,
        "priority": [
            "https://www.nhlbi.nih.gov/health/anemia",
            "https://www.nhlbi.nih.gov/health/sickle-cell-disease",
            "https://www.nhlbi.nih.gov/health/thalassemia",
            "https://www.nhlbi.nih.gov/health/hemophilia",
            "https://www.nhlbi.nih.gov/health/von-willebrand-disease",
            "https://www.nhlbi.nih.gov/health/deep-vein-thrombosis",
            "https://www.nhlbi.nih.gov/health/thrombocythemia-thrombocytosis",
            "https://www.nhlbi.nih.gov/health/iron-deficiency-anemia",
            "https://www.nhlbi.nih.gov/health/aplastic-anemia",
            "https://www.nhlbi.nih.gov/health/immune-thrombocytopenia",
        ],
        "source_type": "nhlbi_blood",
        "base_domain": "https://www.nhlbi.nih.gov",
    },
}

BOILERPLATE = [
    "National Heart, Lung, and Blood Institute",
    "U.S. Department of Health",
    "Skip to main content",
    "Privacy Policy",
    "Accessibility",
    "Social media",
    "Follow us",
    "Subscribe to",
    "Copyright",
    "Web Policies",
    "HHS Vulnerability Disclosure",
    "Contact NHLBI",
    "Careers",
    "Site Map",
    "Freedom of Information",
]

def crawl_index(base_index, base_domain, url_filter):
    print(f"[Index] Crawling {base_index}")
    try:
        resp = requests.get(base_index, timeout=15, headers={"User-Agent": os.environ["USER_AGENT"]})
        resp.raise_for_status()
    except Exception as e:
        print(f"[Index] FAILED: {e}")
        return []
    soup = bs4.BeautifulSoup(resp.text, "html.parser")
    found = set()
    for tag in soup.find_all("a", href=True):
        href = tag["href"]
        if href.startswith("/"):
            href = base_domain + href
        href = href.split("?")[0].split("#")[0]
        if url_filter(href):
            found.add(href)
    urls = sorted(found)
    print(f"[Index] Discovered {len(urls)} URLs")
    return urls

def scrape_pages(urls):
    loader = WebBaseLoader(
        web_paths=tuple(urls),
        requests_per_second=1,
    )
    docs = loader.load()
    return docs

def clean_text(text):
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"\S+@\S+\.\S+", "", text)
    lines = text.split("\n")
    clean_lines = []
    for line in lines:
        line = line.strip()
        if len(line) < 20:
            continue
        found_boilerplate = False
        for bp in BOILERPLATE:
            if bp.lower() in line.lower():
                found_boilerplate = True
                break
        if found_boilerplate:
            continue
        clean_lines.append(line)
    text = "\n".join(clean_lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)
    return text.strip()

def preprocess_docs(docs, category, source_type):
    cleaned_docs = []
    for doc in docs:
        cleaned = clean_text(doc.page_content)
        if len(cleaned) < 200:
            continue
        source = doc.metadata.get("source", "")
        slug = source.rstrip("/").split("/")[-1]
        disease_name = slug.replace("-", " ").replace("_", " ").title()
        cleaned_docs.append(Document(
            page_content=cleaned,
            metadata={
                "source":   source,
                "disease":  disease_name,
                "type":     source_type,
                "language": "en",
                "category": category,
            }
        ))
    return cleaned_docs

def save_docs(docs, folder, filename):
    sections = []
    for doc in docs:
        m = doc.metadata
        sections.append(
            f"[DISEASE: {m['disease']}]\n"
            f"[CATEGORY: {m['category']}]\n"
            f"[TYPE: {m['type']}]\n"
            f"[LANGUAGE: {m['language']}]\n"
            f"[SOURCE: {m['source']}]\n"
            f"{doc.page_content}"
        )
    out_path = folder / filename
    out_path.write_text("\n\n---\n\n".join(sections), encoding="utf-8")
    print(f"[Saved] {out_path} ({out_path.stat().st_size:,} bytes)")

def run_category(cat_name, cfg):
    print(f"\n--- {cat_name.upper()} ---")
    folder = Path(f"data/{cat_name}")
    folder.mkdir(parents=True, exist_ok=True)

    discovered = []
    if cfg.get("base_index"):
        discovered = crawl_index(cfg["base_index"], cfg["base_domain"], cfg["url_filter"])

    all_urls = list(dict.fromkeys(cfg["priority"] + discovered))
    print(f"[URLs] {len(cfg['priority'])} priority + {len(discovered)} discovered = {len(all_urls)} total")

    raw_docs = scrape_pages(all_urls)
    clean_docs = preprocess_docs(raw_docs, cat_name, cfg["source_type"])

    if not clean_docs:
        print(f"[Warning] No usable docs for {cat_name}")
        return 0

    save_docs(clean_docs, folder, f"{cat_name}.txt")
    return len(clean_docs)

def run_all():
    for cat_name, cfg in category_url.items():
        run_category(cat_name, cfg)

if __name__ == "__main__":
    run_all()