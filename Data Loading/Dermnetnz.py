
import re
import bs4
import requests
from pathlib import Path
from langchain_core.documents import Document # type: ignore
from langchain_community.document_loaders import WebBaseLoader #type:ignore
import os
os.environ["USER_AGENT"]="Mozilla/5.0"
 
def url_filter(href):
    if href and "/topics/" in href and href.count("/") == 4:
        return True
    return False
 
category_url={
 
    "skin_disease":{
        "base_index": "https://dermnetnz.org/topics",
        "url_filter": url_filter,
        "priority": [
            "https://dermnetnz.org/topics/acne",
            "https://dermnetnz.org/topics/psoriasis",
            "https://dermnetnz.org/topics/atopic-dermatitis",
            "https://dermnetnz.org/topics/rosacea",
            "https://dermnetnz.org/topics/vitiligo",
            "https://dermnetnz.org/topics/urticaria",
            "https://dermnetnz.org/topics/seborrhoeic-dermatitis",
            "https://dermnetnz.org/topics/contact-dermatitis",
            "https://dermnetnz.org/topics/pityriasis-rosea",
            "https://dermnetnz.org/topics/lichen-planus",
            "https://dermnetnz.org/topics/alopecia-areata",
            "https://dermnetnz.org/topics/scabies",
            "https://dermnetnz.org/topics/impetigo",
            "https://dermnetnz.org/topics/cellulitis",
            "https://dermnetnz.org/topics/chickenpox",
            "https://dermnetnz.org/topics/herpes-simplex",
            "https://dermnetnz.org/topics/herpes-zoster",
            "https://dermnetnz.org/topics/warts",
            "https://dermnetnz.org/topics/molluscum-contagiosum",
            "https://dermnetnz.org/topics/tinea",
            "https://dermnetnz.org/topics/tinea-versicolor",
            "https://dermnetnz.org/topics/fungal-nail-infections",
            "https://dermnetnz.org/topics/candida-skin-infection",
            "https://dermnetnz.org/topics/melanoma",
            "https://dermnetnz.org/topics/basal-cell-carcinoma",
            "https://dermnetnz.org/topics/squamous-cell-carcinoma",
            "https://dermnetnz.org/topics/actinic-keratosis",
            "https://dermnetnz.org/topics/dysplastic-naevi",
            "https://dermnetnz.org/topics/dermatofibroma",
            "https://dermnetnz.org/topics/lupus-erythematosus",
            "https://dermnetnz.org/topics/dermatomyositis",
            "https://dermnetnz.org/topics/scleroderma",
            "https://dermnetnz.org/topics/pemphigus",
            "https://dermnetnz.org/topics/bullous-pemphigoid",
            "https://dermnetnz.org/topics/port-wine-stain",
            "https://dermnetnz.org/topics/melasma",
            "https://dermnetnz.org/topics/hyperpigmentation",
        ],
        "source_type": "dermnet_skin",
        "base_domain": "https://dermnetnz.org",
    }
}
 
DERMNET_BOILERPLATE = [
    "Search DermNet",
    "CtrlK",
    "GO TO DERMNET PRO",
    "Main menu",
    "Topics A-Z",
    "Skin checker",
    "Give feedback",
    "Join DermNet PRO",
    "Quick links",
    "Read more",
    "ADVERTISEMENT",
    "NEWS",
    "Home",
    "Images",
    "Cases",
    "RESOURCES",
    "CONTACT",
    "ABOUT",
    "Contact us",
    "Website feedback",
    "Volunteer",
    "Donate",
    "About DermNet",
    "Editorial process",
    "Website terms",
    "Image licence",
    "FAQ",
    "Privacy policy",
    "Join our newsletter",
    "Join Now",
    "Your email",
    "Your name",
    "Your profession",
    "Profession or specialty",
    "Translate",
    "Glossary",
    "AI image dataset",
    "Quizzes",
    "PO-PASI scoring",
    "Do Not Sell or Share My Personal Information",
    "IMPORTANT NOTICE:",
    "DermNet does not provide a free online consultation service",
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
 
def scrape_dermnet(urls):
    loader=WebBaseLoader(
        web_paths=tuple(urls),
        requests_per_second=1,
    )
    docs=loader.load()
    return docs
 
def clean_dermnet_text(text):
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"\S+@\S+\.\S+", "", text)
    lines = text.split("\n")
    clean_lines = []
    for line in lines:
        line = line.strip()
        if len(line) < 20:
            continue
        found_boilerplate=False
        for bp in DERMNET_BOILERPLATE:
            if bp.lower() in line.lower():
                found_boilerplate=True
                break
        if found_boilerplate:
            continue
        clean_lines.append(line)
    text="\n".join(clean_lines)
    text=re.sub(r"\n{3,}","\n\n",text)
    text=re.sub(r" {2,}"," ",text)
    return text.strip()
 
def preprocess_dermnet_docs(docs, category, source_type):
    cleaned_docs=[]
    for doc in docs:
        cleaned=clean_dermnet_text(doc.page_content)
        if len(cleaned)<200:
            continue
        source=doc.metadata.get("source","")
        disease_name=source.split("/topics/")[-1].replace("-"," ").title()
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
 
    raw_docs = scrape_dermnet(all_urls)
    clean_docs = preprocess_dermnet_docs(raw_docs, cat_name, cfg["source_type"])
 
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
 
