
import random
import logging
from models import Monster, Weapon, Armor, Item
from logic import calibration

logger = logging.getLogger("GodlessMUD")

class DynamicFactory:
    """
    [V6.0] The Godless Evolution Engine.
    Generates entities (Mobs, Gear) on the fly based on Combat Rating (CR) and Grammar Tags.
    """

    @staticmethod
    def generate_mob(cr, tags=None, base_type="entity", game=None):
        """
        Creates a monster scaled to a specific Combat Rating.
        CR = (AxesScore + 1.0) * ( (HP/100) * (DMG/5) )
        """
        tags = tags or []
        cr = float(cr)

        # 1. Template Resolution (For flavor and base traits)
        template = None
        if game:
            template = game.world.monsters.get(base_type.lower())
            if not template:
                # Try ID search for specific variants
                for mid, m in game.world.monsters.items():
                    if base_type.lower() == mid or base_type.lower() in m.name.lower():
                        template = m
                        break
        
        base_name = getattr(template, 'name', base_type.capitalize())
        base_desc = getattr(template, 'description', f"A {base_type} imbued with primordial energy.")
        base_tags = getattr(template, 'tags', [])
        
        # Merge tags (Unique only)
        merged_tags = list(set(tags + base_tags))

        # 2. Resolve Axis Score from Grammar Tags
        axes_score = 0.0
        for axis in calibration.CombatRating.AXIS_DEFAULTS.keys():
            if axis in merged_tags:
                axes_score += 2.0
        
        # Apply specialized status tags based on grammar
        grammar_map = {
            "fire": "burning",
            "frost": "frozen",
            "lightning": "shocked",
            "venom": "poisoned",
            "shadow": "blinded",
            "void": "confused"
        }
        
        for g_tag, state in grammar_map.items():
            if g_tag in merged_tags and f"applies_{state}" not in merged_tags:
                merged_tags.append(f"applies_{state}")

        # Recalculate axes score with state values
        for state, val in calibration.CombatRating.STATE_VALUES.items():
            if f"applies_{state}" in merged_tags:
                axes_score += val

        # 3. Derive Vitals from CR
        vitals_mult = cr / (axes_score + 1.0)
        
        # Balanced distribution (Target: 100 HP / 5 DMG for mult 1.0)
        hp = int((vitals_mult ** 0.5) * 100)
        damage = int((vitals_mult ** 0.5) * 5)

        # Sanity Capping
        hp = max(10, min(3000, hp))
        damage = max(1, min(250, damage))

        # 4. Construct Identity
        adjectives = [t.capitalize() for t in tags if "applies_" not in t]
        full_name = " ".join(adjectives + [base_name]).strip()
        
        proto_id = f"gen_{full_name.lower().replace(' ', '_')}_{int(cr)}"

        mob = Monster(
            name=full_name,
            description=f"[CR {cr}] {base_desc}",
            hp=hp,
            damage=damage,
            tags=merged_tags,
            prototype_id=proto_id,
            game=game
        )
        mob.combat_rating = cr
        
        # Inherit non-vitals from template (shouts, loadout)
        if template:
            inherit_attrs = [
                'shouts', 'loadout', 'vulnerabilities', 'states', 'triggers', 
                'base_mitigation', 'base_concealment', 'base_perception', 
                'is_shopkeeper', 'loot_table', 'active_class'
            ]
            for attr in inherit_attrs:
                if hasattr(template, attr):
                    # Shallow copy dicts/lists to avoid shared state
                    val = getattr(template, attr)
                    if isinstance(val, dict):
                        setattr(mob, attr, val.copy())
                    elif isinstance(val, list):
                        setattr(mob, attr, val[:])
                    else:
                        setattr(mob, attr, val)

        return mob

    @staticmethod
    def generate_gear(cr, tags=None, base_type="sword", slot="weapon", game=None):
        """
        [V6.0] Evolution Engine: Gear.
        Creates gear scaled to a specific Combat Rating.
        """
        tags = tags or []
        cr = float(cr)
        from logic.factories import loot_factory
        from logic import calibration
        
        # 1. Resolve Tier
        quality = "standard"
        if "exotic" in tags: quality = "exotic"
        elif "scrap" in tags: quality = "scrap"
        elif cr >= 12: quality = "exotic"
        
        tier_config = loot_factory.TIERS.get(quality, loot_factory.TIERS.get("standard", {}))
        if tier_config is None: tier_config = {}

        if not loot_factory.TEMPLATES:
            loot_factory.load_loot_tables()

        # 2. Find Template and Material
        potential_templates = [t for t in loot_factory.TEMPLATES.values() if base_type.lower() in t['name'].lower() or base_type.lower() == t['type']]
        template = random.choice(potential_templates) if potential_templates else next(iter(loot_factory.TEMPLATES.values()), None)
        
        if not template:
            # Fallback to a hardcoded minimal template
            template = {"name": base_type, "type": "item", "desc": "A generated object.", "base_weight": 5, "tags": {}}

        material = None
        for mat in (loot_factory.MATERIALS.keys() if loot_factory.MATERIALS else []):
            if mat in tags:
                material = mat
                break
        
        if not material:
            mat_type = template.get("material_type", "metal")
            # If CR is high, prefer higher tier materials
            if cr >= 10:
                valid_mats = [m for m, data in loot_factory.MATERIALS.items() if data["type"] == mat_type and data["tier"] >= 2]
            else:
                valid_mats = [m for m, data in loot_factory.MATERIALS.items() if data["type"] == mat_type and data["tier"] <= (cr // 5) + 1]
            
            material = random.choice(valid_mats) if valid_mats else "iron"

        mat_config = loot_factory.MATERIALS.get(material, {})
        if mat_config is None: mat_config = {}
        
        # 3. Construct Identity
        # Filter out common tags that shouldn't be in the name
        banned_adjectives = [material, quality, "level", "new", "exotic", "standard", "scrap"]
        adjectives = [t.capitalize() for t in tags if t.lower() not in banned_adjectives]
        full_name = f"{quality.capitalize()} {material.capitalize()} {template['name']}"
        if adjectives:
            full_name = f"{' '.join(adjectives)} {full_name}"

        # 4. Calculate Stats
        raw_tags = template.get("tags")
        if isinstance(raw_tags, dict):
            item_tags = raw_tags.copy()
        elif isinstance(raw_tags, list):
            item_tags = {t: 1 for t in raw_tags}
        else:
            item_tags = {}

        for t in tags: 
            if t not in [material, quality, "level"]:
                item_tags[t] = item_tags.get(t, 0) + 1
        
        # Apply Material Tags
        if mat_config:
            for k, v in mat_config.get("tags", {}).items():
                item_tags[k] = item_tags.get(k, 0) + v

        if template.get("type") == "weapon":
            dice_offset = tier_config.get("dice_offset", 0) + mat_config.get("dice_offset", 0)
            idx = template.get("base_dice_index", 1) + dice_offset
            idx = max(0, min(len(loot_factory.DICE_LADDER)-1, idx))
            dice = loot_factory.DICE_LADDER[idx]
            
            item = Weapon(
                name=full_name,
                description=f"[GCR {cr}] {template.get('desc', 'A custom weapon.')}",
                damage_dice=dice,
                tags=item_tags,
                value=int(cr * 100)
            )
        else:
            base_def = template.get("base_defense", 5)
            defense = int(base_def * tier_config.get("mult", 1.0) * mat_config.get("mult", 1.0))
            # CR-based breakthrough scaling
            defense = int(defense * (1 + (cr * 0.1)))
            
            item = Armor(
                name=full_name,
                description=f"[GCR {cr}] {template['desc']}",
                defense=defense,
                tags=item_tags,
                value=int(cr * 100)
            )

        # 5. Finalize Attributes
        item.slot = str(template.get('slot', 'none'))
        item.material = material
        item.combat_rating = cr
        item.power = tier_config.get("mult", 1.0) # Legacy
        
        # Weight Class Calculation
        final_weight = int(template.get("base_weight", 5) * mat_config.get("weight_mult", 1.0))
        item.weight = final_weight
        
        if final_weight <= calibration.ScalingRules.WEIGHT_LIGHT_MAX:
            item.weight_class = "light"
        elif final_weight <= calibration.ScalingRules.WEIGHT_MEDIUM_MAX:
            item.weight_class = "medium"
        else:
            item.weight_class = "heavy"
        
        item.prototype_id = f"gen_{full_name.lower().replace(' ', '_')}_{int(cr)}"
        
        return item
