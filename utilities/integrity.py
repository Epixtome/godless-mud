import os
import logging

logger = logging.getLogger("GodlessMUD")

def check_file_structure():
    """
    Scans the project for architectural violations (Data Drift).
    Returns True if clean, False if issues found.
    """
    issues = []
    
    # Rule 1: No JSON in logic/ (Code Logic should not contain Data)
    for root, _, files in os.walk("logic"):
        if "__pycache__" in root: continue
        for file in files:
            if file.endswith(".json"):
                issues.append(f"Misplaced Data: {os.path.join(root, file)} (Should be in data/)")

    # Rule 2: No Python in data/ (Data should not contain Code)
    for root, _, files in os.walk("data"):
        for file in files:
            if file.endswith(".py"):
                issues.append(f"Misplaced Code: {os.path.join(root, file)} (Should be in logic/)")

    # Rule 3: Empty Files (Ghost files from bad moves)
    for root, _, files in os.walk("."):
        if "__pycache__" in root or ".git" in root or "logs" in root:
            continue
        for file in files:
            path = os.path.join(root, file)
            # Ignore __init__.py files as they are required for package structure even if empty
            if file == "__init__.py":
                continue
            if os.path.getsize(path) == 0:
                issues.append(f"Empty File: {path}")

    if issues:
        logger.warning("=== INTEGRITY CHECK FAILED ===")
        for issue in issues:
            logger.warning(f"  - {issue}")
        logger.warning("==============================")
        return False
    
    logger.info("Integrity check passed. File structure is clean.")
    return True