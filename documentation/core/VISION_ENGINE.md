# Vision System Overhaul: High-Elevation Visibility

> **Status:** DRAFT PROPOSAL
> **Target:** `logic/engines/vision_engine.py`
> **Objective:** Fix "Blind Peak" syndrome where players on high elevation (Z-axis) cannot see terrain on lower Z-levels.

---

## 1. Problem Analysis

### A. The "Flat Earth" Assumption
Currently, `get_visible_rooms` in `vision_engine.py` strictly queries the Spatial Engine for rooms at the player's exact Z-coordinate:

```python
# Current Logic (vision_engine.py:176)
r = spatial.get_room(tx, ty, sz)
```

If a player stands on a Peak at `Z=5` and looks at a valley at `Z=0`, the engine queries `(tx, ty, 5)`. Since the valley floor is at `Z=0`, the query returns `None` (Air), and the map renders nothing or "Void" for that tile.

### B. The "Infinite Wall" Raycast
Even if we fix the Z-query, the `raycast` function treats all terrain as fully occupying its voxel.

If a player looks from `Z=5` to `Z=0`, the 3D Bresenham line algorithm will calculate intermediate steps (e.g., `Z=4`, `Z=3`). If it encounters a "Mountain" room at `Z=4`, and Mountain opacity is `0.9` or `1.0`, the ray is blocked.

While physically accurate for solid voxels, this feels bad in a game where "Peak" implies being *on top* of the mountain, not inside a solid block of stone. We need logic to simulate "looking over" terrain that is significantly below the observer.

---

## 2. Implementation Plan

### Step 1: Implement "Top-Down" Surface Scanning
Modify `get_visible_rooms` to scan downwards from the player's Z-level to find the "highest non-air room" at each X/Y coordinate.

**Logic:**
1. Iterate `check_z` from `player.z` down to `player.z - VIEW_DEPTH` (e.g., 5 levels).
2. The first room found is considered the "Surface" for that tile.
3. If the player is *underground* (negative Z), we might need to scan upwards or restrict this behavior, but for now, we assume standard outdoor rules.

### Step 2: Elevation Advantage in Raycasting
Modify `_check_step` to allow the observer to ignore opacity if they are sufficiently higher than the obstacle.

**Logic:**
1. Pass `start_room` into `_check_step`.
2. Calculate `observer_height` vs `obstacle_height`.
3. If `observer_height > obstacle_height`, bypass the `get_opacity >= 1.0` check.

---

## 3. Proposed Code Changes

### A. Update `get_visible_rooms`

```python
def get_visible_rooms(start_room, radius, world, check_los=True, debug_player=None):
    # ... setup ...
    sx, sy, sz = start_room.x, start_room.y, start_room.z
    VIEW_DEPTH = 6 # How far down we look

    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            # ...
            tx, ty = sx + dx, sy + dy
            
            # NEW: Scan downwards for surface
            r = None
            for dz in range(0, VIEW_DEPTH):
                check_z = sz - dz
                found = spatial.get_room(tx, ty, check_z)
                if found:
                    r = found
                    break # Found the top-most room
            
            if not r: continue
            
            # ... existing LOS checks ...
```

### B. Update `_check_step` signature

```python
def _check_step(curr_room, next_room, target_room, start_room):
    # ...
    # Elevation Bypass
    # If observer is at Z=5 and obstacle is at Z=4, we see over it.
    if start_room.z > next_room.z:
        return True
        
    # Standard Opacity
    if get_opacity(next_room) >= 1.0:
        return False
    return True
```

---

## 4. Safety Checks & Verification

1.  **Performance**: The nested Z-loop in `get_visible_rooms` adds overhead.
    *   *Mitigation*: `spatial.get_room` is a fast dictionary lookup. 5 lookups per tile is acceptable for a 5x5 grid (25 tiles * 5 = 125 lookups). For larger maps (`@zonemap`), we might need to optimize or disable the Z-scan.
2.  **Indoor/Dungeon Handling**:
    *   If `start_room.terrain == 'indoors'`, disable Z-scanning to prevent seeing through floors?
    *   *Decision*: For V1, apply globally. Most dungeons are spread out on X/Y.
3.  **Raycast Precision**:
    *   Ensure `raycast` passes `start_room` correctly to `_check_step`.

## 5. Execution Order
1.  Apply changes to `logic/engines/vision_engine.py`.
2.  Restart server (`@restart`).
3.  Test by teleporting to a Peak (`@tp <coords>`) and looking down.