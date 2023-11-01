import glob
import json
import argparse
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

def get_sentence_stream(docs, k=20, language="english"):
    for _ in range(k):
        doc = random.choice(docs)
        with open(doc, encoding="utf-8") as f:
            lines = f.readlines()
        
        for _ in range(5):  # 5 tries to get a 'good' line
            line = random.choice(lines)
            if len(line) > 25:
                break
        line_sents = nltk.sent_tokenize(line, language=language)
        for s in line_sents:
            if len(s) > 10 and len(s) < 250:
                yield s, doc
                break

def try_make_frame_based_query(
        frame, frame_structure,
        deep_frame="Entity", deep_role="Entity", 
        process_role=False, ignore_trigger=False, 
        max_role_length=3, language="english"
    ):
    """
    Check if the frame structure meets frame_based certain requirements, clean it
    and check string requirements 
    """
    assert process_role or not ignore_trigger, "`ignore_trigger` can only be used if `process_role` is true"

    inherited_role = find_inherited_role(frame, deep_frame, deep_role)
    if inherited_role is None:
        return None, None
    
    # exclude some weird/uninteresting/undesirable frame / role combinations
    if deep_frame == "Entity" and inherited_role == "Event":
        return None, None
    
    if process_role and inherited_role not in frame_structure:
        return None, None
    trigger_cleaned = clean_texts(frame_structure["_TRIGGER"], language)
    if not trigger_cleaned:
        return None, None

    if not process_role:
        return trigger_cleaned, inherited_role

    role_cleaned = clean_texts(frame_structure[inherited_role], language)
    if not role_cleaned:
        return None, None

    if role_cleaned == trigger_cleaned:
        return None, None

    if len(role_cleaned.split()) > max_role_length:
        role_tokens = role_cleaned.split()
        role_capped = ""
        while len(role_capped.split()) < max_role_length:
            role_capped += " " + role_tokens.pop(0)
        if ignore_trigger:
            return role_capped.lstrip(), inherited_role
        return f"{trigger_cleaned} {role_capped.lstrip()}", inherited_role

    if ignore_trigger:
        return role_cleaned, inherited_role
    return f"{trigger_cleaned} {role_cleaned}", inherited_role

    

