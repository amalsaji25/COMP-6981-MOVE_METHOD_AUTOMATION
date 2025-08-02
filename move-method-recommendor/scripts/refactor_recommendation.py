import json, os, re, sys
import numpy as np
from collections import defaultdict
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from tabulate import tabulate
from transformers import AutoTokenizer, AutoModel
import torch


"""
    Load and preprocess LLM-generated summaries for classes and methods.

    Returns two structures:
       - `classes`: mapping (class names) → { summary, package, body }
       - `methods`: mapping (class_name, method_name) → { summary, …metadata }
"""
def load_llm_summaries(path="llm_code_summaries.json"):
    with open(path, encoding="utf-8") as file:
        data = json.load(file)

        classes, methods = {}, defaultdict(dict)
        
        # First pass: build cleaned summaries for classes and methods
        for class_name, class_data in data.items():
            classes[class_name] = {
                "summary": summary_preprocessor(class_data["summary"]),
                "package": class_data.get("package",""),
                "classBody":class_data.get("classBody",""),
                "classFields":class_data.get("classFields",[])
            }
            
            for method_name, method_summary in class_data["methods"].items():
                methods[(class_name,method_name)]["summary"] = summary_preprocessor(method_summary)

        # Second pass: attach additional method metadata from “methods_meta”
        for class_name, class_data in data.items():
            for method_info in class_data.get("methods_meta",[]):
                key = (class_name,method_info["name"])
                methods[key].update(method_info)

        return classes, methods

def summary_preprocessor(summary: str) -> str:
    """
    Remove out common boilerplate phrases and generic terms from a code summary to reduce noise before embedding.
    helps to focus the model on meaningful content by removing patterns like “in the X system”, “method”, “class”, etc
    """
    FILLERS = [
        r"\bin (the)?[\w\s]+ system\b",
        r"\b(in|within) a[n]? [\w\s]+ platform\b",
        r"\bmethod\b",
        r"\bclass\b",       
    ]

    for pattern in FILLERS:
        summary = re.sub(pattern, "", summary, flags=re.I)
    return " ".join(summary.split())

def encode_codebert(code, tokenizer, model):
    """
        Generate vector representations for code snippets: 1. Tokenize the code. 2. Running through CodeBERT without gradients (just encoding not training).
        3. Extracte the [CLS] token embedding. 4. Return as a NumPy array.
    """
    tokens = tokenizer(code, padding=True, truncation=True, return_tensors="pt")
    with torch.no_grad():
        outputs = model(**tokens)
    return outputs.last_hidden_state[:, 0, :].cpu().numpy()   

def is_interface(class_body: str) -> bool:
    """
        if the code is part of a java interface then return true (no move method for it as it is just a contract)
    """
    lines = class_body.splitlines()
    for line in lines:
        if line.strip():
            if re.search(r'\binterface\b', line, re.IGNORECASE):
                return True
            break
    return False  

def is_simple_delegate(method_meta):
    """
     return True if the method is a one-line delegate (ie. a method having a single return or assignment statement)
    """
    if not method_meta:
        return False
    body = method_meta.get("methodBody","")
    lines = [line.strip() for line in body.splitlines() if line.strip()]
    return len(lines) == 1 and ("return" in lines[0] or "=" in lines[0] and ";" in lines[0])

def is_getter_setter(method_meta, method_name):
    """
     Checks if a method is a simple getter or setter with only one line of code.
    """
    GETTER_SETTER_PATTERN = re.compile(r"^(get|set|is)[A-Z].*")

    if not GETTER_SETTER_PATTERN.match(method_name):
        return False
    body = method_meta.get("methodBody","")
    lines = [line.strip() for line in body.splitlines() if line.strip()]
    return len(lines) == 1 and ("return" in lines[0] or "=" in lines[0])

