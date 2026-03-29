import os

content = '''"""Standard utilities."""
import logic.common as common

def get_target(player, args, target=None):
    return common._get_target(player, args, target)
'''

modules_to_fix = [
    "guardian", "hunter", "sorcerer", "temporalist", 
    "chemist", "dancer", "summoner", "puppet_master", "machinist"
]

base_dir = r"c:\Users\Chris\antigravity\Godless\logic\modules"

for m in modules_to_fix:
    path = os.path.join(base_dir, m, "utils.py")
    with open(path, 'w') as f:
        f.write(content)
        print(f"Fixed {path}")
