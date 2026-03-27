import logging
import json
import asyncio
from utilities.colors import Colors

# Facade Imports (Standard Godless Architecture)
from logic.core import event_engine, effects, combat, resources
from logic.engines.blessings_engine import Auditor
from logic.core.systems.influence_service import InfluenceService

logger = logging.getLogger("GodlessMUD")

def send_ui_update(player, force_map=False):
    """[V9.1 OPTIMIZED] Main UI Synchronization Pulse (Offloaded from Player Model)."""
    if not player or not player.game or not getattr(player.connection, 'is_web', False):
        return

    # 1. Base status and vitals
    send_status_update(player)
    
    # 2. Tactical Perception Layer (Delta-based Optimization)
    try:
        current_coords = (player.room.x, player.room.y, player.room.z) if player.room else (0,0,0)
        last_coords = player.ext_state.get('last_synced_coords')
        
        # Only send map if coordinates changed OR force-requested
        if force_map or current_coords != last_coords:
            from logic.core import perception as vision
            
            tactical = vision.get_perception(player, radius=5, context=vision.TACTICAL)
            if hasattr(tactical, 'to_dict'):
                player.send_json({
                    "type": "map_data",
                    "data": { "context": "map", "perception": tactical.to_dict() }
                })
                # Update persistent sync state
                player.ext_state['last_synced_coords'] = current_coords
    except Exception as e:
        logger.error(f"UI Map Pulse Error: {e}")

def save_ui_prefs(player, prefs):
    """[V9.1] Persists UI layout/preferences to the player model."""
    if not isinstance(prefs, dict):
        return
    player.ext_state['ui_prefs'] = prefs
    logger.debug(f"UI Prefs saved for {player.name}")

