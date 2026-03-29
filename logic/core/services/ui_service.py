import logging
import json
import asyncio
from utilities.colors import Colors

# Facade Imports (Standard Godless Architecture)
from logic.core import event_engine, effects, combat, resources
from logic.engines.blessings_engine import Auditor
from logic.core.systems.influence_service import InfluenceService
from logic.core import perception as vision

# [V9.7 ZERO-LAG TRIGGER] Ref-self for command bridge
from logic.core.services import ui_service 

logger = logging.getLogger("GodlessMUD")

def send_ui_update(player, force_map=False):
    """[V9.7 OPTIMIZED] Main UI Synchronization Pulse (No-Lag Mode)."""
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
            # [V9.7 PARITY FIX] Dynamic Radius matching backend MAP command
            elev = getattr(player.room, 'elevation', 0)
            target_radius = 7 + elev
            final_radius = max(2, min(15, target_radius))
            
            tactical = vision.get_perception(player, radius=final_radius, context=vision.TACTICAL)
            if hasattr(tactical, 'to_dict'):
                perc_dict = tactical.to_dict()
                # [V9.7 FIX] Use the ACTUAL radius from the vision engine (respecting weather/penalties)
                perc_dict['current_radius'] = tactical.radius 
                player.send_json({
                    "type": "map_data",
                    "data": { "context": "map", "perception": perc_dict }
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

def send_audio_event(player, sound_id, x, y, z, intensity=1.0):
    if not player or not getattr(player.connection, 'is_web', False):
        return
    rel_x = x - player.room.x if player.room else 0
    rel_y = y - player.room.y if player.room else 0
    if abs(rel_x) > 7 or abs(rel_y) > 7:
        return
    player.send_json({
        "type": "audio:event",
        "data": {"id": sound_id, "rel_x": rel_x, "rel_y": rel_y, "intensity": intensity}
    })

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
                b_name = b.get('name', b_id) if isinstance(b, dict) else getattr(b, 'name', b_id)
                b_type = b.get('logic_type', 'skill') if isinstance(b, dict) else getattr(b, 'logic_type', 'skill')
                b_tags = b.get('identity_tags', []) if isinstance(b, dict) else getattr(b, 'identity_tags', [])
                cooldown_ready = player.cooldowns.get(b_id, 0) <= pulse
                reqs = b.get('requirements', {}) if isinstance(b, dict) else getattr(b, 'requirements', {})
                fighting_ready = True
                if reqs.get('fighting') is True and not player.fighting:
                    fighting_ready = False
                resource_ready = True
                costs = Auditor.calculate_costs(b, player)
                for res_name, cost_val in costs.items():
                    if player.resources.get(res_name, 0) < cost_val:
                        resource_ready = False
                        break
                ready = cooldown_ready and resource_ready and fighting_ready
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
                    "id": b_id, "name": b_name, "type": b_type, "tags": b_tags,
                    "ready": ready, "setup_ready": setup_ready, 
                    "cooldown": max(0, player.cooldowns.get(b_id, 0) - pulse),
                    "cost": b.get('cost', 0) if isinstance(b, dict) else getattr(b, 'cost', 0),
                    "resource_name": b.get('resource_name', 'SP') if isinstance(b, dict) else getattr(b, 'resource_name', 'SP')
                })

        cycle = (player.game.tick_count if player.game else 0) % 300
        if cycle < 75: time_label, is_day = "Morning", True
        elif cycle < 150: time_label, is_day = "Day", True
        elif cycle < 225: time_label, is_day = "Evening", False
        else: time_label, is_day = "Night", False

        from logic.core import resource_registry
        class_res = None
        res_defs = resource_registry.get_resources_for_kit(getattr(player, 'active_class', 'common'))
        if res_defs:
            res = res_defs[0]
            if res.id != 'balance':
                class_res = {"name": res.display_name, "current": player.resources.get(res.id, 0), "max": player.get_max_resource(res.id), "id": res.id}

        entities = []
        if player.room:
            for p in getattr(player.room, 'players', []):
                if p == player: continue
                entities.append({"id": str(id(p)), "name": p.name, "symbol": Colors.strip(getattr(p, 'symbol', '@'))[0], "is_player": True})
            for m in getattr(player.room, 'monsters', []):
                can_see = vision.can_see(player, m)
                in_combat = (m.fighting is not None)
                is_aggressive = getattr(m, 'is_aggressive', False)
                if can_see or in_combat or is_aggressive:
                    symbol = Colors.strip(getattr(m, 'symbol', 'm'))[0]
                    name = m.name if can_see else "Something"
                    if not can_see and in_combat: symbol = "?"
                    entities.append({"id": str(id(m)), "name": name, "symbol": symbol, "is_hostile": is_aggressive, "in_combat": in_combat})

        inventory = []
        for itm in player.inventory:
            inventory.append({"id": str(id(itm)), "name": itm.name, "type": itm.__class__.__name__.lower(), "symbol": getattr(itm, 'symbol', '?')})

        equipment = {
            "weapon": player.equipped_weapon.name if player.equipped_weapon else "Unequipped",
            "armor": player.equipped_armor.name if player.equipped_armor else "Unequipped",
            "offhand": player.equipped_offhand.name if player.equipped_offhand else "Unequipped",
            "head": player.equipped_head.name if player.equipped_head else "Unequipped"
        }

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
                "blessings": blessings, "weather": weather, "time": time_label, "is_day": is_day,
                "status_effects": [{"id": eid, "name": eid.replace('_', ' ').title(), "duration": 0} for eid in player.status_effects.keys()],
                "ui_prefs": player.ext_state.get('ui_prefs', {}),
                "inventory": inventory, "equipment": equipment,
                "room": {"name": getattr(player.room, 'name', 'Void'), "entities": entities}
            }
        })
    except Exception as e:
        logger.error(f"Status Update Error: {e}")
