import random
import logging
from logic.factories import loot_factory
from models.items import Currency

logger = logging.getLogger("GodlessMUD")

def populate_mob_loot(mob):
    """
    Populates a mob's inventory with loot and currency based on its power level.
    Called during mob instantiation.
    """
    if not mob:
        return
        
    # Determine Tier based on HP/Damage
    # Level is already calculated in Monster.__init__: max_hp / 20
    level = getattr(mob, 'level', 1)
    
    # 1. Generate Currency (Gold)
    # Average gold = level * 10
    gold_amount = int(random.gauss(level * 5, level * 2))
    gold_amount = max(1, gold_amount)
    
    if gold_amount > 0:
        mob.inventory.append(Currency(amount=gold_amount, coin_type="gold"))

    # 2. Roll for Gear
    # Base chance for a piece of gear drops (scales slightly with level)
    gear_chance = 0.10 + (level * 0.01)
    gear_chance = min(0.40, gear_chance) # Cap at 40%
    
    if random.random() < gear_chance:
        # Determine Quality
        # Higher level mobs have better quality chances
        roll = random.random()
        quality = "standard"
        if roll < 0.02 + (level * 0.005):
            quality = "exotic"
        elif roll < 0.15 + (level * 0.01):
            quality = "standard" # standard is default, but we can have 'scrap'
        elif roll < 0.30:
            quality = "scrap"
            
        # Determine Mob Tier for material scaling
        mob_tier = min(4, max(1, int(level / 5) + 1))
        
        item = loot_factory.generate_loot(level=level, quality=quality, mob_tier=mob_tier)
        if item:
            mob.inventory.append(item)
            # logger.debug(f"[LOOT] Generated {item.name} for {mob.name} (Lvl {level})")

    # 3. Roll for Consumables (Potions/Food)
    consumable_chance = 0.20
    if random.random() < consumable_chance:
        # List of potentially dropping consumables (IDs from data/items/consumables.json)
        # We can eventually make this data-driven per mob type.
        consumables = ["wild_berry", "cactus_fruit", "swamp_root", "minor_healing_potion"]
        # Filter by level-ish (simplified)
        choice = random.choice(consumables)
        
        from logic.factories import item_factory
        item = item_factory.create_item(choice, game=mob.game)
        if item:
            mob.inventory.append(item)

def on_mob_spawned(ctx):
    """Event listener for mob_spawned."""
    mob = ctx.get('mob')
    game = ctx.get('game')
    if mob:
        populate_mob_loot(mob)
