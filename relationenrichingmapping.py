import json
import csv

def enrich_json_with_entity_roles(json_path, csv_path, output_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    csv_data = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) != 5:
                continue
            article, sentence, funding, technical_support, facilities = row
            try:
                csv_data.append({
                    'article': article.strip(),
                    'sentence': sentence.strip(),
                    'funding': float(funding),
                    'technical_support': float(technical_support),
                    'facilities': float(facilities)
                })
            except ValueError:
                continue

    for title, entry in data.items():
        if "ner" not in entry:
            continue

        persons = entry["ner"].get("person", [])
        orgs = entry["ner"].get("orgs", [])
        entity_roles = {}

        matching_rows = [row for row in csv_data if row['article'] == title]

        for row in matching_rows:
            sentence_lower = row['sentence'].lower()

            role_scores = {
                "funding": row["funding"],
                "technical_support": row["technical_support"],
                "facilities": row["facilities"]
            }
            max_role = max(role_scores, key=role_scores.get)

            for person in persons:
                if person.lower() in sentence_lower:
                    entity_roles[person] = max_role

            for org in orgs:
                if org.lower() in sentence_lower:
                    entity_roles[org] = max_role

        if entity_roles:
            entry["entity_roles"] = entity_roles

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("done")


enrich_json_with_entity_roles(
    '/Users/Jakub/Desktop/iswc/new_ner_output.json',
    '/Users/Jakub/Desktop/iswc/relation_bgev15_semi_08.csv',
    '/Users/Jakub/Desktop/iswc/last_entity_role_enrichment_8_6.json'
)
