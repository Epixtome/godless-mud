#@spawn, @search
import json
import os
import logic.handlers.command_manager as command_manager
from models import Monster, Item
from utilities.colors import Colors

@command_manager.register("@spawn", admin=True, category="admin_entities")
def spawn(player, args):
    """
    Spawn a monster or item (V6.0 Unified Factory).
    
    [Standard Spawning]
      @spawn <proto_id> [count]
      Examples: @spawn goblin | @spawn iron_sword 3
    
    [Dynamic Generation]
      @spawn new [CR] [tags...] <base_type>
      
      CR (Combat Rating): 1-100 (determines stats/potency)
      
      Valid Elements: fire, frost, ice, lightning, shock, venom, poison, shadow, void, holy, unholy, arcane, entropy
      Valid Traits:   brutal, keen, sturdy, agile, thick, exotic, mythic, scrap, rusty, sharp, jagged, serrated, holy, cursed
      Valid Materials: iron, steel, adamant, mithril, leather, silk, cloth, wood, bone, obsidian
      
      Base Types:
          - Weapons: sword, axe, mace, dagger, staff, hammer, maul, bow, knuckles, wraps, whip, scythe, spear, rapier
          - Armor: chestplate, helm, boots, leggings, gloves, bracers, shield, robes, tunic, cloak, hat, cap, gauntlets
          - Mobs: goblin, wolf, rat, warrior, mage, demon, gargoyle, skeleton, zombie, undead, entity, dragon, bandit, guard
          
      Examples:
        @spawn new 10 fire goblin
        @spawn new 5 mythic steel sword
        @spawn new level 15 shadow demon
    """
    if not args:
        player.send_line(spawn.__doc__)
        return

    parts = args.split()
    
    # --- [V6.0] Dynamic Factory Integration ---
    if parts[0].lower() == "new":
        from logic.factories.dynamic_factory import DynamicFactory
        from logic.core.services import world_service
        
        try:
            # Parse: [new] [level] [CR] [tags...] [type]
            # Handle both "@spawn new 5 goblin" and "@spawn new level 5 goblin"
            has_level_word = len(parts) > 1 and parts[1].lower() == "level"
            cr_index = 2 if has_level_word else 1
            
            if len(parts) <= cr_index:
                raise IndexError("Missing CR/Level value.")

            cr = float(parts[cr_index])
            
            # The remaining parts are tags and the base type (last word)
            remaining = parts[cr_index+1:]
            if not remaining:
                base_type = "entity"
                tags = []
            else:
                base_type = remaining[-1]
                tags = remaining[:-1] if len(remaining) > 1 else []
            
            # Determine if it's a Mob or Gear
            # Gear types list for factory routing
            gear_types = ["sword", "axe", "mace", "dagger", "hammer", "bow", "staff", "knuckles", "wraps", "whip",
                          "helmet", "chestplate", "boots", "gloves", "plate", "mail", "shield", "robes", "tunic", "vest", "cloak",
                          "gauntlets", "bracers", "pauldrons", "greaves", "trousers", "jerkin", "hat", "cap", "ring", "pendant", "amulet", "necklace", "belt", "sash",
                          "leggings", "bracers"]
            
            if base_type.lower() in gear_types:
                weapon_bases = ["sword", "axe", "mace", "dagger", "hammer", "bow", "staff", "knuckles", "wraps", "whip"]
                slot = "weapon" if base_type.lower() in weapon_bases else "armor"
                entity = DynamicFactory.generate_gear(cr, tags, base_type, slot, game=player.game)
                world_service.register_dynamic_prototype(player.game, entity)
                world_service.spawn_item(player.game, entity.prototype_id, player)
                player.send_line(f"{Colors.CYAN}[FACTORY] {entity.name} (Lvl {cr}) shimmers into existence in your inventory.{Colors.RESET}")
                player.send_line(f"{Colors.DGREY}[PROTOTYPE: {entity.prototype_id}]{Colors.RESET}")
            else:
                entity = DynamicFactory.generate_mob(cr, tags, base_type, game=player.game)
                world_service.register_dynamic_prototype(player.game, entity)
                world_service.spawn_monster(player.game, entity.prototype_id, player.room)
                player.room.broadcast(f"{Colors.YELLOW}{player.name} summons a dynamic {entity.name} (CR {cr}) into existence!{Colors.RESET}", exclude_player=player)
                player.send_line(f"{Colors.GREEN}[FACTORY] Dynamically generated CR {cr} {entity.name}! (ID: {entity.prototype_id}){Colors.RESET}")
                
            return
        except (ValueError, IndexError):
            player.send_line(f"{Colors.RED}Factory Syntax Error!{Colors.RESET}")
            player.send_line("Try: @spawn new [level] <CR> [tags] <type>")
            player.send_line("Ex: @spawn new 10 fire goblin")
            return

    # --- Standard Prototype Spawns ---
    count = 1
    if parts[-1].isdigit():
        count = int(parts[-1])
        search_term = " ".join(parts[:-1]).lower()
    else:
        search_term = args.lower()

    # Search Logic
    from logic.core import search
    m_candidates = search.find_matches(player.game.world.monsters.values(), search_term)
    i_candidates = search.find_matches(player.game.world.items.values(), search_term)
    
    matches = []
    for m in m_candidates:
        m_id = getattr(m, 'prototype_id', None) or getattr(m, 'id', 'unknown')
        matches.append(('MOB', m_id, m))
    for i in i_candidates:
        i_id = getattr(i, 'prototype_id', None) or getattr(i, 'id', 'unknown')
        matches.append(('ITEM', i_id, i))

    if not matches:
        player.send_line(f"No mob or item found matching '{args}'.")
    elif len(matches) == 1:
        m_type, m_id, proto = matches[0]
        from logic.core import world_service
        
        if m_type == 'MOB':
            world_service.spawn_monster(player.game, m_id, player.room, count=count)
            player.room.broadcast(f"{player.name} summons {count}x {proto.name}!", exclude_player=player)
        else:
            world_service.spawn_item(player.game, m_id, player, count=count)
            player.send_line(f"You summon {count}x {proto.name} into your inventory.")
        
        player.send_line(f"Spawned {count}x {m_type.lower()}: {proto.name}")
    else:
        player.send_line("\nMultiple matches found. Please specify ID:")
        for m_type, m_id, proto in matches[:10]:
            player.send_line(f"  [{m_type}] {m_id} - {proto.name}")

@command_manager.register("@search", admin=True, category="admin_tools")
def search_db(player, args):
    """Search database for ID/Name."""
    if not args:
        player.send_line("Usage: @search <keyword> | mob <name> | item <name>")
        return
    
    parts = args.split()
    cat = parts[0].lower() if parts[0].lower() in ['mob', 'mobs', 'item', 'items'] else None
    keyword = " ".join(parts[1:]).lower() if cat else args.lower()
    
    matches = []
    if not cat or cat.startswith('mob'):
        for mid, m in player.game.world.monsters.items():
            if keyword in str(mid).lower() or keyword in str(m.name).lower():
                matches.append(f"[MOB] {mid} - {m.name}")
    if not cat or cat.startswith('item'):
        for iid, i in player.game.world.items.items():
            if keyword in str(iid).lower() or keyword in str(i.name).lower():
                matches.append(f"[ITEM] {iid} - {i.name}")

    if matches:
        player.send_paginated("\n".join(sorted(matches)))
    else:
        player.send_line(f"No matches for '{keyword}'.")
