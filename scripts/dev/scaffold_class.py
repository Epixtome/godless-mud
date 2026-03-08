import os
import sys
import json
import argparse

def scaffold_class(class_id, kingdom, description, recipe_str):
    class_id = class_id.lower()
    kingdom = kingdom.lower()
    
    # 1. Parse Recipe
    recipe = {}
    if recipe_str:
        for pair in recipe_str.split(','):
            key, val = pair.split(':')
            recipe[key.strip()] = int(val.strip())

    # 2. Define Paths
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    module_dir = os.path.join(base_dir, "logic", "modules", class_id)
    data_file = os.path.join(base_dir, "data", "classes", f"{kingdom}.json")
    loader_file = os.path.join(base_dir, "logic", "commands", "module_loader.py")

    print(f"--- Scaffolding Class: {class_id.capitalize()} ({kingdom}) ---")

    # 3. Create Files
    if not os.path.exists(module_dir):
        os.makedirs(module_dir)

    # __init__.py
    with open(os.path.join(module_dir, "__init__.py"), "w") as f:
        f.write(f"from . import events, actions, state\n")

    # state.py
    with open(os.path.join(module_dir, "state.py"), "w") as f:
        f.write(f"""def initialize_{class_id}(player):
    \"\"\"Initializes {class_id.capitalize()} specific state within player.ext_state.\"\"\"
    if "{class_id}" not in player.ext_state:
        player.ext_state["{class_id}"] = {{
            "version": 1.0,
            "modifiers": []
        }}
""")

    # events.py
    with open(os.path.join(module_dir, "events.py"), "w") as f:
        f.write(f"""from logic.core import event_engine
import utilities.telemetry as telemetry

def register_events():
    \"\"\"Subscribes {class_id.capitalize()} hooks to the event engine.\"\"\"
    # event_engine.subscribe("on_combat_tick", handle_{class_id}_heartbeat)
    pass

def handle_{class_id}_heartbeat(player):
    if getattr(player, 'active_class', None) != '{class_id}':
        return
    # Implement logic here
    pass

# Auto-register on import
register_events()
""")

    # actions.py
    with open(os.path.join(module_dir, "actions.py"), "w") as f:
        f.write(f"""from logic.actions.registry import register
import utilities.telemetry as telemetry

# Example Skill
@register("skill_name")
async def do_example_skill(player, skill, args):
    if getattr(player, 'active_class', None) != '{class_id}':
        return None, True
        
    return None, True
""")

    # 4. Update Data
    if os.path.exists(data_file):
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        data[class_id] = {
            "id": class_id,
            "name": class_id.capitalize(),
            "description": description,
            "kingdom": kingdom.capitalize(),
            "recipe": recipe,
            "engine_passive": {
                "name": f"Master of {class_id.capitalize()}",
                "description": f"Standard passive for {class_id.capitalize()}."
            }
        }
        
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        print(f"Updated data/classes/{kingdom}.json")
    else:
        print(f"Warning: Data file {data_file} not found. Skipping data update.")

    # 5. Update Loader
    if os.path.exists(loader_file):
        with open(loader_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Decide which section to add to based on kingdom
        # This is a bit heuristic but better than nothing
        target_func = "_register_common_modules"
        if kingdom == "light": target_func = "_register_divine_modules"
        elif kingdom == "dark": target_func = "_register_arcane_modules"
        elif kingdom in ["instinct", "martial"]: target_func = "_register_martial_modules"
        elif kingdom == "hybrid": target_func = "_register_hybrid_modules"

        new_lines = []
        found_func = False
        import_added = False
        
        for line in lines:
            new_lines.append(line)
            if f"def {target_func}():" in line:
                found_func = True
            
            if found_func and not import_added and line.strip() == "":
                # Insert at the end of the block (before the next function or empty line sequence)
                new_import = f"    from logic.modules.{class_id} import events as {class_id}_ev\n"
                # Check if already exists
                if new_import not in lines:
                    new_lines.insert(-1, new_import)
                    import_added = True
                    found_func = False # Stop looking

        with open(loader_file, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print(f"Registered {class_id} in module_loader.py")

    print(f"SUCCESS: {class_id.capitalize()} scaffolded at logic/modules/{class_id}/")
    print(f"\n{'='*60}")
    print(f" MANDATORY POST-SCAFFOLD AUDIT:")
    print(f"{'='*60}")
    print(f" 1. DATA AUDIT: Check data/blessings/{class_id}.json and ensure")
    print(f"    'base_power' and 'scaling' are set. Defaults are weak!")
    print(f" 2. LOGIC AUDIT: Run the simulation to verify the class is functional:")
    print(f"    python scripts/dev/combat_sim.py {class_id} barbarian")
    print(f"{'='*60}\n")
    parser = argparse.ArgumentParser(description="Scaffold a new class for Godless MUD.")
    parser.add_argument("class_id", help="The machine ID of the class (e.g. samurai)")
    parser.add_argument("kingdom", help="The kingdom (light, dark, instinct, hybrid)")
    parser.add_argument("--description", default="A new mysterious class.", help="A short description.")
    parser.add_argument("--recipe", default="", help="Resonance recipe (e.g. 'martial:5,speed:2')")

    args = parser.parse_args()
    scaffold_class(args.class_id, args.kingdom, args.description, args.recipe)