def make_queries(persona, language="english"):
    docs = glob.glob(f"../../../datasets/personas/personas_raw/{persona}/**/*.txt", recursive=True)

    out_file = f"../../../datasets/personas/personas_fn_queries/{persona}_query.json"

    queries = []

    entities = set()
    entities_with_attrib = set()
    places = set()

    place_relations = set()
    undergo_action = set()
    perform_action = set()

    def _thing_quotas_met():
        return len(entities) + len(entities_with_attrib) + len(places) >= 1000
    
    def _rel_quotas_met():
        return len(place_relations) + len(undergo_action) + len(perform_action) >= 1000

    def _append_query(qry, cat, snt, doc, frm, rols, fsx):
        queries.append({
            "query": qry,
            "_category": cat,
            "_txt_meta": {
                "sentence": snt,
                "document": doc
            },
            "_fn_meta": {
                "frame": frm,
                "roles": rols,
                "frame_structure": fsx
            }
        })

    sentence_stream = get_sentence_stream(docs, k=1_000_000, language=language)
    
    counter = 0
    while not (_thing_quotas_met() and _rel_quotas_met()):
        if counter % 10 == 0:
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(queries, f, ensure_ascii=False, indent=4, sort_keys=True)
        
        counter += 1
        
        sentence, document = next(sentence_stream)
        frame_structures = get_frame_structures(sentence.lower())
        print("\n" + sentence)

        for fs_id, fs in frame_structures.items():
            fs_id, frame = fs_id.split(".")

            # ---- searching for 'THINGS' ----
            if not _thing_quotas_met():
                # Places (Locale)
                place_query, _ = try_make_frame_based_query(frame, fs, "Locale", "Locale", language=language)
                if place_query:
                    places.add(place_query)
                    _append_query(place_query, "places", sentence, document, frame, [], fs)
                    print(f"[✔️] place query added ({frame}) -> new total {len(places)}")
                    print("\t", place_query, "\n")
                    continue                    

            if not _thing_quotas_met():
                # Entity (Entity)
                entity_query, _ = try_make_frame_based_query(frame, fs, "Entity", "Entity", language=language)
                if entity_query:
                    entities.add(entity_query)
                    _append_query(entity_query, "entities", sentence, document, frame, [], fs)
                    print(f"[✔️] entity query added ({frame}) -> new total {len(entities)}")
                    print("\t", entity_query, "\n")                    
                    continue

            if not _thing_quotas_met():
                # Entity with attribute
                attrib_query, attrib_role = try_make_frame_based_query(frame, fs, "Attributes", "Entity", process_role=True, language=language)
                if attrib_query:
                    entities_with_attrib.add(attrib_query)
                    _append_query(attrib_query, "entities_with_attrib", sentence, document, frame, [attrib_role], fs)
                    print(f"[✔️] entity with attribute added ({frame}, {attrib_role}) -> new total {len(entities_with_attrib)}")                    
                    print("\t", attrib_query, "\n")                    
                    continue

            # --- searching for 'RELATIONS' ---
            if not _rel_quotas_met():
                # Undergo an action (Transitive_action)
                u_action_query, undergoer_role = try_make_frame_based_query(frame, fs, "Transitive_action", "Patient", process_role=True, language=language)
                if u_action_query:
                    undergo_action.add(u_action_query)
                    _append_query(u_action_query, "undergo_action", sentence, document, frame, [undergoer_role], fs)
                    print(f"[✔️] undergoing action added ({frame}, {undergoer_role}) -> new total {len(undergo_action)}")                    
                    print("\t", u_action_query, "\n")                    
                    continue

            if not _rel_quotas_met():
                # Perform an action (Transitive_action)
                p_action_query, agent_role = try_make_frame_based_query(frame, fs, "Transitive_action", "Agent", process_role=True, language=language)
                if p_action_query:
                    perform_action.add(p_action_query)
                    _append_query(p_action_query, "perform_action", sentence, document, frame, [agent_role], fs)
                    print(f"[✔️] performing action added ({frame}, {agent_role}) -> new total {len(perform_action)}")                    
                    print("\t", p_action_query, "\n")                    
                    continue

            if not _rel_quotas_met():
                # Perform an action (Intentionally_act)
                p_action_query, agent_role = try_make_frame_based_query(frame, fs, "Intentionally_act", "Agent", process_role=True, language=language)
                if p_action_query:
                    perform_action.add(p_action_query)
                    _append_query(p_action_query, "perform_action", sentence, document, frame, [agent_role], fs)
                    print(f"[✔️] performing action added ({frame}, {agent_role}) -> new total {len(perform_action)}")                    
                    print("\t", p_action_query, "\n")                    
                    continue

            if not _rel_quotas_met():
                # Place relationships
                loc_rel_figure, figure_role = try_make_frame_based_query(frame, fs, "Locative_relation", "Figure", process_role=True, ignore_trigger=True, language=language)
                loc_rel_ground, ground_role = try_make_frame_based_query(frame, fs, "Locative_relation", "Ground", process_role=True, ignore_trigger=True, language=language)            
                if loc_rel_figure and loc_rel_ground:
                    query_str = " ".join(f"{loc_rel_figure} {loc_rel_ground}".split())
                    place_relations.add(query_str)
                    _append_query(query_str, "place_relations", sentence, document, frame, [figure_role, ground_role], fs)
                    print(f"[✔️] place relationship added ({frame}, {figure_role}, {ground_role}) -> new total {len(place_relations)}")                    
                    print("\t", f"{loc_rel_figure} {loc_rel_ground}", "\n")                    
                    continue

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(queries, f, ensure_ascii=False, indent=4, sort_keys=True)
        

    print("==================")
    # entities = set()
    # entities_with_attrib = set()
    # places = set()

    # place_relations = set()
    # undergo_action = set()
    # perform_action = set()
    print("Entity:\n\t" + "\n\t".join(entities))
    print("Entities with attributes:\n\t" + "\n\t".join(entities_with_attrib))
    print("Places:\n\t" + "\n\t".join(places))
    
    print("Place relations:\n\t" + "\n\t".join(place_relations))
    print("Undergoing actions:\n\t" + "\n\t".join(undergo_action))
    print("Performing actions:\n\t" + "\n\t".join(perform_action))


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
    docs = glob.glob("../../../datasets/personas/personas_raw/multiling_news_fr_sample4000/*.txt")
    # docs = glob.glob("../../../datasets/personas/personas_raw/multiling_recipes_fr_sample400/*.txt")

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

    ap = argparse.ArgumentParser()
    ap.add_argument("--persona", default="1_accountant")
    ap.add_argument("--language", default="english")

    args = ap.parse_args()
    make_queries(args.persona, args.language)