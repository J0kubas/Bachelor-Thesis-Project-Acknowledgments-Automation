
'''from REL.mention_detection import MentionDetection
from REL.utils import process_results
from REL.entity_disambiguation import EntityDisambiguation
from REL.ner import Cmns, load_flair_ner
from REL.wikipedia import Wikipedia



wiki_version = "wiki_2019"
base_url = "/Volumes/Disk/Mac files/baseproject"

input_text = {
    "my_doc": ("Hello, world!", []),
}

mention_detection = MentionDetection(base_url, wiki_version)
tagger_ner = load_flair_ner("ner-fast-with-lowercase")

tagger_ngram = Cmns(base_url, wiki_version, n=5)
mentions, n_mentions = mention_detection.find_mentions(input_text, tagger_ngram)

config = {
    "mode": "eval",
    "model_path": "ed-wiki-2019",
}
model = EntityDisambiguation(base_url, wiki_version, config)

predictions, timing = model.predict(mentions)
result = process_results(mentions, predictions, input_text)
print(result)
# {'my_doc': [(0, 13, 'Hello, world!', 'Hello_world_program', 0.6534378618767961, 182, '#NGRAM#')]}'''

import json
import requests
import time

WIKIDATA_SEARCH_API = "https://www.wikidata.org/w/api.php"
SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"


TYPE_QIDS = {
    "person": "Q5",
    "organization": "Q43229"
}

def search_wikidata(name):
    params = {
        'action': 'wbsearchentities',
        'search': name,
        'language': 'en',
        'format': 'json',
        'limit': 1
    }
    response = requests.get(WIKIDATA_SEARCH_API, params=params)
    data = response.json()
    if data.get("search"):
        return data["search"][0]["id"]
    return None

def check_type(qid, expected_type):
    type_qid = TYPE_QIDS.get(expected_type)
    query = f"""
    SELECT ?type WHERE {{
      wd:{qid} wdt:P31 ?type .
    }}
    """
    headers = {'Accept': 'application/sparql-results+json'}
    response = requests.get(SPARQL_ENDPOINT, params={'query': query}, headers=headers)
    data = response.json()
    for result in data["results"]["bindings"]:
        t = result["type"]["value"]
        if t.endswith(type_qid):
            return True
    return False

def resolve_entities(data):
    resolved = {}
    seen = set()

    for entry_id, entry in data.items():
        ner = entry.get("ner", {})
        for entity_type in ["person", "orgs"]:
            label = "person" if entity_type == "person" else "organization"
            for name in ner.get(entity_type, []):
                if name in seen:
                    continue  
                seen.add(name)
                #qid = search_wikidata(name)
                qid = search_wikidata_fuzzy(name)
                time.sleep(0.5)  
                if qid:
                    resolved[name] = {
                        "qid": qid,
                        "wikidata_url": f"https://www.wikidata.org/wiki/{qid}",
                        "type": label
                    }
                else:
                    resolved[name] = {
                        "qid": None,
                        "wikidata_url": None,
                        "type": label,
                        "note": "No valid match or type mismatch"
                    }

    return resolved


#-----------------------------
#-----------------------------
from rapidfuzz import fuzz
import re

def normalize_text(text):
    text = text.lower()
    text = re.sub(r"[\-\s]+", " ", text) 
    text = re.sub(r'the ', '', text)
    text = text.strip()
    return text

def search_wikidata_fuzzy(name, threshold=80):
    params = {
        'action': 'wbsearchentities',
        'search': name,
        'language': 'en',
        'format': 'json',
        'limit': 10  
    }
    response = requests.get(WIKIDATA_SEARCH_API, params=params)
    data = response.json()
    if not data.get("search"):
        return None

    normalized_name = normalize_text(name)

    for result in data["search"]:
        candidate_label = result.get("label", "")
        normalized_label = normalize_text(candidate_label)
        similarity = fuzz.token_sort_ratio(normalized_name, normalized_label)
        if similarity >= threshold:
            return result["id"] 

    return None

#-----------------------------

with open("/Users/Jakub/Desktop/iswc/last_entity_role_enrichment_8_6.json") as f:
    input_data = json.load(f)

results = resolve_entities(input_data)

with open("/Users/Jakub/Desktop/iswc/fuzzy_entity_link_newner_comp_2.json", "w") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