def send_status_update(player):
    """Serializes current vitals and environment context as JSON."""
    try:
        weather = player.room.get_weather() if hasattr(player.room, 'get_weather') else "clear"
        pulse = player.game.pulse_count if player.game else 0
        
        # --- ABILITY DECK (Equipped Blessings with GCA status) ---
        blessings = []
        for b_id in player.equipped_blessings:
            b = player.game.world.blessings.get(b_id)
            if b:
                # Resolve GCA Attributes (Dict/Object Support)
                b_name = b.get('name', b_id) if isinstance(b, dict) else getattr(b, 'name', b_id)
                b_type = b.get('logic_type', 'skill') if isinstance(b, dict) else getattr(b, 'logic_type', 'skill')
                b_tags = b.get('identity_tags', []) if isinstance(b, dict) else getattr(b, 'identity_tags', [])
                
                # Cooldown Readiness
                cooldown_ready = player.cooldowns.get(b_id, 0) <= pulse
                
                # Situational Requirements
                reqs = b.get('requirements', {}) if isinstance(b, dict) else getattr(b, 'requirements', {})
                fighting_ready = True
                if reqs.get('fighting') is True and not player.fighting:
                    fighting_ready = False
                
                # Dynamic Resource Check (Auditor Logic)
                resource_ready = True
                costs = Auditor.calculate_costs(b, player)
                for res_name, cost_val in costs.items():
                    if player.resources.get(res_name, 0) < cost_val:
                        resource_ready = False
                        break
                
                ready = cooldown_ready and resource_ready and fighting_ready

                # Combo/Setup Readiness (Status Interactions)
                setup_ready = False
                p_rules = b.get('potency_rules', []) if isinstance(b, dict) else getattr(b, 'potency_rules', [])
                for rule in p_rules:
                    if rule.get('type') == 'status_mod':
                        status_id = rule.get('status_id')
                        check_target = rule.get('check_target', False)
                        target_obj = player.fighting if check_target else player
                        if target_obj and effects.has_effect(target_obj, status_id):
                            setup_ready = True
                            break
                
                blessings.append({
                    "id": b_id, 
                    "name": b_name,
                    "type": b_type,
                    "tags": b_tags,
                    "ready": ready,
                    "setup_ready": setup_ready, # UI indicator
                    "cooldown": max(0, player.cooldowns.get(b_id, 0) - pulse),
                    "cost": b.get('cost', 0) if isinstance(b, dict) else getattr(b, 'cost', 0),
                    "resource_name": b.get('resource_name', 'SP') if isinstance(b, dict) else getattr(b, 'resource_name', 'SP')
                })

        cycle = (player.game.tick_count if player.game else 0) % 300
        if cycle < 75: time_label, is_day = "Morning", True
        elif cycle < 150: time_label, is_day = "Day", True
        elif cycle < 225: time_label, is_day = "Evening", False
        else: time_label, is_day = "Night", False

        # --- CLASS RESOURCE MANAGEMENT ---
        from logic.core import resource_registry
        class_res = None
        res_defs = resource_registry.get_resources_for_kit(getattr(player, 'active_class', 'common'))
        if res_defs:
            res = res_defs[0]
            if res.id != 'balance':
                class_res = {
                    "name": res.display_name,
                    "current": player.resources.get(res.id, 0),
                    "max": player.get_max_resource(res.id),
                    "id": res.id
                }

        # --- ROOM CONTENTS (Entities, Objects, Shrines) ---
        entities = []
        if player.room:
            # Players
            for p in getattr(player.room, 'players', []):
                if p == player: continue
                entities.append({
                    "id": str(id(p)), "name": p.name, 
                    "symbol": Colors.strip(getattr(p, 'symbol', '@'))[0], "is_player": True
                })
            
            # Monsters
            for m in getattr(player.room, 'monsters', []):
                entities.append({
                    "id": str(id(m)), "name": m.name, 
                    "symbol": Colors.strip(getattr(m, 'symbol', 'm'))[0],
                    "is_hostile": getattr(m, 'is_aggressive', False)
                })

            # Interactive Items & Objects
            for itm in getattr(player.room, 'items', []):
                entities.append({
                    "id": str(id(itm)),
                    "name": itm.name,
                    "symbol": getattr(itm, 'symbol', 'o')[0],
                    "is_item": True,
                    "type": itm.__class__.__name__.lower()
                })

            # Shrines (Sovereignty Interface)
            for s_id, shrine in InfluenceService.get_instance().shrines.items():
                if shrine.coords == [player.room.x, player.room.y, player.room.z]:
                    entities.append({
                        "id": s_id,
                        "name": shrine.name,
                        "symbol": "\u03a8", # Psi Symbol
                        "is_shrine": True,
                        "kingdom": shrine.captured_by
                    })
        
        # --- ROOM TRAPS ---
        traps = []
        if player.room:
            # Metadata-based traps
            if hasattr(player.room, 'metadata') and 'traps' in player.room.metadata:
                for trap in player.room.metadata['traps']:
                    is_owner = trap.get('owner') == player.name
                    is_assassin = getattr(player, 'active_class', 'unknown') == 'assassin'
                    if is_owner or is_assassin:
                        traps.append({
                            "id": str(id(trap)),
                            "type": trap.get('type', 'spike'),
                            "owner": trap.get('owner', 'unknown'),
                            "is_mine": is_owner
                        })
            
            # Visible trap items
            for itm in getattr(player.room, 'items', []):
                if "trap" in getattr(itm, 'flags', []):
                    traps.append({
                        "id": str(id(itm)),
                        "type": itm.name,
                        "is_mechanism": True
                    })

        # --- INVENTORY & EQUIPMENT ---
        inventory = []
        for itm in player.inventory:
            inventory.append({
                "id": str(id(itm)),
                "name": itm.name,
                "type": itm.__class__.__name__.lower(),
                "symbol": getattr(itm, 'symbol', '?')
            })

        equipment = {
            "weapon": player.equipped_weapon.name if player.equipped_weapon else "Unequipped",
            "armor": player.equipped_armor.name if player.equipped_armor else "Unequipped",
            "offhand": player.equipped_offhand.name if player.equipped_offhand else "Unequipped",
            "head": player.equipped_head.name if player.equipped_head else "Unequipped"
        }

        # --- DISPATCH ---
        player.send_json({
            "type": "status_update",
            "data": {
                "hp": {"current": player.hp, "max": player.max_hp},
                "stamina": {"current": player.resources.get('stamina', 0), "max": player.get_max_resource('stamina')},
                "balance": {"current": player.resources.get('balance', 0), "max": player.get_max_resource('balance')},
                "resource": class_res,
                "target": {
                    "name": player.fighting.name,
                    "hp": {"current": player.fighting.hp, "max": player.fighting.max_hp},
                    "symbol": Colors.strip(getattr(player.fighting, 'symbol', 'm'))[0]
                } if player.fighting else None,
                "blessings": blessings,
                "weather": weather,
                "time": time_label,
                "is_day": is_day,
                "status_effects": [
                    {"id": eid, "name": eid.replace('_', ' ').title(), "duration": max(0, ticks - pulse)}
                    for eid, ticks in player.status_effects.items()
                ],
                "ui_prefs": player.ext_state.get('ui_prefs', {}),
                "inventory": inventory,
                "equipment": equipment,
                "room": {
                    "name": getattr(player.room, 'name', 'Void'),
                    "entities": entities
                }
            }
        })
    except Exception as e:
        logger.error(f"Status Update Error: {e}")
