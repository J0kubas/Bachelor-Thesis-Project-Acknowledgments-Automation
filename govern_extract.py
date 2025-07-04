import json
import re

INPUT_FILE = "/Users/Jakub/Desktop/iswc/last and graphs/data_with_added_uri_selenium.json"
OUTPUT_FILE = "/Users/Jakub/Desktop/iswc/last and graphs/data_with_added_uri_selenium1.json"

gov_keywords = [
    r'\bministry\b', r'\boffice\b', r'\bagency\b', r'\bbureau\b', r'\bcommission\b',
    r'\bcouncil\b', r'\bfederal\b', r'\bstate\b', r'\bnational\b', r'\bpublic authority\b',
    r'\bgovernment\b', r'\beuropean\b', r'\bunion\b', r'\bauthority\b', r'\bof china\b',
    r'\bU\.S\.\b', r'\bUnited States\b', r'\beurope\b', r'\bEU\b', r'\bforce\b',
    r'\bmilitary\b', r'\bdefense\b', r'\bdefence\b', r'\barmy\b', r'\bdarpa\b', r'\bfoen\b'
]
gov_pattern = re.compile("|".join(gov_keywords), re.IGNORECASE)

exclusion_keywords = [r'\buniversity\b', r'\bcollege\b', r'\bacademy\b', r'\bschool\b']
exclude_pattern = re.compile("|".join(exclusion_keywords), re.IGNORECASE)

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

url_to_government_flag = {}

for entry in data.values():
    org_names = entry.get("ner", {}).get("orgs", [])
    roles_dict = entry.get("entity_roles_and_wiki", {})

    updated_roles = {}

    for entity, value in roles_dict.items():
        if isinstance(value, list):
            role = value[0]
            url = value[1] if len(value) > 1 else None
        else:
            updated_roles[entity] = value
            continue

        if entity in org_names:
            if exclude_pattern.search(entity):
                is_governmental = False
            elif gov_pattern.search(entity):
                is_governmental = True
            else:
                is_governmental = False

            updated_roles[entity] = {
                "role": role,
                "url": url,
                "is_governmental": is_governmental
            }

            if url:
                if url not in url_to_government_flag:
                    url_to_government_flag[url] = is_governmental
                else:
                    url_to_government_flag[url] = url_to_government_flag[url] or is_governmental
        else:
            updated_roles[entity] = {
                "role": role,
                "url": url
            }

    entry["entity_roles_and_wiki"] = updated_roles

for entry in data.values():
    roles_dict = entry.get("entity_roles_and_wiki", {})
    for entity, value in roles_dict.items():
        if isinstance(value, dict) and "url" in value:
            url = value["url"]
            if url in url_to_government_flag and "is_governmental" in value:
                value["is_governmental"] = url_to_government_flag[url]

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("done")

