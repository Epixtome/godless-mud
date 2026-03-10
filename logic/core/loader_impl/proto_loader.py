"""
logic/core/loader_impl/proto_loader.py
Handles the instantiation of game entities from JSON prototypes.
"""
import logging
from models import Armor, Weapon, Consumable, Item, Corpse, Monster, Blessing

logger = logging.getLogger("GodlessMUD")

def load_prototypes(world, data, blessing_data, class_data, kit_data, deity_data, synergy_data, quest_data, status_effect_data, recipe_data, help_data):
    """Injects all prototype data into the world object."""
    world.kits = kit_data
    
    # 1. Items
    for i_data in data.get('items', []):
        tags = i_data.get('tags') or i_data.get('gear_tags')
        i_type = i_data.get('type', 'item')
        if i_type == 'armor':
            armor = Armor(i_data['name'], i_data['description'], i_data.get('defense', 0), value=i_data.get('value', 10), flags=i_data.get('flags'), prototype_id=i_data['id'], tags=tags)
            armor.bonus_hp = i_data.get('bonus_hp', 0)
            world.items[i_data['id']] = armor
        elif i_type == 'weapon':
            stats = i_data.get('stats', {})
            damage_dice = stats.get('damage_dice') if stats else i_data.get('damage_dice', '1d4')
            world.items[i_data['id']] = Weapon(i_data['name'], i_data['description'], damage_dice, i_data.get('scaling', {}), value=i_data.get('value', 10), flags=i_data.get('flags'), prototype_id=i_data['id'], tags=tags)
        elif i_type == 'consumable':
            world.items[i_data['id']] = Consumable(i_data['name'], i_data['description'], i_data['effects'], value=i_data.get('value', 5), flags=i_data.get('flags'), prototype_id=i_data['id'], tags=tags)
        elif i_type == 'corpse':
            world.items[i_data['id']] = Corpse(i_data['name'], i_data['description'], [], flags=i_data.get('flags'), tags=tags)
        else:
            world.items[i_data['id']] = Item(i_data['name'], i_data['description'], value=i_data.get('value', 10), flags=i_data.get('flags'), prototype_id=i_data['id'], tags=tags)

    # 2. Monsters
    for m_data in data.get('monsters', []):
        tags = m_data.get('tags', [])
        mob = Monster(m_data['name'], m_data['description'], m_data['hp'], m_data['damage'], tags, m_data.get('max_hp'), prototype_id=m_data['id'])
        world.monsters[m_data['id']] = mob
        
        # GCA Class Hook
        for tag in tags:
            if tag.startswith("class:"):
                mob.active_class = tag.split(":")[1]
                mob.refresh_class()
                kit = world.kits.get(mob.active_class, {})
                for b_id in kit.get('blessings', []):
                    if b_id not in mob.skills: mob.skills.append(b_id)
                break
        
        # Advanced Mechanics
        mob.quests = m_data.get('quests', [])
        mob.vulnerabilities = m_data.get('vulnerabilities', {})
        mob.states = m_data.get('states', {})
        mob.triggers = m_data.get('triggers', [])
        mob.current_state = m_data.get('current_state', 'normal')
        mob.loadout = m_data.get('loadout', [])

    # 3. Blessings (Skills)
    for b_data in blessing_data:
        if 'id' in b_data and 'name' in b_data:
            world.blessings[b_data['id']] = Blessing(**b_data)
            b = world.blessings[b_data['id']]
            if b.description:
                for term in ["Concentration", "Mana", "Stamina"]:
                    b.description = b.description.replace(f"Drains {term}", "").replace(term, "").replace(term.lower(), "")
                b.description = b.description.strip()
