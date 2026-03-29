import os

content = '''"""Standard utilities."""
import logic.common as common

def get_target(player, args, target=None):
    return common._get_target(player, args, target)
'''

modules_to_fix = [
    "barbarian", "knight", "mage", "rogue", "druid", 
    "warlock", "paladin", "ranger", "bard", "samurai", 
    "necromancer", "illusionist", "beastmaster", "archer", 
    "assassin", "berserker", "ninja", "thief", "dragoon", 
    "elementalist", "engineer", "gambler", "gunner",
    "shadow_dancer", "shadow_blade", "soul_reaver", "soul_weaver",
    "defiler", "witch", "black_mage", "death_knight"
]

base_dir = r"c:\Users\Chris\antigravity\Godless\logic\modules"

for m in modules_to_fix:
    path = os.path.join(base_dir, m, "utils.py")
    dir_path = os.path.dirname(path)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    with open(path, 'w') as f:
        f.write(content)
        print(f"Fixed {path}")
