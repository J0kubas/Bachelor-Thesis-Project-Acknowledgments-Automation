import os
import json
import csv
from pathlib import Path
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import spacy

nlp = spacy.load("en_core_web_trf")

input_path = "/Users/Jakub/Desktop/iswc/new_ner_output.json"
output_csv_path = "/Users/Jakub/Desktop/iswc/relation_bgev15_semi_08.csv"

#model = SentenceTransformer('all-roberta-large-v1')

model = SentenceTransformer("BAAI/bge-large-en-v1.5")

#model = SentenceTransformer("thenlper/gte-large")

#model = SentenceTransformer("BAAI/bge-m3")

topic_examples = {
    "funding": [
        "This work was funded by the XYZ.",
        "The research received financial support from the XYZW.",
        "Funding was provided by ACTIVE and NeOn.",
        "Supported by grant XYZ123.",
        "Research was sponsored by the XYZ.",
        "funded by", "financial", "grant", "sponsored", "funding provided", "fellowship",
        "scholarship", "funds", "financing"
    ],
    "technical_support": [
        "We thank Carsten Lutz and others for useful discussions.",
        "The authors appreciate the technical advice provided by Uli Sattler.",
        "Thanks to Boris Motik for collaboration.",
        "We acknowledge valuable feedback and ideas from colleagues.",
        "Discussions with peers greatly improved this work.",
        "discussions", "feedback", "advice", "collaboration", "input from", "motivation",
        "help", "development", "review", "comments", "opinions"
    ],
    "facilities": [
        "Experiments were conducted at the XYZ.",
        "This work was enabled by the computing resources provided by ABC.",
        "Lab infrastructure support was provided by DEF.",
        "Data was collected using equipment at the LMN .",
        "The simulations used resources hosted at the Supercomputing Center.",
        "infrastructure", "lab", "equipment", "computing resources", "supercomputing", "provided access to",
        "software", "hardware"
    ]
}

topic_labels = list(topic_examples.keys())
topic_embeddings = []

for topic in topic_labels:
    example_embeddings = model.encode(topic_examples[topic])
    averaged_embedding = np.mean(example_embeddings, axis=0)
    topic_embeddings.append(averaged_embedding)

SIM_THRESHOLD = 0.8

def split_into_sentences(text):
    #doc = nlp(text)
    #return [sent.text.strip() for sent in doc.sents if sent.text.strip()]
    doc = nlp(text)
    sentences = []
    for sent in doc.sents:
        sent_text = sent.text.strip()
        if not sent_text:
            continue
        
        semicolon_splits = [s.strip() for s in sent_text.split(';') if s.strip()]
        sentences.extend(semicolon_splits)
    return sentences

def process_acknowledgment_json(json_path, output_csv_path):
    rows = []

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)  

    for article_name, article_data in data.items():
        ack_section = article_data.get("AckSection", "")
        if isinstance(ack_section, str):
            ack_sentences = split_into_sentences(ack_section)
        else:
            continue

        if not ack_sentences:
            continue

        sentence_embeddings = model.encode(ack_sentences)
        sim_matrix = cosine_similarity(sentence_embeddings, topic_embeddings)

        for i, sentence in enumerate(ack_sentences):
            scores = sim_matrix[i]
            row = {
                "article": article_name,
                "sentence": sentence,
                "funding": float(scores[0]),
                "technical_support": float(scores[1]),
                "facilities": float(scores[2])
            }
            rows.append(row)

    with open(output_csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["article", "sentence"] + topic_labels)
        writer.writeheader()
        writer.writerows(rows)

    print("done")


process_acknowledgment_json(input_path, output_csv_path)
