import json
import re

input_path = "/Users/Jakub/Desktop/iswc/aff_clean_final.json"  # Your input file
output_json_path = "/Users/Jakub/Desktop/iswc/ack_clen_newline_final.json"
output_ids_path = "/Users/Jakub/Desktop/dashspace_entry_ids.txt"

pattern = re.compile(r"([a-zA-Z])- ")

with open(input_path, "r", encoding="utf-8") as f:
    data = json.load(f)

matching_ids = []

for entry_id, entry in data.items():
    ack = entry.get("AckSection", "")
    if pattern.search(ack):
        matching_ids.append(entry_id)
        entry["AckSection"] = pattern.sub(r"\1", ack)

with open(output_ids_path, "w") as f:
    for eid in matching_ids:
        f.write(f"{eid}\n")

with open(output_json_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("done")