def structural_candidates(method_meta, all_classes):
    """
    Identifies candidate classes that are structurally related to the given method.
    It uses:
    - Parameter types
    - Method call targets
    - Field access targets

    If none are matched, returns all classes.
    """
    if not method_meta:
        return list(all_classes)
    
    possible_candidate_class_filters = set()

    # 1. Add parameter types directly
    possible_candidate_class_filters.update(method_meta.get("parameters", []))

    # 2. Extract prefixes of method calls like 'notifier.send()' -> 'notifier'
    method_call_targets = {
        method_call.split(".")[0]
        for method_call in method_meta.get("methodCalls", [])
        if "." in method_call
    }

    # 3. Extract prefixes of field accesses like 'discount.value' -> 'discount'
    field_access_targets = {
        field_access.split(".")[0]
        for field_access in method_meta.get("methodFieldAccess", [])
        if "." in field_access
    }

    # 4. Get declared fields from the class context (injected from AST pre-processing)
    class_fields = method_meta.get("classFields", [])  # List of dicts: {var_name, var_type}
    field_name_to_type = {
        field["var_name"]: field["var_type"]
        for field in class_fields
    }

    # 5. Map object names (from calls/fields) to their actual types if known
    for obj_name in method_call_targets | field_access_targets:
        if obj_name in field_name_to_type:
            possible_candidate_class_filters.add(field_name_to_type[obj_name])

    # 6. Match filters to actual class names
    candidate_classes = []
    for class_name in all_classes:
        for possible_type_filter in possible_candidate_class_filters:
            if possible_type_filter in class_name:
                candidate_classes.append(class_name)
                break  # Avoid duplicates

    # 7. Return the filtered candidates, or fallback to all
    return candidate_classes or list(all_classes)
#    return list(all_classes)

def same_package_bonus(source_class_package:str, candidate_class_package:str) -> float:
    """
    Return a bonus if both classes belong to the same package.
    """
    SAME_PKG_BONUS     = 0.10
    return SAME_PKG_BONUS if source_class_package == candidate_class_package and source_class_package else 0.0

def field_bonus(method_metadata, candiate_class):
    """
     Return a bonus if the method accesses any field that belongs to the target candidate class.
    """
    FIELD_ACCESS_BONUS = 0.10

    if not method_meta:
        return 0.0
    
    field_accesses = method_metadata.get("methodFieldAccess")
    class_fields = method_metadata.get("classFields", [])

    # Map object name to its type
    object_type_map = {field["var_name"]: field["var_type"] for field in class_fields}

    for field_access in field_accesses:
        if "." in field_access:
            object_name = field_access.split(".")[0]
            if object_type_map.get(object_name) == candiate_class:
                return FIELD_ACCESS_BONUS
    return 0.0

def cohesion_bonus(method_metadata, candiate_class):
    """
     Return a bonus based on how much a method interact with a particular candidate class
    """

    if not method_meta:
        return 0.0
    
    # Check if the method invokes the setter methods of the candidate class
    class_fields = method_metadata.get("classFields", [])
    field_type_map = {field["var_name"]: field["var_type"] for field in class_fields}

    write_calls = 0
    read_calls = 0

    for field_access in method_metadata.get("fieldAccesses", []):
        if "." in field_access:
            object_name, access_type = field_access.split(".", 1)
            object_type = field_type_map.get(object_name)
            if object_type == candiate_class:
                if re.match(r"^set[A-Z].*", access_type):
                    write_calls += 1
                elif re.match(r"^get[A-Z].*", access_type):
                    read_calls += 1

    external_calls = 0
    for call in method_metadata.get("methodCalls", []):
        if "." in call:
            object_name, _ = call.split(".", 1)
            object_type = field_type_map.get(object_name)
            if object_type == candiate_class:
                external_calls += 1

    bonus = (0.05 * write_calls) + (0.01 * read_calls) + (0.05 * external_calls)
    return bonus

def extract_method_used_classes(method_meta, class_field_map):
    """
    Returns a set of class names/types that the method depends on, based on:
    - parameters
    - method calls on known field objects
    - field accesses on known field objects
    """
    used_classes = set()

    # Use parameter types directly
    used_classes.update(method_meta.get("parameters", []))

    # Map field names → types
    field_type_map = {f["var_name"]: f["var_type"] for f in class_field_map}

    # methodCalls like: objectName.methodCall
    for call in method_meta.get("methodCalls", []):
        if "." in call:
            object_name = call.split(".")[0]
            class_type = field_type_map.get(object_name)
            if class_type:
                used_classes.add(class_type)

    # methodFieldAccess like: objectName.fieldAccess
    for access in method_meta.get("methodFieldAccess", []):
        if "." in access:
            object_name = access.split(".")[0]
            class_type = field_type_map.get(object_name)
            if class_type:
                used_classes.add(class_type)

    return used_classes

