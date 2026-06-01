import re
import bs4
import requests
from pathlib import Path
from langchain_core.documents import Document # type: ignore
from langchain_community.document_loaders import WebBaseLoader #type:ignore
import os
os.environ["USER_AGENT"]="Mozilla/5.0"

def url_filter(href):
    if (
        href
        and "medlineplus.gov/" in href
        and href.endswith(".html")
        and "/ency/" not in href
        and "/lab-tests/" not in href
    ):
        return True
    return False

category_url = {

    "general_disease": {
        "base_index": "https://medlineplus.gov/healthtopics.html",
        "url_filter": url_filter,
        "priority": [
            "https://medlineplus.gov/commoncold.html",
            "https://medlineplus.gov/flu.html",
            "https://medlineplus.gov/pneumonia.html",
            "https://medlineplus.gov/tuberculosis.html",
            "https://medlineplus.gov/malaria.html",
            "https://medlineplus.gov/dengue.html",
            "https://medlineplus.gov/typhoidfever.html",
            "https://medlineplus.gov/lyme.html",
            "https://medlineplus.gov/hiv.html",
            "https://medlineplus.gov/hepatitis.html",
            "https://medlineplus.gov/hepatitisb.html",
            "https://medlineplus.gov/hepatitisc.html",
            "https://medlineplus.gov/diabetes.html",
            "https://medlineplus.gov/diabetestype2.html",
            "https://medlineplus.gov/diabetestype1.html",
            "https://medlineplus.gov/obesity.html",
            "https://medlineplus.gov/thyroiddiseases.html",
            "https://medlineplus.gov/hypothyroidism.html",
            "https://medlineplus.gov/hyperthyroidism.html",
            "https://medlineplus.gov/gout.html",
            "https://medlineplus.gov/irritablebowelsyndrome.html",
            "https://medlineplus.gov/crohnsdisease.html",
            "https://medlineplus.gov/ulcerativecolitis.html",
            "https://medlineplus.gov/gerd.html",
            "https://medlineplus.gov/pepticulcer.html",
            "https://medlineplus.gov/appendicitis.html",
            "https://medlineplus.gov/gallstones.html",
            "https://medlineplus.gov/pancreatitis.html",
            "https://medlineplus.gov/cirrhosis.html",
            "https://medlineplus.gov/kidneystones.html",
            "https://medlineplus.gov/chronickidneydisease.html",
            "https://medlineplus.gov/urinarytractinfections.html",
            "https://medlineplus.gov/osteoarthritis.html",
            "https://medlineplus.gov/rheumatoidarthritis.html",
            "https://medlineplus.gov/osteoporosis.html",
            "https://medlineplus.gov/backpain.html",
            "https://medlineplus.gov/fibromyalgia.html",
            "https://medlineplus.gov/polycysticovarysyndrome.html",
            "https://medlineplus.gov/endometriosis.html",
        ],
        "source_type": "medlineplus_general",
        "base_domain": "https://medlineplus.gov",
    },

    "heart_disease": {
        "base_index": None,
        "url_filter": url_filter,
        "priority": [
            "https://medlineplus.gov/coronaryarterydisease.html",
            "https://medlineplus.gov/heartattack.html",
            "https://medlineplus.gov/heartfailure.html",
            "https://medlineplus.gov/arrhythmia.html",
            "https://medlineplus.gov/atrialfibrillation.html",
            "https://medlineplus.gov/cardiomyopathy.html",
            "https://medlineplus.gov/heartvalvediseases.html",
            "https://medlineplus.gov/pericarditis.html",
            "https://medlineplus.gov/endocarditis.html",
            "https://medlineplus.gov/myocarditis.html",
            "https://medlineplus.gov/congenitalheartdefects.html",
            "https://medlineplus.gov/heartdiseaseinwomen.html",
            "https://medlineplus.gov/peripheralarterialdisease.html",
            "https://medlineplus.gov/aorticaneurysm.html",
            "https://medlineplus.gov/highbloodpressure.html",
            "https://medlineplus.gov/cholesterol.html",
            "https://medlineplus.gov/triglycerides.html",
            "https://medlineplus.gov/stroke.html",
            "https://medlineplus.gov/transientischemicattack.html",
        ],
        "source_type": "medlineplus_heart",
        "base_domain": "https://medlineplus.gov",
    },

    "respiratory": {
        "base_index": None,
        "url_filter": url_filter,
        "priority": [
            "https://medlineplus.gov/asthma.html",
            "https://medlineplus.gov/copd.html",
            "https://medlineplus.gov/emphysema.html",
            "https://medlineplus.gov/chronicbronchitis.html",
            "https://medlineplus.gov/lungcancer.html",
            "https://medlineplus.gov/pulmonaryembolism.html",
            "https://medlineplus.gov/pulmonaryhypertension.html",
            "https://medlineplus.gov/sarcoidosis.html",
            "https://medlineplus.gov/cysticfibrosis.html",
            "https://medlineplus.gov/sleepapnea.html",
            "https://medlineplus.gov/sinusitis.html",
            "https://medlineplus.gov/bronchitis.html",
        ],
        "source_type": "medlineplus_respiratory",
        "base_domain": "https://medlineplus.gov",
    },

    "neurological": {
        "base_index": None,
        "url_filter": url_filter,
        "priority": [
            "https://medlineplus.gov/alzheimersdisease.html",
            "https://medlineplus.gov/parkinsonsdisease.html",
            "https://medlineplus.gov/multiplesclerosis.html",
            "https://medlineplus.gov/epilepsy.html",
            "https://medlineplus.gov/migraine.html",
            "https://medlineplus.gov/meningitis.html",
            "https://medlineplus.gov/encephalitis.html",
            "https://medlineplus.gov/braintumors.html",
            "https://medlineplus.gov/amyotrophiclateralsclerosis.html",
            "https://medlineplus.gov/huntingtonsdisease.html",
            "https://medlineplus.gov/guillainbarresyndrome.html",
            "https://medlineplus.gov/headache.html",
            "https://medlineplus.gov/dizzinessandvertigo.html",
            "https://medlineplus.gov/tremor.html",
            "https://medlineplus.gov/dementia.html",
        ],
        "source_type": "medlineplus_neuro",
        "base_domain": "https://medlineplus.gov",
    },

    "mental_health": {
        "base_index": None,
        "url_filter": url_filter,
        "priority": [
            "https://medlineplus.gov/depression.html",
            "https://medlineplus.gov/anxiety.html",
            "https://medlineplus.gov/bipolardisorder.html",
            "https://medlineplus.gov/schizophrenia.html",
            "https://medlineplus.gov/obsessivecompulsivedisorder.html",
            "https://medlineplus.gov/posttraumaticstressdisorder.html",
            "https://medlineplus.gov/eatingdisorders.html",
            "https://medlineplus.gov/attentiondeficithyperactivitydisorder.html",
            "https://medlineplus.gov/autism.html",
            "https://medlineplus.gov/panicdisorder.html",
            "https://medlineplus.gov/phobias.html",
            "https://medlineplus.gov/sleepingdisorders.html",
            "https://medlineplus.gov/substanceusedisorders.html",
        ],
        "source_type": "medlineplus_mental",
        "base_domain": "https://medlineplus.gov",
    },

    "cancer": {
        "base_index": None,
        "url_filter": url_filter,
        "priority": [
            "https://medlineplus.gov/cancer.html",
            "https://medlineplus.gov/breastcancer.html",
            "https://medlineplus.gov/lungcancer.html",
            "https://medlineplus.gov/coloncancer.html",
            "https://medlineplus.gov/prostatecancer.html",
            "https://medlineplus.gov/leukemia.html",
            "https://medlineplus.gov/lymphoma.html",
            "https://medlineplus.gov/pancreaticcancer.html",
            "https://medlineplus.gov/kidneycancer.html",
            "https://medlineplus.gov/bladdercancer.html",
            "https://medlineplus.gov/thyroidcancer.html",
            "https://medlineplus.gov/stomachcancer.html",
            "https://medlineplus.gov/livercancer.html",
            "https://medlineplus.gov/cervicalcancer.html",
            "https://medlineplus.gov/ovariancancer.html",
            "https://medlineplus.gov/skincancer.html",
            "https://medlineplus.gov/multiplemyeloma.html",
            "https://medlineplus.gov/esophagealcancer.html",
        ],
        "source_type": "medlineplus_cancer",
        "base_domain": "https://medlineplus.gov",
    },

    "eye_disease": {
        "base_index": None,
        "url_filter": url_filter,
        "priority": [
            "https://medlineplus.gov/glaucoma.html",
            "https://medlineplus.gov/cataract.html",
            "https://medlineplus.gov/maculardegeneration.html",
            "https://medlineplus.gov/diabeticeyeproblems.html",
            "https://medlineplus.gov/conjunctivitis.html",
            "https://medlineplus.gov/retinaldetachment.html",
            "https://medlineplus.gov/amblyopia.html",
            "https://medlineplus.gov/cornealdisorders.html",
            "https://medlineplus.gov/refractiveerrors.html",
        ],
        "source_type": "medlineplus_eye",
        "base_domain": "https://medlineplus.gov",
    },

    "pediatric_disease": {
        "base_index": None,
        "url_filter": url_filter,
        "priority": [
            "https://medlineplus.gov/chickenpox.html",
            "https://medlineplus.gov/measles.html",
            "https://medlineplus.gov/mumps.html",
            "https://medlineplus.gov/whoopingcough.html",
            "https://medlineplus.gov/croup.html",
            "https://medlineplus.gov/kawasaki.html",
            "https://medlineplus.gov/tonsillitis.html",
            "https://medlineplus.gov/downsyndrome.html",
            "https://medlineplus.gov/birthdefects.html",
            "https://medlineplus.gov/cysticfibrosis.html",
        ],
        "source_type": "medlineplus_pediatric",
        "base_domain": "https://medlineplus.gov",
    },
}

BOILERPLATE = [
    "MedlinePlus links to health information",
    "A service of the National Library",
    "National Institutes of Health",
    "U.S. Department of Health",
    "Skip navigation",
    "Privacy Policy",
    "Accessibility",
    "Social media",
    "Follow us",
    "Subscribe to",
    "Copyright",
    "NIH MedlinePlus Magazine",
    "Connect with NLM",
    "Web Policies",
    "HHS Vulnerability Disclosure",
    "National Library of Medicine",
    "8600 Rockville Pike",
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
        slug = re.sub(r"\.(html|htm)$", "", slug)
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