import logging
from utilities.colors import Colors

logger = logging.getLogger("GodlessMUD")

def calculate_identity(player, preferred_class=None, tag_cache=None):
    """
    Redirects to ResonanceAuditor to ensure Voltage (tag sums) are updated.
    Does NOT automatically change player class.
    """
    from logic.engines.resonance_engine import ResonanceAuditor
    ResonanceAuditor.calculate_resonance(player, preferred_class=preferred_class)


def check_unlocks(player):
    """
    Checks if player qualifies for any new classes based on KNOWN blessings.
    Adds to player.unlocked_classes.
    Returns list of newly unlocked Class objects.
    """
    # 1. Count tags in known collection
    tag_counts = {}
    for b_id in player.known_blessings:
        blessing = player.game.world.blessings.get(b_id)
        if not blessing: continue
        for tag in blessing.identity_tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
            
    newly_unlocked = []
    
    for cls in player.game.world.classes.values():
        if cls.id in player.unlocked_classes:
            continue
            
        match = True
        reqs = getattr(cls, 'recipe', {})
        
        if not reqs: 
            continue
        
        for tag, required_count in reqs.items():
            if tag_counts.get(tag, 0) < required_count:
                match = False
                break
        
        if match:
            player.unlocked_classes.append(cls.id)
            newly_unlocked.append(cls)
            player.send_line(f"{Colors.GREEN}You have unlocked the {cls.name} class!{Colors.RESET}")
            
    return newly_unlocked

def apply_kit(player, archetype, kits=None):
    """
    Equips a kit for the specified class from data/kits.json.
    Used by @class admin command and Commune interaction.
    """
    import os
    import json
    import copy
    from models import Armor, Weapon
    from logic.engines.resonance_engine import ResonanceAuditor

    if not kits:
        kits_path = "data/kits.json"
        if not os.path.exists(kits_path):
            return False, "data/kits.json not found"
        try:
            with open(kits_path, "r") as f:
                kits = json.load(f)
        except Exception:
            return False, "Invalid JSON in kits.json"

    if archetype not in kits:
        return False, f"Unknown archetype: {archetype}"
        
    kit = kits[archetype]
    
    # --- RESET LOGIC (Clean Slate) ---
    player.state = "normal"
    player.fighting = None
    player.attackers = []
    player.is_resting = False
    
    # Inventory & Deck
    player.inventory = []
    player.equipped_blessings = []
    player.known_blessings = []
    player.status_effects = {}
    player.cooldowns = {}
    
    # Clear Equipment (All Slots)
    slots = ["equipped_weapon", "equipped_offhand", "equipped_armor", "equipped_head", "equipped_neck", "equipped_shoulders", "equipped_arms", "equipped_hands", "equipped_finger_l", "equipped_finger_r", "equipped_legs", "equipped_feet", "equipped_floating", "equipped_mount"]
    for slot in slots:
        setattr(player, slot, None)
        
    kit['id'] = archetype
    player.active_kit = kit
    # ---------------------------------

    # 1. Equip Gear
    for item_id in kit.get("gear", []):
        item = player.game.world.items.get(item_id)
        if item:
            new_item = copy.deepcopy(item)
            player.inventory.append(new_item)
            
            # Slot-based Auto-Equip
            slot = getattr(new_item, 'slot', None)
            flags = getattr(new_item, 'flags', [])
            
            if slot == "off_hand" or "shield" in flags:
                player.equipped_offhand = new_item
            elif slot == "main_hand" or isinstance(new_item, Weapon):
                player.equipped_weapon = new_item
            elif slot == "head" or "head" in flags:
                player.equipped_head = new_item
            elif slot == "legs":
                player.equipped_legs = new_item
            elif slot == "feet":
                player.equipped_feet = new_item
            elif slot == "hands":
                player.equipped_hands = new_item
            elif slot == "arms":
                player.equipped_arms = new_item
            elif slot == "shoulders":
                player.equipped_shoulders = new_item
            elif isinstance(new_item, Armor):
                # Default Armor to body slot
                player.equipped_armor = new_item

        
    # 2. Equip Blessings
    missing_blessings = []
    for b_id in kit.get("blessings", []):
        if b_id in player.game.world.blessings:
            if b_id not in player.known_blessings:
                player.known_blessings.append(b_id)
            if b_id not in player.equipped_blessings:
                player.equipped_blessings.append(b_id)
        else:
            missing_blessings.append(b_id)
            logger.error(f"[KIT_ERROR] Blessing '{b_id}' not found in world.blessings for kit '{archetype}'")

    if missing_blessings and player.is_admin:
        player.send_line(f"{Colors.RED}[WARN] The following blessings are missing from the world and couldn't be equipped: {', '.join(missing_blessings)}{Colors.RESET}")

    # 3. Finalize Identity
    ResonanceAuditor.calculate_resonance(player, preferred_class=archetype)
    player.active_class = archetype
    
    if hasattr(player, 'reset_resources'):
        player.reset_resources()
        
    return True, f"You have become a {archetype.capitalize()}."

def get_classes_by_kingdom(world, kingdom):
    """
    Returns a list of Class objects that belong to the specified kingdom.
    Handles both string and list formats for the 'kingdom' attribute.
    """
    matches = []
    for class_obj in world.classes.values():
        # Check if kingdom attribute exists (handling legacy models)
        c_kingdom = getattr(class_obj, 'kingdom', 'None')
        
        if isinstance(c_kingdom, list):
            if kingdom in c_kingdom:
                matches.append(class_obj)
        elif isinstance(c_kingdom, str):
            if c_kingdom == kingdom:
                matches.append(class_obj)
                
    return matches

def get_class_kingdoms(class_obj):
    """Returns a list of kingdoms a class belongs to."""
    c_kingdom = getattr(class_obj, 'kingdom', 'None')
    if isinstance(c_kingdom, list):
        return c_kingdom
    return [c_kingdom]
