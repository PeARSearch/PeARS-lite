import glob
import json
from collections import defaultdict
import random
import requests

import nltk
from nltk.corpus import framenet as fn

from utils import clean_texts

# copied from IncelFillmore project https://gitlab.com/sociofillmore/incel-fillmore/-/blob/main/notebooks/scraped_corpus/agentivity.ipynb
def find_inherited_role(src_frame, tgt_frame, tgt_role, verbose=False):
    if verbose: 
        print("Comparing:", src_frame, tgt_frame)

    if src_frame == tgt_frame:
        return tgt_role

    for fr in fn.frame(src_frame).frameRelations:
        if fr.type.name == "Inheritance" and fr.subFrameName == src_frame:
            _inherited_role = find_inherited_role(fr.superFrameName, tgt_frame, tgt_role)
            if _inherited_role:
                for fer in fr.feRelations:
                    if fer.superFEName == _inherited_role:
                        if verbose: 
                            print(f"{fr.type.name}:", f"{fr.subFrameName}.{fer.subFEName}<=={fr.superFrameName}.{_inherited_role}")
                        return fer.subFEName
    return None


def find_agentive_role(frame, verbose=False):
    ia_role = find_inherited_role(frame, "Intentionally_act", "Agent", verbose=verbose)
    if ia_role:
        return ia_role, "Intentionally_act"
    
    ta_role = find_inherited_role(frame, "Transitive_action", "Agent", verbose=verbose)
    if ta_role:
        return ta_role, "Transitive_action"
    
    return None, None

def get_sentence_stream(docs, k=20):
    for _ in range(k):
        doc = random.choice(docs)
        with open(doc, encoding="utf-8") as f:
            lines = f.readlines()
        
        for _ in range(5):  # 5 tries to get a 'good' line
            line = random.choice(lines)
            if len(line) > 25:
                break
        line_sents = nltk.sent_tokenize(line, language="french")
        for s in line_sents:
            if len(s) > 10 and len(s) < 250:
                yield s


def make_queries():
    docs = glob.glob("../../../datasets/personas/personas_raw/multiling_recipes_fr_sample400/*.txt")

    actions = []
    entities = []
    attributes = []

    sentence_stream = get_sentence_stream(docs, k=1000)
    while len(attributes) < 10 or len(actions) < 10:
        s = next(sentence_stream)
        s_matched = False
        frame_structures = get_frame_structures(s.lower())
        for fs in frame_structures:
            fs_id, frame = fs.split(".")
            entity_inh_role = find_inherited_role(frame, "Entity", "Entity")
            
            if entity_inh_role is not None:
                if not s_matched:
                    print(s)
                    s_matched = True
                print(f"ENTITY: {frame}->{frame_structures[fs]['_TRIGGER']}")
                print("\tframe info:", json.dumps(frame_structures[fs], ensure_ascii=False, sort_keys=True))
                print()
                entities.append(frame_structures[fs]['_TRIGGER'])

            action_inh_role = find_inherited_role(frame, "Transitive_action", "Patient")
            if action_inh_role is not None and action_inh_role in frame_structures[fs]:
                if not s_matched:
                    print(s)
                    s_matched = True
                print(f"ACTION: {frame}->{frame_structures[fs]['_TRIGGER']}")
                print("\tframe info:", json.dumps(frame_structures[fs], ensure_ascii=False, sort_keys=True))
                print()
                actions.append(clean_texts(f"{frame_structures[fs]['_TRIGGER']} {frame_structures[fs][action_inh_role]}", "french"))

            attrib_inh_role = find_inherited_role(frame, "Attributes", "Entity")
            if attrib_inh_role is not None and attrib_inh_role in frame_structures[fs]:
                if not s_matched:
                    print(s)
                    s_matched = True
                print(f"ATTRIBUTE: {frame}->{frame_structures[fs]['_TRIGGER']}")
                print("\tframe info:", json.dumps(frame_structures[fs], ensure_ascii=False, sort_keys=True))
                print()
                attributes.append(clean_texts(f"{frame_structures[fs]['_TRIGGER']} {frame_structures[fs][attrib_inh_role]}", "french"))

    print("==================")
    print("Entity:\n\t" + "\n\t".join(entities[:10]))
    print("Actions:\n\t" + "\n\t".join(actions))
    print("Attributes:\n\t" + "\n\t".join(attributes))


def get_frame_structures(s):
    r = requests.get("http://localhost:2233/analyze", params={"text": s})
    data = r.json()
    frame_analyses = data["analyses"]
    frame_structures = defaultdict(lambda: defaultdict(str))
    for fa in frame_analyses:
        for frame_list, token in zip(fa["frame_list"], fa["tokens"]):
            for frame_label in frame_list:
                annotation, struct_id = frame_label.split("@")
                if annotation.startswith("T:"):
                    frame_name = annotation[2:]
                    rel_name = "_TRIGGER"
                else:
                    frame_name, rel_name = annotation[2:].split(":")
                s_key = f"{struct_id}.{frame_name}"
                if frame_structures[s_key][rel_name]:
                    frame_structures[s_key][rel_name] += f" {token}"
                else:
                    frame_structures[s_key][rel_name] = token
    return frame_structures

def test_sample_sentences():
    docs = glob.glob("../../../datasets/personas/personas_raw/multiling_recipes_fr_sample400/*.txt")

    sentences = []
    while len(sentences) < 10:
        doc = random.choice(docs)
        with open(doc, encoding="utf-8") as f:
            lines = f.readlines()
        
        for _ in range(5):  # 5 tries to get a 'good' line
            line = random.choice(lines)
            if len(line) > 25:
                break
        line_sents = nltk.sent_tokenize(line, language="french")
        for s in line_sents:
            if len(s) > 10 and len(s) < 250:
                sentences.append(s.lower())

    for s in sentences:
        print(f"SENTENCE: {s}")
        frame_structures = get_frame_structures(s)
        print(json.dumps(frame_structures, ensure_ascii=False, indent=4, sort_keys=True))
        print()

if __name__ == "__main__":
    make_queries()