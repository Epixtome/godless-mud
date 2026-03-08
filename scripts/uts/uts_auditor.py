import json
import glob
import os
import sys

# --- CONFIGURATION ---
CLASS_DIR = "data/classes"
BLESSING_DIR = "data/blessings"
ITEM_DIR = "data/items"
REPORT_FILE = "godless_audit_report.txt"

class SnapSimulator:
    def __init__(self, class_dir, blessing_dir, item_dir):
        self.classes = self._load_classes(class_dir)
        self.blessings = self._load_blessings(blessing_dir)
        self.items = self._load_items(item_dir)
        self.report_lines = []

    def _load_classes(self, directory):
        loaded = {}
        # Recursive search for JSON files
        files = glob.glob(os.path.join(directory, "**", "*.json"), recursive=True)
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Handle "classes" wrapper (matches loader.py logic)
                    if 'classes' in data and isinstance(data['classes'], dict):
                        source = data['classes']
                    elif isinstance(data, dict):
                        source = data
                    else:
                        continue

                    # Filter out non-class keys if mixed
                    for k, v in source.items():
                        if isinstance(v, dict) and 'recipe' in v:
                            loaded[k] = v
                            
            except Exception as e:
                print(f"Error loading class file {file_path}: {e}")
        return loaded

    def _load_blessings(self, directory):
        loaded = {}
        files = glob.glob(os.path.join(directory, "**", "*.json"), recursive=True)
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Handle "blessings" wrapper (matches loader.py logic)
                    if 'blessings' in data and isinstance(data['blessings'], dict):
                        source = data['blessings']
                    elif isinstance(data, dict):
                        source = data
                    else:
                        continue

                    for k, v in source.items():
                        if isinstance(v, dict) and 'identity_tags' in v:
                            loaded[k] = v
                            
            except Exception as e:
                print(f"Error loading blessing file {file_path}: {e}")
        return loaded

    def _load_items(self, directory):
        loaded = {'weapon': [], 'armor': [], 'accessory': []}
        files = glob.glob(os.path.join(directory, "*.json"))
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    items_list = data.get('items', []) if isinstance(data, dict) else []
                    
                    for item in items_list:
                        i_type = item.get('type', 'item')
                        
                        # Resolve Tags (UTS 2.0 gear_tags > Legacy tags dict)
                        tags = item.get('gear_tags', [])
                        if not tags and 'tags' in item and isinstance(item['tags'], dict):
                            tags = list(item['tags'].keys())
                        
                        if not tags: continue

                        entry = {'id': item.get('id'), 'name': item.get('name', 'Unknown'), 'tags': tags}

                        if i_type == 'weapon':
                            loaded['weapon'].append(entry)
                        elif i_type == 'armor':
                            loaded['armor'].append(entry)
                        else:
                            loaded['accessory'].append(entry)
            except Exception as e:
                print(f"Error loading item file {file_path}: {e}")
        return loaded

    def log(self, message):
        print(message)
        self.report_lines.append(message)

    def audit_deck(self, blessing_ids, gear_tags=None):
        """Simulates the Identity Auditor. Returns list of snapped Class Names."""
        gtc = {}
        
        # 0. Apply Gear Tags (Static Voltage)
        if gear_tags:
            for tag, count in gear_tags.items():
                gtc[tag] = gtc.get(tag, 0) + count

        # 1. Calculate GTC (Global Tag Count)
        for b_id in blessing_ids:
            blessing = self.blessings.get(b_id)
            if blessing:
                for tag in blessing.get('identity_tags', []):
                    gtc[tag] = gtc.get(tag, 0) + 1
        
        # 2. Check Recipes
        snapped = []
        for c_id, c_data in self.classes.items():
            recipe = c_data.get('recipe', {})
            if not recipe: continue 
            
            if all(gtc.get(tag, 0) >= count for tag, count in recipe.items()):
                snapped.append(c_data.get('name', c_id))
        return snapped

    def run_collision_test(self, target_class, deck, gear_tags=None):
        """Checks if a deck snaps other classes."""
        snapped = self.audit_deck(deck, gear_tags)
        collisions = [c for c in snapped if c != target_class]
        return collisions

    def find_best_gear_loadout(self, recipe):
        """Selects best 1 Weapon, 1 Armor, 2 Accessories for the recipe."""
        selected_gear = []
        combined_tags = {}

        def calculate_score(item):
            return sum(1 for t in item['tags'] if t in recipe)

        # 1. Best Weapon
        best_weapon = max(self.items['weapon'], key=calculate_score, default=None)
        if best_weapon and calculate_score(best_weapon) > 0:
            selected_gear.append(best_weapon)

        # 2. Best Armor
        best_armor = max(self.items['armor'], key=calculate_score, default=None)
        if best_armor and calculate_score(best_armor) > 0:
            selected_gear.append(best_armor)

        # 3. Best 2 Accessories
        relevant_accs = [acc for acc in self.items['accessory'] if calculate_score(acc) > 0]
        relevant_accs.sort(key=calculate_score, reverse=True)
        selected_gear.extend(relevant_accs[:2])

        # Aggregate Tags
        gear_names = []
        for item in selected_gear:
            gear_names.append(item['name'])
            for t in item['tags']:
                combined_tags[t] = combined_tags.get(t, 0) + 1
        
        return combined_tags, gear_names

    def run_bridge_efficiency_test(self, recipe):
        """Analyzes availability of Bridge Blessings."""
        if len(recipe) < 2:
            return "N/A (Single Tag)"
            
        relevant_blessings = 0
        bridge_blessings = 0
        required_tags = set(recipe.keys())
        
        for b_data in self.blessings.values():
            b_tags = set(b_data.get('identity_tags', []))
            matches = b_tags.intersection(required_tags)
            if matches:
                relevant_blessings += 1
                if len(matches) >= 2:
                    bridge_blessings += 1
                    
        if relevant_blessings == 0: return "No relevant blessings"
        ratio = (bridge_blessings / relevant_blessings) * 100
        return f"{bridge_blessings}/{relevant_blessings} ({ratio:.1f}%)"

    def _find_best_deck_dynamic(self, target_class, recipe, kingdom_affinity=None, gear_tags=None):
        """
        Dynamic Greedy Algorithm to find the most efficient deck.
        Prioritizes:
        1. Blessings that satisfy multiple UNMET requirements (Bridges).
        2. Blessings matching the Class Kingdom (Affinity).
        """
        deck = []
        current_tags = {}
        
        # Initialize with gear tags
        if gear_tags:
            for t, c in gear_tags.items():
                current_tags[t] = current_tags.get(t, 0) + c
                
        # Helper to check if snapped
        def check_snapped(tags):
            return all(tags.get(t, 0) >= req for t, req in recipe.items())

        if check_snapped(current_tags):
            return deck, True

        # Filter pool to relevant blessings only
        pool = []
        for b_id, b_data in self.blessings.items():
            if any(t in recipe for t in b_data.get('identity_tags', [])):
                pool.append(b_id)

        # Iterative selection (Max 15 slots to prevent infinite loops)
        for _ in range(15):
            best_candidate = None
            # Score: (useful_tags_count, is_kingdom_match)
            best_score = (-1, -1)

            # Calculate unmet needs
            unmet = {t: max(0, r - current_tags.get(t, 0)) for t, r in recipe.items()}
            unmet = {t: v for t, v in unmet.items() if v > 0}
            
            if not unmet:
                return deck, True

            for b_id in pool:
                if b_id in deck: continue
                
                b_data = self.blessings[b_id]
                b_tags = b_data.get('identity_tags', [])
                
                # 1. Weighted Tag Search: Count useful tags for UNMET requirements
                useful = sum(1 for t in b_tags if t in unmet)
                
                if useful == 0: continue
                
                # 2. Kingdom Affinity
                is_kingdom = 0
                if kingdom_affinity and kingdom_affinity in b_tags:
                    is_kingdom = 1
                
                score = (useful, is_kingdom)
                
                if score > best_score:
                    best_score = score
                    best_candidate = b_id
            
            if best_candidate:
                deck.append(best_candidate)
                for t in self.blessings[best_candidate].get('identity_tags', []):
                    current_tags[t] = current_tags.get(t, 0) + 1
                
                if check_snapped(current_tags):
                    return deck, True
            else:
                # No useful blessings found to advance state
                break
                
        return deck, False

    def run_full_audit(self):
        self.log("="*60)
        self.log(f"GODLESS UTS SYSTEM AUDIT REPORT")
        self.log(f"Classes Loaded:   {len(self.classes)}")
        self.log(f"Blessings Loaded: {len(self.blessings)}")
        self.log(f"Items Loaded:     {sum(len(v) for v in self.items.values())}")
        self.log("="*60 + "\n")

        sorted_classes = sorted(self.classes.items(), key=lambda x: x[1].get('name', x[0]))

        for c_id, c_data in sorted_classes:
            class_name = c_data.get('name', c_id)
            recipe = c_data.get('recipe', {})
            
            if not recipe:
                self.log(f"CLASS: {class_name.upper()} (Base Class)")
                self.log("-" * 30)
                continue

            # Determine Kingdom Tag for Affinity
            kingdom_raw = c_data.get('kingdom', 'Universal')
            if isinstance(kingdom_raw, list): kingdom_raw = kingdom_raw[0]
            
            kingdom_tag = None
            if kingdom_raw == 'Dark': kingdom_tag = 'dark'
            elif kingdom_raw == 'Light': kingdom_tag = 'holy'
            elif kingdom_raw == 'Instinct': kingdom_tag = 'instinct'

            # 1. Naked Test
            deck, snapped = self._find_best_deck_dynamic(class_name, recipe, kingdom_tag)
            
            deck_size = len(deck)
            gear_dependent = False
            gear_tags = {}
            gear_names = []

            # 2. Gear Test (if Naked failed or inefficient)
            if not snapped or deck_size > 9:
                gear_tags, gear_names = self.find_best_gear_loadout(recipe)
                g_deck, g_snapped = self._find_best_deck_dynamic(class_name, recipe, kingdom_tag, gear_tags)
                
                # If gear helps us reach efficiency
                if g_snapped and len(g_deck) <= 9:
                    deck = g_deck
                    deck_size = len(g_deck)
                    snapped = True
                    gear_dependent = True

            self.log(f"CLASS: {class_name.upper()}")
            self.log(f"  Recipe: {json.dumps(recipe)}")
            
            if not snapped:
                self.log(f"  [!] CRITICAL: Unreachable (Even with gear).")
            else:
                status = "OK"
                if deck_size > 9: status = "IMPOSSIBLE (>9 Slots)"
                elif deck_size <= 2: status = "TOO EASY (<=2 Slots)"
                
                if gear_dependent:
                    self.log(f"  - Snap Efficiency: {deck_size} slots [GEAR DEPENDENT]")
                    self.log(f"    Gear Used: {gear_names}")
                else:
                    self.log(f"  - Snap Efficiency: {deck_size} slots ({status})")

                # 3. Collision Test
                collisions = self.run_collision_test(class_name, deck, gear_tags)
                if collisions:
                    self.log(f"  [!] WARNING: Dual-Snaps detected: {collisions}")

            # 4. Bridge Test
            bridge_stats = self.run_bridge_efficiency_test(recipe)
            self.log(f"  - Bridge Efficiency: {bridge_stats}")

            self.log("-" * 30)

        try:
            with open(REPORT_FILE, 'w', encoding='utf-8') as f:
                f.write("\n".join(self.report_lines))
            print(f"\nReport saved to: {os.path.abspath(REPORT_FILE)}")
        except Exception as e:
            print(f"Failed to write report: {e}")

if __name__ == "__main__":
    # Handle running from tools/ or root
    if os.path.basename(os.getcwd()) == "tools":
        os.chdir("..")
        
    if os.path.exists(CLASS_DIR) and os.path.exists(BLESSING_DIR) and os.path.exists(ITEM_DIR):
        sim = SnapSimulator(CLASS_DIR, BLESSING_DIR, ITEM_DIR)
        sim.run_full_audit()
    else:
        print(f"Error: Could not find data directories.")
        print(f"Expected: {os.path.abspath(CLASS_DIR)} and {os.path.abspath(ITEM_DIR)}")
