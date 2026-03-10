"""
logic/commands/admin/editors/base_editor.py
Shared utilities and constants for the Editor suite.
"""
from logic.common import find_by_index
from logic import search

FIELD_HELP = {
    "name": "Set the item's name.\nUsage: name <new name>",
    "desc": "Set the description.\nUsage: desc <text>",
    "description": "Set the description.\nUsage: description <text>",
    "slot": "Set equipment slot.\nOptions: head, neck, chest, arms, hands, legs, feet, main_hand, off_hand, floating, mount\nUsage: slot <slot>",
    "damage": "Set weapon damage dice.\nUsage: damage <dice> (e.g. 1d6, 2d4+1)",
    "defense": "Set armor defense value.\nUsage: defense <integer>",
    "value": "Set gold value.\nUsage: value <integer>",
    "scaling": "Set tag scaling for weapons.\nUsage: scaling <tag>:<val> ... (e.g. fire:1.0 martial:0.5)",
    "flags": "Set item flags.\nUsage: flags <flag1> <flag2> ... (Overwrite)\n       flags +<flag> -<flag> ... (Modify)\nCommon: portal, nexus, decay, magic, glow, resource, hazard, shield",
    "effects": "Set consumable effects.\nUsage: effects <type>:<val> ... (e.g. hp:20 mana:10)"
}

def _find_item_everywhere(player, name):
    """Helper to find items in inventory, room, or equipment."""
    item = find_by_index(player.inventory, name)
    if not item: item = find_by_index(player.room.items, name)
    if not item: item = search.search_list(player.inventory, name)
    if not item: item = search.search_list(player.room.items, name)
    
    if not item:
        equipped = []
        attrs = ["equipped_weapon", "equipped_offhand", "equipped_armor", 
                 "equipped_head", "equipped_neck", "equipped_arms", 
                 "equipped_hands", "equipped_legs", "equipped_feet", 
                 "equipped_floating", "equipped_mount"]
        for attr in attrs:
            it = getattr(player, attr, None)
            if it: equipped.append(it)
        item = search.search_list(equipped, name)
    return item

def _find_mob_everywhere(player, name):
    mob = find_by_index(player.room.monsters, name)
    if not mob: mob = search.search_list(player.room.monsters, name)
    return mob
