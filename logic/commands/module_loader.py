import os
import importlib
import logging

logger = logging.getLogger("GodlessMUD")

"""
Centralized module loader for Godless classes.
Shards the registration to keep skill_commands.py under the 300-line limit.
V5.3: Zero-Config Dynamic Discovery.
"""

def register_all_modules():
    """Main entry point to register all modules dynamically."""
    # 1. Core System Events (Infrastructure)
    try:
        from logic.core import quests as quest_engine
        quest_engine.register_events()
    except Exception as e:
        logger.error(f"Failed to register core quest events: {e}")

    # 2. Dynamic Discovery of Class & System Modules
    base_path = os.path.join("logic", "modules")
    if not os.path.exists(base_path):
        logger.warning(f"Module path {base_path} does not exist.")
        return

    # Files and folders to ignore (e.g. __init__.py, pycache, hidden files)
    IGNORE_PREFIXES = ["__", "."]

    for module_name in os.listdir(base_path):
        # Skip ignore-prefixed directories
        if any(module_name.startswith(p) for p in IGNORE_PREFIXES):
            continue
            
        module_dir = os.path.join(base_path, module_name)
        if not os.path.isdir(module_dir):
            continue

        # [V5.3 Standard] Scan EVERY .py file in the module directory
        # This makes the loader truly "Zero-Configuration"
        for f in os.listdir(module_dir):
            if f.endswith(".py") and not any(f.startswith(p) for p in IGNORE_PREFIXES):
                file_key = f[:-3] # Remove .py
                import_path = f"logic.modules.{module_name}.{file_key}"
                
                try:
                    mod = importlib.import_module(import_path)
                    
                    # Run standard registration hooks if they exist
                    # 'register_events' for listeners, 'initialize_module' for setup
                    for hook_name in ["register_events", "initialize_module"]:
                        hook = getattr(mod, hook_name, None)
                        if hook:
                            hook()
                            
                except Exception as e:
                    logger.error(f"Error loading module {import_path}: {e}")

    logger.info("Dynamic Module Scanning Complete (Zero-Config Mode).")
