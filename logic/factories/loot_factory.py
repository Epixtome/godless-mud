import random
import json
import os
import logging
from models import Weapon, Armor, Item

logger = logging.getLogger("GodlessMUD")

# --- Configuration (Loaded from JSON) ---

TIERS = {}
MATERIALS = {}
DICE_LADDER = []
PREFIXES = {}
SUFFIXES = {}
TEMPLATES = {}

def load_loot_tables():
    global TIERS, MATERIALS, DICE_LADDER, PREFIXES, SUFFIXES, TEMPLATES
    path = "data/loot_tables.json"
    if not os.path.exists(path):
        logger.error(f"Loot tables not found at {path}")
        return

    try:
        with open(path, 'r') as f:
            data = json.load(f)
            TIERS = data.get("tiers", {})
            MATERIALS = data.get("materials", {})
            DICE_LADDER = data.get("dice_ladder", [])
            PREFIXES = data.get("prefixes", {})
            SUFFIXES = data.get("suffixes", {})
            TEMPLATES = data.get("templates", {})
    except Exception as e:
        logger.error(f"Failed to load loot tables: {e}")

# Initial Load
load_loot_tables()

def generate_loot(level=1, quality="standard", material=None, mob_tier=1):
    """
    Generates a random item based on level and quality tier.
    Returns an Item, Weapon, or Armor object.
    """
    if not TEMPLATES:
        load_loot_tables() # Safety reload

    # 1. Select Template
    template_key = random.choice(list(TEMPLATES.keys()))
    template = TEMPLATES[template_key]
    
    # 2. Resolve Material
    if material is None:
        mat_type = template.get("material_type", "metal")
        
        if quality == "exotic":
            valid_mats = [m for m, data in MATERIALS.items() if data["type"] == mat_type and data["tier"] >= 3 and data["tier"] <= mob_tier + 1]
            if not valid_mats:
                valid_mats = [m for m, data in MATERIALS.items() if data["type"] == mat_type]
        else:
            valid_mats = [m for m, data in MATERIALS.items() if data["type"] == mat_type and data["tier"] <= mob_tier]
            
        if not valid_mats:
            valid_mats = [m for m, data in MATERIALS.items() if data["type"] == mat_type]
            
        material = random.choice(valid_mats) if valid_mats else "iron"

    mat_config = MATERIALS.get(material, next(iter(MATERIALS.values())) if MATERIALS else {})

    # 3. Resolve Tier
    tier_config = TIERS.get(quality, TIERS.get("standard", {}))

    # 4. Resolve Affixes
    prefix_data = None
    suffix_data = None
    
    prefix_chance = 1.0 if quality == "exotic" else 0.5
    suffix_chance = 1.0 if quality == "exotic" else 0.2
    
    prefix_name = None
    suffix_name = None

    if random.random() < prefix_chance:
        valid_prefixes = [p for p, data in PREFIXES.items() if data["tier"] <= mob_tier]
        prefix_name = random.choice(valid_prefixes) if valid_prefixes else None
        if prefix_name:
            prefix_data = PREFIXES[prefix_name]
            
    if random.random() < suffix_chance:
        suffix_name = random.choice(list(SUFFIXES.keys())) if SUFFIXES else None
        if suffix_name:
            suffix_data = SUFFIXES[suffix_name]
    
    # 5. Calculate Name
    display_prefix = prefix_name if prefix_data else tier_config.get("prefix", "")
    display_suffix = suffix_name if suffix_data else ""
    
    name = f"{display_prefix} {material.capitalize()} {template['name']} {display_suffix}".strip()
    
    # 6. Prepare Tags
    tags = template["tags"].copy()
    for w in ["light", "medium", "heavy"]:
        tags.pop(w, None)
    
    if mat_config:
        tags[mat_config.get("weight", "medium")] = 1
        if "tags" in mat_config:
            for k, v in mat_config["tags"].items():
                tags[k] = tags.get(k, 0) + v
    
    dice_offset_accum = tier_config.get("dice_offset", 0) + mat_config.get("dice_offset", 0)
    
    if prefix_data:
        dice_offset_accum += prefix_data.get("dice_offset", 0)
        for k, v in prefix_data.get("tags", {}).items():
            tags[k] = tags.get(k, 0) + v
            
    if suffix_data:
        for k, v in suffix_data.get("tags", {}).items():
            tags[k] = tags.get(k, 0) + v
    
    # 7. Instantiate
    item = None
    
    if template["type"] == "weapon":
        idx = template["base_dice_index"] + dice_offset_accum
        idx = max(0, min(len(DICE_LADDER)-1, idx)) if DICE_LADDER else 0
        damage_dice = DICE_LADDER[idx] if DICE_LADDER else "1d4"
        
        item = Weapon(
            name=name,
            description=template["desc"],
            damage_dice=damage_dice,
            scaling=template.get("scaling", {}),
            value=0,
            tags=tags
        )
        
    elif template["type"] == "armor":
        defense = int(template["base_defense"] * tier_config.get("mult", 1.0) * mat_config.get("mult", 1.0))
        defense = int(defense * (1 + (level * 0.1)))
        
        item = Armor(
            name=name,
            description=template["desc"],
            defense=defense,
            value=0,
            tags=tags
        )
        
    # 8. Finalize Item Properties
    if item:
        item.weight_class = mat_config.get("weight", "medium")
        item.weight = int(template.get("base_weight", 1) * mat_config.get("weight_mult", 1.0))
        item.slot = template.get("slot", "none")
        item.material = material
        item.max_integrity = mat_config.get("max_integrity", 50)
        item.integrity = item.max_integrity
        
        tag_density_bonus = sum(tags.values()) * 5
        base_value = 10 * tier_config.get("mult", 1.0) * level
        item.value = int(base_value + tag_density_bonus)
            
    return item
