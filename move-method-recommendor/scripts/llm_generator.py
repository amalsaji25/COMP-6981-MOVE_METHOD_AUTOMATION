import subprocess
import os
import sys
import json

def get_java_files(java_dir: str):
    for root, _, files in os.walk(java_dir):
        for file in files:
            if file.endswith(".java"):
                yield os.path.join(root, file)

def read_java_file(java_file_path: str) -> str:
    with open(java_file_path, 'r', encoding="utf-8") as file:
        return file.read()
    
def run_ast_generator(java_file_path: str) -> dict:

    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    cmd = ["java",
           "-cp",
           f"{root}/test_out:{root}/libs/gson-2.10.1.jar:{root}/libs/javaparser-core-3.25.4.jar",
           "scripts.GenerateAST",
           java_file_path
           ]
    
    java_process = subprocess.run(cmd, capture_output=True, text=True)
    
    if java_process.returncode != 0:
        print(f"[AST Error] {java_file_path}:\n {java_process.stderr}", file=sys.stderr)
        return {}
    return json.loads(java_process.stdout)

def get_summary_with_ollama(llm_model_name: str, llm_prompt: str) -> str:

    cmd = ["ollama", "run", llm_model_name]

    llm_process = subprocess.run(cmd, input=llm_prompt.encode("utf-8"), capture_output=True, check = True)

    return llm_process.stdout.decode("utf-8").strip()


def get_class_summary(llm_model_name: str, pkg_name: str, cls_name: str, methods_meta: list, code: str) -> dict:
    methods = ""
    method_calls = set()
    used_classes = set()
    cls_fields = methods_meta[0].get("classFields", []) if methods_meta else []

    fields = ""
    for f in cls_fields:
        fields += f"  - `{f['var_type']} {f['var_name']}`\n"
        used_classes.add(f['var_type'])

    for method in methods_meta:
        method_name = method.get('name', '')
        params = method.get('parameters', [])
        return_type = method.get('returnType', 'void')
        param_str = ", ".join(params)
        methods += f"- `{return_type} {method_name}({param_str})`\n"

        for call in method.get('methodCalls', []):
            if "." in call:
                prefix = call.split(".")[0]
                used_classes.add(prefix)  #  the prefix is an object of another class

        for param in params:
            used_classes.add(param)

    # Construct LLM prompt
    llm_prompt = f"""
                    ### PACKAGE ###
                    {pkg_name}

                    ### CLASS & METHODS AST INFO ###
                    Class: {cls_name}

                    **Fields:**
                    {fields or ' - None'}

                    **Methods:**
                    {methods or ' - None'}

                    ### CODE ###
                    {code}

                    ### INSTRUCTIONS ###
                    You are summarizing the Java class `{cls_name}` based on its actual code and structure.

                    Include the following in your summary:

                    - What data it owns (fields)
                    - What services/methods it offers (just summarize intent)
                    - What external classes it **uses** (e.g., in parameters, method calls, or field types)

                    ### RULES ###
                    - Mention only those classes visible in the AST or code — do NOT assume anything.
                    - If the class depends on another class, say clearly: "uses class X".
                    - Do NOT describe how the result is delivered (e.g., email/SMS) unless it's in the code.
                    - Avoid phrases like "this class contains..." or "this class is responsible for...".
                    - No method chains or imaginary behavior. Stick to what's in the code.

                    Output a clear, human-readable English summary. Avoid code formatting.
                    """.strip()

    # LLM response (summary text)
    summary_text = get_summary_with_ollama(llm_model_name, llm_prompt)

    return {
        "summary": summary_text.strip(),
        "uses_classes": sorted(used_classes - {cls_name})  
    }

def get_method_summary(llm_model_name: str, pkg_name: str, class_summary:str, method: dict, code: str) -> str:
    method_name = method.get("name", "")
    param_list = ", ".join(method.get("parameters", []))
    return_type = method.get("returnType", "void")
    method_calls = "\n".join(f" Call: {func_calls}" for func_calls in method.get("methodCalls", []))
    field_accesses = "\n".join(f"  FieldAccess: {f}" for f in method.get("methodFieldAccess", []))
    local_vars = "\n".join(f"  Var: {v['var_name']}->{v['var_type']}" for v in method.get("methodLocalVariables", []))

    method_body = method.get("methodBody", "")

    llm_prompt = f"""
                    ### PACKAGE ###
                    {pkg_name}

                    ### METHOD AST INFO ###
                    Method: {method_name}({param_list}) -> {return_type}

                    Field Accesses:
                    {field_accesses or ' - None'}

                    Method Calls:
                    {method_calls or ' - None'}

                    Local Variables:
                    {local_vars or ' - None'}

                    ### METHOD CODE ###
                    {method_body}

                    ### INSTRUCTIONS ###
                    In 1 sentence (≤ 30 words), describe what the method `{method_name}` does.

                    ### RULES ###
                    - Start with a verb (e.g., Sends, Validates, Logs).
                    - Mention if it **uses** other classes (e.g., “uses class X”), but do **not** write full method chains or speculative behavior.
                    - Do **not** refer to any behavior or class not visible in the AST.
                    - Be strictly literal and grounded in the data above.
                    - Focus on clarity, not speculation.

                    Output format: A single sentence starting with a verb.
                """.strip()
    
    return get_summary_with_ollama(llm_model_name, llm_prompt)

if __name__ == "__main__":

    # Define the llm model used for summarization of java code + ast
    llm_model_name = "codellama:13b"

    # Specify the directory containing the java codes to be refactored
    java_dir = input("Enter path to folder containing Java files: ").strip()
    if not os.path.isdir(java_dir):
        print(f"Not a valid directory: {java_dir}",file=sys.stderr)
        sys.exit(1)

    summaries = {}

    for java_file in get_java_files(java_dir):
        code = read_java_file(java_file)
        ast = run_ast_generator(java_file)

        print(ast)

        if not ast:
            continue

        package_name = ast.get("package","")
        classes = ast.get("classes", [])

        for cls in classes:
            cls_name = cls.get("class", "UnknownClass")
            methods_meta = cls.get("methods", [])

            class_summary_dict = get_class_summary(llm_model_name, package_name, cls_name, methods_meta, code)
            print(f"Class {cls_name}: {class_summary_dict['summary']}")

            summaries[cls_name] = {
                "summary" : class_summary_dict["summary"],
                "uses_classes": class_summary_dict["uses_classes"],
                "package" : package_name,
                "classBody":code,
                "classFields"  : cls.get("classFields", []),
                "methods": {},
                "methods_meta": []
            }

            for method in methods_meta:
                method_summary = get_method_summary(llm_model_name, package_name, class_summary_dict["summary"], method, code)
                print(f" \u21b3 {method['name']}: {method_summary}")

                summaries[cls_name]["methods"][method['name']] = method_summary
                summaries[cls_name]["methods_meta"].append({
                    "name": method.get("name", ""),
                    "parameters": method.get("parameters", []),
                    "methodCalls": method.get("methodCalls", []),
                    "methodFieldAccess": method.get("methodFieldAccess", []),
                    "classFields"  : cls.get("classFields", []),
                    "methodBody": method.get("methodBody", "")
                })                

        print("-" * 60)

    with open("llm_code_summaries.json","w", encoding="utf-8") as out:
        json.dump(summaries, out, indent=2, ensure_ascii=False)
    print("Saved all java code summaries to llm_code_summaries.json")