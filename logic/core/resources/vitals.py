"""
logic/core/resources/vitals.py
Pillar 1: Core Vital Resource Engines.
"""
def update_max_hp(entity):
    """
    Recalculates Max HP based on Base + Gear Bonus.
    """
    if not hasattr(entity, 'equipped_armor'): return
    
    base_hp = 100 # Standard Base HP
    bonus = 0
    
    slots = ["equipped_armor", "equipped_head", "equipped_neck", "equipped_arms", "equipped_hands", "equipped_legs", "equipped_feet", "equipped_offhand"]
    for slot in slots:
        item = getattr(entity, slot, None)
        if item:
            bonus += getattr(item, 'bonus_hp', 0)
            
    entity._max_hp = base_hp + bonus
    entity.hp = min(entity.hp, entity.max_hp)
