import json
import glob
import os

coords = {} # (x, y, z) -> [room_ids]

for f_path in glob.glob("data/zones/*.json"):
    try:
        with open(f_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        rooms = data.get('rooms', [])
        for r in rooms:
            if isinstance(r, dict):
                x, y, z = r.get('x'), r.get('y'), r.get('z')
                if x is not None and y is not None and z is not None:
                    c = (x, y, z)
                    if c not in coords: coords[c] = []
                    coords[c].append(r.get('id'))
    except:
        pass

overlaps = {c: ids for c, ids in coords.items() if len(ids) > 1}
for c, ids in overlaps.items():
    if len(ids) > 1:
        print(f"Overlap at {c}: {ids[:5]} (Total: {len(ids)})")
