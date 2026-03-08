import os
import re

def audit_repo(root_dir):
    findings = {
        "over_300_lines": [],
        "over_150_lines": [],
        "deep_imports": [],
        "isinstance_checks": [],
        "missing_init_facades": [],
        "class_logic_leaks": []
    }

    core_dirs = ["logic/core", "logic/engines"]
    module_dir = "logic/modules"
    
    for root, dirs, files in os.walk(root_dir):
        # Skip git, venv, data, etc.
        if any(skip in root for skip in [".git", "venv", "data", "__pycache__"]):
            continue
            
        for file in files:
            if not file.endswith(".py"):
                continue
                
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, root_dir)
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                line_count = len(lines)
                content = "".join(lines)
                
                # 1. Check Line Counts
                if line_count > 300:
                    findings["over_300_lines"].append(f"{rel_path} ({line_count} lines)")
                elif line_count > 150:
                    findings["over_150_lines"].append(f"{rel_path} ({line_count} lines)")
                
                # 2. Check for Deep Imports (Facade violation)
                # Matches: from x.y.z.w import ... (more than 3 levels if not relative)
                import_pattern = re.compile(r'^from (logic\.[a-z_]+\.[a-z_]+\.[a-z_]+)', re.MULTILINE)
                deep_imports = import_pattern.findall(content)
                if deep_imports:
                    findings["deep_imports"].append(f"{rel_path}: {list(set(deep_imports))}")
                
                # 3. Check for isinstance() checks (Clean Border violation)
                if "isinstance(" in content:
                    # Ignore if in validation or handlers, focus on logic/core/engines
                    if any(core in rel_path for core in core_dirs):
                        findings["isinstance_checks"].append(rel_path)
                
                # 4. Check for Class Logic Leaks in Core
                if "if player.active_class" in content or "if player.class" in content:
                    if any(core in rel_path for core in core_dirs):
                        findings["class_logic_leaks"].append(rel_path)

        # 5. Check for missing facades in __init__.py
        if "__init__.py" in files:
            init_path = os.path.join(root, "__init__.py")
            rel_init = os.path.relpath(init_path, root_dir)
            if os.path.getsize(init_path) == 0:
                # If it's a directory with logic, it should probably have a facade
                if "logic" in rel_init and not any(skip in rel_init for skip in ["tests", "migrations"]):
                    findings["missing_init_facades"].append(rel_init)

    return findings

if __name__ == "__main__":
    root = os.getcwd()
    results = audit_repo(root)
    
    print("# GEMINI.md Audit Report")
    print(f"\n## 1. Files Over 300 Lines (Critical Violation)")
    if results["over_300_lines"]:
        for f in results["over_300_lines"]: print(f"- {f}")
    else: print("- None")

    print(f"\n## 2. Deep Import Violations")
    if results["deep_imports"]:
        for f in results["deep_imports"]: print(f"- {f}")
    else: print("- None")

    print(f"\n## 3. isinstance() Checks in Logic/Core")
    if results["isinstance_checks"]:
        for f in results["isinstance_checks"]: print(f"- {f}")
    else: print("- None")

    print(f"\n## 4. Class Identity Leaks in Core")
    if results["class_logic_leaks"]:
        for f in results["class_logic_leaks"]: print(f"- {f}")
    else: print("- None")

    print(f"\n## 5. Potential Missing Init Facades")
    if results["missing_init_facades"]:
        for f in results["missing_init_facades"]: print(f"- {f}")
    else: print("- None")
