import os

logic_modules_dir = "logic/modules"
kits_dir = "data/blessings/kits"

# Get all directories in logic/modules
modules = [d for d in os.listdir(logic_modules_dir) if os.path.isdir(os.path.join(logic_modules_dir, d)) and not d.startswith("_")]

# Get all json files in data/blessings/kits (remove .json)
kits = [f[:-5] for f in os.listdir(kits_dir) if f.endswith(".json")]

print("Class Status Audit")
print("==================")
print(f"Total Modules found: {len(modules)}")
print(f"Total Kits found: {len(kits)}")
print("")

upgraded = []
legacy = []

for mod in sorted(modules):
    if mod in kits:
        upgraded.append(mod)
    else:
        legacy.append(mod)

print("UPGRADED CLASSES (JSON Kit Exists):")
for u in upgraded:
    print(f"  [X] {u}")

print("")
print("LEGACY CLASSES (No JSON Kit in 'kits/'):")
for l in legacy:
    print(f"  [ ] {l}")

# Check for orphan kits
orphans = [k for k in kits if k not in modules]
if orphans:
    print("")
    print("ORPHAN KITS (JSON exists but no logic/module):")
    for o in orphans:
        print(f"  [?] {o}")
