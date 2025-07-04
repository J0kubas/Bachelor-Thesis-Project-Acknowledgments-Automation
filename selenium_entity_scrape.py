import json
import time
import re
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import os


BAD_INSTANCE_TYPES = {
    "human", "person", "natural person", "plant", "animal", "place", "geographical object"
}


options = webdriver.ChromeOptions()
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)


with open("/Users/Jakub/Desktop/iswc/data_with_added_uri.json", "r") as f:
    ner_data = json.load(f)

entity_cache = {}

def get_duckduckgo_wikidata_links(entity, max_results=3):
    query = f"site:wikidata.org {entity}"
    url = f"https://duckduckgo.com/?q={query}"
    driver.get(url)
    time.sleep(2) 

    urls = []
    links = driver.find_elements(By.CSS_SELECTOR, "article a[href*='wikidata.org/wiki']")
    for link in links[:max_results]:
        href = link.get_attribute("href")
        if href and "wikidata.org/wiki/" in href:
            urls.append(href.split("?")[0])
    return urls

def get_instance_of(wikidata_url):
    try:
        qid = wikidata_url.rstrip('/').split('/')[-1]
        response = requests.get(f"https://www.wikidata.org/wiki/Special:EntityData/{qid}.json")
        if response.status_code == 200:
            data = response.json()
            claims = data["entities"][qid]["claims"]
            if "P31" in claims:
                labels = []
                for claim in claims["P31"]:
                    obj_id = claim["mainsnak"]["datavalue"]["value"]["id"]
                    label_res = requests.get(f"https://www.wikidata.org/wiki/Special:EntityData/{obj_id}.json")
                    if label_res.status_code == 200:
                        obj_data = label_res.json()
                        label = obj_data["entities"][obj_id]["labels"]["en"]["value"].lower()
                        labels.append(label)
                return labels
    except Exception as e:
        print(f"Error querying API: {e}")
    return []

linked_entities = {}

for paper_id, paper_info in ner_data.items():
    orgs = paper_info.get("ner", {}).get("orgs", [])
    for org in orgs:
        if org in entity_cache:
            result = entity_cache[org]
        else:
            urls = get_duckduckgo_wikidata_links(org)
            result = None
            for url in urls:
                labels = get_instance_of(url)
                if not any(bad in labels for bad in BAD_INSTANCE_TYPES):
                    result = url
                    break
            entity_cache[org] = result
            time.sleep(1.5) 

        if result:
            if org not in linked_entities:
                linked_entities[org] = {
                    "wikidata_url": result,
                    "paper_ids": []
                }
            linked_entities[org]["paper_ids"].append(paper_id)

with open("/Users/Jakub/Desktop/iswc/selenium_entities.json", "w") as f:
    json.dump(linked_entities, f, indent=2)

driver.quit()


#process_json_entities("/Users/Jakub/Desktop/iswc/data_with_added_uri.json", "/Users/Jakub/Desktop/iswc/selenium_entities.json")


