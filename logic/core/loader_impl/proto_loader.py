"""
logic/core/loader_impl/proto_loader.py
Handles the instantiation of game entities from JSON prototypes.
"""
import logging
from models import Armor, Weapon, Consumable, Item, Corpse, Monster, Blessing, HelpEntry

logger = logging.getLogger("GodlessMUD")

def load_prototypes(world, data, blessing_data, class_data, kit_data, deity_data, synergy_data, quest_data, status_effect_data, recipe_data, help_data):
    """Injects all prototype data into the world object."""
    world.kits = kit_data
    
    # 1. Items
    for i_data in data.get('items', []):
        i_type = i_data.get('type', 'item')
        if i_type == 'armor':
            world.items[i_data['id']] = Armor.from_dict(i_data)
        elif i_type == 'weapon':
            world.items[i_data['id']] = Weapon.from_dict(i_data)
        elif i_type == 'consumable':
            world.items[i_data['id']] = Consumable.from_dict(i_data)
        elif i_type == 'corpse':
            world.items[i_data['id']] = Corpse.from_dict(i_data)
        else:
            world.items[i_data['id']] = Item.from_dict(i_data)

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
        mob.shouts = m_data.get('shouts', {})
        mob.dialogue = m_data.get('dialogue', {})
        mob.shop_inventory = m_data.get('shop_inventory', [])
        if 'skills' in m_data:
            mob.skills = m_data['skills']

    # 3. Classes
    for c_data in class_data:
        if 'id' in c_data and 'name' in c_data:
            from models import Class
            world.classes[c_data['id']] = Class(**c_data)

    # 4. Blessings (Skills)
    for b_data in blessing_data:
        if 'id' in b_data and 'name' in b_data:
            world.blessings[b_data['id']] = Blessing(**b_data)
            b = world.blessings[b_data['id']]
            if b.description:
                # [V4.5] Description Cleanup: Remove legacy resource mentions if specified
                if b.metadata.get('clean_description', False):
                    for term in ["Concentration", "Mana", "Stamina"]:
                        b.description = b.description.replace(f"Drains {term}", "").replace(term, "").replace(term.lower(), "")
                    b.description = b.description.strip()
                
    # 5. Help Entries
    world.help = [HelpEntry(**h_data) for h_data in help_data if 'title' in h_data and 'body' in h_data]