if __name__ == "__main__":
    
    if not os.path.exists("llm_code_summaries.json"):
        sys.exit("llm_code_summaries.json not found. Run llm_generator.py first")
    
    classes, methods = load_llm_summaries()
    print(f"Loaded {len(classes)} classes, {len(methods)} methods")

    print("Embedding summaries and code ...")

    # Load class/method summary and transform it into a fixed length embedding vector
    summary_embedder = SentenceTransformer("all-MiniLM-L6-v2")

    # Intialize tokenizer to split the source code into subword tokens
    code_tokenizer = AutoTokenizer.from_pretrained("microsoft/codebert-base")

    # Load pretrained tranformer encoder and pass tokenized code to prodice embeddings
    code_model = AutoModel.from_pretrained("microsoft/codebert-base")

    class_vectors = {}
    for cls, info in classes.items():
        summary_vector = summary_embedder.encode(info["summary"])
        code_vector = encode_codebert([info.get("classBody")], code_tokenizer, code_model)[0]
        class_vectors[cls] = {
                                "summary_vec": summary_vector,
                                "code_vec": code_vector[:384]
                            }


    method_vectors = {}
    for (cls, method_name), info in methods.items():
        summary_vector = summary_embedder.encode(info["summary"])
        code_vector = encode_codebert([info.get("methodBody", "")], code_tokenizer, code_model)[0]
        method_vectors[(cls, method_name)] = {
                                                "summary_vec": summary_vector,
                                                "code_vec": code_vector[:384]
                                            }

    interface_classes = set()

    for class_name, info in classes.items():
        class_body = info.get("classBody", "")
        if is_interface(class_body):
            interface_classes.add(class_name)

    if len(interface_classes) != 0 :
        print(f'Interfaces found : {interface_classes}')

    recommendations = []

    for (cls_name, method_name), method_vector in method_vectors.items():
        method_meta = methods[(cls_name, method_name)]
        source_package = classes[cls_name]["package"]

        if cls_name in interface_classes:
            action = "KEEP (inteface)"
        elif is_simple_delegate(method_meta):
            action = "KEEP (simple delegate)"
        elif is_getter_setter(method_meta, method_name):
            action = "KEEP (getter/setter)"
        
        # Core logic to decide whether to keep, move, or extract a method based on its similarity and structural fit with other classes
        else:
            # first let the current class itself be the methods best class with a dummy score
            best_cls, best_score = cls_name, -1.0
            MOVE_THRESHOLD     = 0.60
            EXTRACT_THRESHOLD  = 0.50

            for candiate_class in structural_candidates(method_meta, classes):
                # Compute semantic similarity between the method and candidate class using vector embeddings
                summary_sim = cosine_similarity(
                                                    [method_vector["summary_vec"]],
                                                    [class_vectors[candiate_class]["summary_vec"]]
                                                )[0][0]

                code_sim = cosine_similarity(
                                                [method_vector["code_vec"]],
                                                [class_vectors[candiate_class]["code_vec"]]
                                            )[0][0]

                base_score = 0.5 * summary_sim + 0.5 * code_sim

                # Add bonus points if the method is closely related to the candidate class (same package, uses its fields, or has similar logic)
                package_bonus_score = same_package_bonus(source_package, classes[candiate_class]["package"])
                field_bonus_score = field_bonus(method_meta, candiate_class)
                cohesion_bonus_score = cohesion_bonus(method_meta, candiate_class)

                # bonus if the class is used by the method's current class
                method_used_classes = extract_method_used_classes(method_meta, classes[cls_name].get("classFields", []))
                use_class_bonus_score = 0.05 if candiate_class in method_used_classes else 0.0

                bonus_score = package_bonus_score + field_bonus_score + cohesion_bonus_score + use_class_bonus_score

                candidate_score = (0.8 * base_score) + bonus_score
#                candidate_score = base_score
                print(f"[{method_name}] {cls_name} → {candiate_class} | summary: {summary_sim:.4f}, code: {code_sim:.4f}, "
                f"package: {package_bonus_score:.3f}, field: {field_bonus_score:.3f}, cohesion: {cohesion_bonus_score:.3f}, uses: {use_class_bonus_score:.3f} "
                f"→ final: {candidate_score:.4f}")

                if candidate_score > best_score:
                    best_cls, best_score = candiate_class, candidate_score
    
            if best_cls == cls_name:
                action = "KEEP"
            elif best_score >= MOVE_THRESHOLD:
                action = f"MOVE to {best_cls}"
            elif best_score < EXTRACT_THRESHOLD:
                action = "EXTRACT to new class"

        recommendation_score = 1.0 if action.startswith("KEEP") else float(round(best_score, 3))
        recommendations.append({
            "method":        method_name,
            "current_class": cls_name,
            "best_class":    cls_name if action.startswith("KEEP") else best_cls,
            "score":         recommendation_score,
            "action":        action
        })

    print(tabulate(
        [(r["method"], r["current_class"], r["action"], r["score"]) for r in recommendations],
        headers=["Method", "Current", "Action", "Score"],
        tablefmt="github"
    ))

    with open("recactor_recommendations.json", "w", encoding="utf-8") as file_out:
        json.dump(recommendations, file_out, indent=2, ensure_ascii=False)
    print("\nRecommendations written to recommendations.json")