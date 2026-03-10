import os
import json

# Load Decay Config
DECAY_CONFIG = {"default": 150}
if os.path.exists("data/decay.json"):
    try:
        with open("data/decay.json", "r") as f:
            data = json.load(f)
            DECAY_CONFIG.update(data.get("decay", {}))
    except Exception as e:
        print(f"Error loading decay.json: {e}")

def register_decay(game, item, room):
    """Signals the system to start tracking an item for decay."""
    if not game: return
    if not hasattr(game, 'decaying_items') or game.decaying_items is None:
        game.decaying_items = set()
    game.decaying_items.add((item, room))

def initialize_decay(game):
    """One-time scan to populate the registry (e.g., after server restart)."""
    if not hasattr(game, 'decaying_items'):
        game.decaying_items = set()
        
    for room in game.world.rooms.values():
        if hasattr(room, 'items'):
            for item in room.items:
                if hasattr(item, 'flags') and "decay" in item.flags:
                    game.decaying_items.add((item, room))

def decay(game):
    """Processes decay for registered items only."""
    if not hasattr(game, 'decaying_items'):
        return

    # Use a copy to allow modification during iteration
    for entry in list(game.decaying_items):
        item, room = entry
        
        # Validation: If item is no longer in the room, stop tracking
        if item not in room.items:
            game.decaying_items.discard(entry)
            continue
            
        # Determine Rate
        if getattr(item, 'timer', None) is None:
            key = "default"
            for k in DECAY_CONFIG:
                if k in item.name.lower() or (hasattr(item, 'tags') and k in item.tags):
                    key = k
                    break
            item.timer = DECAY_CONFIG.get(key, 150)
            
        item.timer -= 1
        
        if item.timer <= 0:
            if item in room.items:
                room.items.remove(item)
                if room.players:
                    room.broadcast(f"{item.name} crumbles into dust.")
            game.decaying_items.discard(entry)
