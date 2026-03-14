import os
import json
import importlib
import importlib.util
import sys

# Add root to path for imports
sys.path.append(os.getcwd())

class LoomValidator:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def log_error(self, msg):
        self.errors.append(msg)
        print(f"\033[91m[ERROR]\033[0m {msg}")

    def log_warning(self, msg):
        self.warnings.append(msg)
        print(f"\033[93m[WARN]\033[0m {msg}")

    def validate_kits(self):
        print("Loom: Validating Kits and Modules...")
        kits_path = "data/kits.json"
        if not os.path.exists(kits_path):
            self.log_error("kits.json missing.")
            return

        with open(kits_path, "r") as f:
            kits = json.load(f)

        for kit_id, data in kits.items():
            # 1. Check Module Existence
            mod_path = f"logic/modules/{kit_id}"
            if not os.path.exists(mod_path):
                self.log_warning(f"Kit '{kit_id}' has no logic/modules/ directory.")
                continue

            # 2. Check State Init
            state_file = os.path.join(mod_path, "state.py")
            if os.path.exists(state_file):
                try:
                    spec = importlib.util.spec_from_file_location(f"{kit_id}.state", state_file)
                    if not spec:
                        self.log_error(f"Could not create spec for {state_file}")
                        continue
                    state_mod = importlib.util.module_from_spec(spec)
                    if spec.loader:
                        spec.loader.exec_module(state_mod)
                    if not hasattr(state_mod, "initialize") and not hasattr(state_mod, f"initialize_{kit_id}"):
                        self.log_warning(f"Module '{kit_id}' state.py lacks initialize() or initialize_{kit_id}()")
                except Exception as e:
                    self.log_error(f"Failed to load {state_file}: {e}")
            
            # 3. Check Event Registration
            events_file = os.path.join(mod_path, "events.py")
            if os.path.exists(events_file):
                try:
                    spec = importlib.util.spec_from_file_location(f"{kit_id}.events", events_file)
                    if not spec:
                        self.log_error(f"Could not create spec for {events_file}")
                        continue
                    events_mod = importlib.util.module_from_spec(spec)
                    if spec.loader:
                        spec.loader.exec_module(events_mod)
                    if not hasattr(events_mod, "register_events"):
                        self.log_error(f"Module '{kit_id}' events.py missing register_events()")
                except Exception as e:
                    self.log_error(f"Failed to load {events_file}: {e}")

            # 4. Blessing Integrity
            blessings = data.get("blessings", [])
            self.validate_blessings(kit_id, blessings)

    def validate_blessings(self, kit_id, blessing_ids):
        # We check classes/ or blessings/ directories
        found_blessings = {}
        bless_dir = "data/blessings"
        if os.path.exists(bless_dir):
            for f in os.listdir(bless_dir):
                if f.endswith(".json"):
                    try:
                        with open(os.path.join(bless_dir, f), "r") as j:
                            payload = json.load(j)
                            # Format 1: {"blessings": {"id": {...}}}
                            if isinstance(payload, dict) and "blessings" in payload:
                                b_content = payload["blessings"]
                                if isinstance(b_content, dict):
                                    found_blessings.update(b_content)
                                elif isinstance(b_content, list):
                                    for b in b_content:
                                        if isinstance(b, dict) and "id" in b:
                                            found_blessings[b["id"]] = b
                            # Format 2: [{"id": ...}]
                            elif isinstance(payload, list):
                                for b in payload:
                                    if isinstance(b, dict) and "id" in b:
                                        found_blessings[b["id"]] = b
                    except Exception as e:
                        self.log_error(f"Failed to read blessing file {f}: {e}")

        for b_id in blessing_ids:
            if b_id not in found_blessings:
                self.log_error(f"Kit '{kit_id}' references non-existent blessing: '{b_id}'")
            else:
                b_data = found_blessings[b_id]
                if not b_data.get("identity_tags"):
                    self.log_warning(f"Blessing '{b_id}' has NO identity_tags. UTS will fail.")
                if not b_data.get("action"):
                    self.log_warning(f"Blessing '{b_id}' has NO action mapping.")

    def run(self):
        self.validate_kits()
        print("\n" + "="*30)
        print(f"Loom Cycle Complete: {len(self.errors)} Errors, {len(self.warnings)} Warnings.")
        return len(self.errors) == 0

if __name__ == "__main__":
    validator = LoomValidator()
    if not validator.run():
        sys.exit(1)
