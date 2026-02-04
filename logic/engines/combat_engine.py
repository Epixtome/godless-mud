import random
from utilities.utils import roll_dice

def calculate_player_damage(player):
    """Calculates damage for a player's auto-attack."""
    damage = 0
    if player.equipped_weapon:
        base = roll_dice(player.equipped_weapon.damage_dice) or 1
        
        scaling_bonus = 0
        if player.equipped_weapon.scaling:
            for stat, multiplier in player.equipped_weapon.scaling.items():
                scaling_bonus += player.get_stat(stat) * multiplier
        
        damage = int(base + scaling_bonus)
    else:
        # Unarmed: 1 + STR * 0.2
        damage = 1 + int(player.get_stat('str') * 0.2)
    
    # --- Passive Bonuses ---
    if player.active_class:
        cls = player.game.world.classes.get(player.active_class)
        if cls and cls.bonuses and 'passive' in cls.bonuses:
            passive = cls.bonuses['passive']
            
            # Warrior: "Weapon damage increased by 10%."
            if "Weapon damage increased" in passive and player.equipped_weapon:
                damage = int(damage * 1.10)
                
            # Barbarian: "Damage increases as HP decreases."
            if "Damage increases as HP decreases" in passive:
                missing_hp_pct = 1.0 - (player.hp / player.max_hp)
                # Up to 50% bonus damage at 0 HP
                bonus_mult = 1.0 + (missing_hp_pct * 0.5)
                damage = int(damage * bonus_mult)
    
    # --- Status Effects ---
    if hasattr(player, 'status_effects'):
        if "berserk_rage" in player.status_effects:
            damage = int(damage * 1.25) # 25% Damage Bonus
                
    return max(1, damage)

def estimate_player_damage(player):
    """Estimates average damage for the consider command."""
    if player.equipped_weapon:
        try:
            dice_count, dice_sides = map(int, player.equipped_weapon.damage_dice.split('d'))
            avg_base = dice_count * (dice_sides + 1) / 2
        except (ValueError, AttributeError):
            avg_base = 1
            
        scaling_bonus = 0
        if player.equipped_weapon.scaling:
            for stat, multiplier in player.equipped_weapon.scaling.items():
                scaling_bonus += player.get_stat(stat) * multiplier
        return int(avg_base + scaling_bonus)
    else:
        return 1 + int(player.get_stat('str') * 0.2)

def calculate_mob_damage(mob, target):
    """Calculates damage dealt by a mob to a player."""
    raw = mob.damage
    defense = 0
    if hasattr(target, 'get_defense'):
        defense = target.get_defense()
    elif hasattr(target, 'equipped_armor') and target.equipped_armor:
        defense = target.equipped_armor.defense
        
    damage = max(1, raw - defense)
    
    # Beast Master Passive: Companions deal 20% more damage
    if mob.leader and hasattr(mob.leader, 'active_class') and mob.leader.active_class == 'beast_master':
        # Check for passive string or just assume class ID implies it for performance
        damage = int(damage * 1.20)
        
    return damage

def distribute_favor(player, target, game):
    """Awards favor to the player based on the kill."""
    tags = getattr(target, 'tags', [])
    if not tags and hasattr(target, 'identity_tags'):
        tags = target.identity_tags

    base_favor = 10
    if "avatar" in tags:
        base_favor = 100

    awarded_deities = []
    
    # Helper: Find opposing deity by stat
    def get_opposing(deity_obj, target_kingdom):
        candidates = [d for d in game.world.deities.values() if d.kingdom == target_kingdom and d.stat == deity_obj.stat]
        if candidates: return candidates[0]
        return None

    # Check for specific deity tags in mob to find direct opposition
    mob_deity = None
    for tag in tags:
        if tag in game.world.deities:
            mob_deity = game.world.deities[tag]
            break
    
    if mob_deity:
        # Direct opposition logic
        target_k = "light" if mob_deity.kingdom == "dark" else "dark"
        if mob_deity.kingdom == "instinct": target_k = "light" # Instinct vs Light (Order)
        
        opposing = get_opposing(mob_deity, target_k)
        if opposing:
            awarded_deities.append(opposing)
    else:
        # General kingdom opposition
        target_k = None
        if "dark" in tags: target_k = "light"
        elif "light" in tags: target_k = "dark"
        elif "instinct" in tags: target_k = "light"
        
        if target_k:
            candidates = [d for d in game.world.deities.values() if d.kingdom == target_k]
            if candidates:
                awarded_deities.append(random.choice(candidates))

    for d in awarded_deities:
        player.favor[d.id] = player.favor.get(d.id, 0) + base_favor
        player.send_line(f"You gain {base_favor} Favor with {d.name}.")

def validate_target(attacker, target):
    """
    Centralized check to see if a target is valid for combat.
    Returns True if valid, False otherwise.
    """
    if not target: return False
    if target.hp <= 0: return False
    if target.room != attacker.room: return False
    return True