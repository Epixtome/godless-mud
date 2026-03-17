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
    [V6.0] Procedural Gear Generation.
    Generates a random item based on level and quality tier.
    Returns an Item, Weapon, or Armor object with calculated CR.
    """
    from logic import calibration
    if not TEMPLATES:
        load_loot_tables() # Safety reload

    # 1. Select Template
    template_key = random.choice(list(TEMPLATES.keys()))
    template = TEMPLATES[template_key]
    
    # 2. Resolve Material
    if material is None:
        mat_type = template.get("material_type", "metal")
        
        if quality == "exotic":
            valid_mats = [m for m, data in MATERIALS.items() if data["type"] == mat_type and data["tier"] >= 2]
        else:
            valid_mats = [m for m, data in MATERIALS.items() if data["type"] == mat_type and data["tier"] <= mob_tier]
            
        if not valid_mats:
            valid_mats = [m for m, data in MATERIALS.items() if data["type"] == mat_type]
            
        material = random.choice(valid_mats) if valid_mats else "iron"

    mat_config = MATERIALS.get(material)
    if not mat_config:
        mat_config = next(iter(MATERIALS.values())) if MATERIALS else {}

    # 3. Resolve Tier
    tier_config = TIERS.get(quality) or TIERS.get("standard") or {}

    # 4. Resolve Affixes (Prefixes/Suffixes)
    prefix_data = None
    suffix_data = None
    
    prefix_chance = 0.8 if quality == "exotic" else 0.3
    suffix_chance = 0.6 if quality == "exotic" else 0.1
    
    prefix_name = None
    suffix_name = None

    if random.random() < prefix_chance:
        valid_prefixes = [p for p, data in PREFIXES.items() if data["tier"] <= mob_tier + 1]
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
    
    # 6. Prepare Tags (UTS Protocol)
    tags = template.get("tags", {}).copy()
    
    # Apply material tags
    if mat_config:
        for k, v in mat_config.get("tags", {}).items():
            tags[k] = tags.get(k, 0) + v
    
    # Apply prefix/suffix tags
    if prefix_data:
        for k, v in prefix_data.get("tags", {}).items():
            tags[k] = tags.get(k, 0) + v
            
    if suffix_data:
        for k, v in suffix_data.get("tags", {}).items():
            tags[k] = tags.get(k, 0) + v

    # 7. Calculate Stats & Instantiate
    item = None
    dice_offset_accum = tier_config.get("dice_offset", 0) + mat_config.get("dice_offset", 0)
    if prefix_data: dice_offset_accum += prefix_data.get("dice_offset", 0)
    
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
        # Scaled defense based on level
        defense = int(defense * (1 + (level * 0.1)))
        
        item = Armor(
            name=name,
            description=template["desc"],
            defense=defense,
            value=0,
            tags=tags
        )
    else:
        item = Item(name=name, description=template["desc"], value=0, tags=tags)

    # 8. Finalize Item Properties (V6.0 Calibration)
    if item:
        # Calculate Weight
        final_weight = int(template.get("base_weight", 5) * mat_config.get("weight_mult", 1.0))
        setattr(item, 'weight', final_weight)
        setattr(item, 'slot', template.get("slot", "none"))
        setattr(item, 'material', material)
        
        # Determine Weight Class based on calibration thresholds
        if final_weight <= calibration.ScalingRules.WEIGHT_LIGHT_MAX:
            w_class = "light"
        elif final_weight <= calibration.ScalingRules.WEIGHT_MEDIUM_MAX:
            w_class = "medium"
        else:
            w_class = "heavy"
        setattr(item, 'weight_class', w_class)
        
        # Calculate Combat Rating (CR)
        # Formula: CR = (QualityMult * MaterialTier) + (TagDensity * 0.5)
        tag_density = sum(tags.values()) if isinstance(tags, dict) else len(tags)
        mat_tier = mat_config.get("tier", 1)
        quality_mult = tier_config.get("mult", 1.0)
        
        cr = (quality_mult * mat_tier) + (tag_density * 0.2)
        if template["type"] == "weapon":
            # Weapons get a slight bump from dice index
            cr += (dice_offset_accum * 0.5)
            
        item.combat_rating = round(max(1.0, cr), 2)
        item.power = quality_mult # Legacy support
        
        # Value calculation
        base_value = 10 * quality_mult * level
        item.value = int(base_value + (tag_density * 10))
        
        item.prototype_id = f"proc_{item.name.lower().replace(' ', '_')}"

    return item
