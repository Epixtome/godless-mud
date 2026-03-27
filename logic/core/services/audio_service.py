import logging
from logic.core import event_engine
from logic.core.services import ui_service

logger = logging.getLogger("GodlessMUD")

def initialize_audio_hooks():
    """Subscribes the Audio Service to core game events."""
    event_engine.subscribe("on_enter_room", handle_movement_audio)
    logger.info("Spatial Audio Service Initialized.")

def handle_movement_audio(context):
    """
    Dispatches footstep sounds to nearby observers when an entity moves.
    """
    entity = context.get('entity')
    target_room = context.get('room')
    
    if not entity or not target_room:
        return

    # 1. Who hears this? (All players in the destination room and surrounding tactical radius)
    game = getattr(entity, 'game', None)
    if not game:
        return

    # For now, we only notify players in the same room to keep it simple and high-impact
    for player in target_room.players:
        if player == entity:
            # Self-footstep (Static center)
            ui_service.send_audio_event(player, 'footstep', player.room.x, player.room.y, player.room.z, intensity=0.6)
        else:
            # Observer-footstep (Spatial)
            ui_service.send_audio_event(player, 'footstep', entity.room.x, entity.room.y, entity.room.z, intensity=0.4)

import time

_LAST_COMBAT_SOUND_TIME = {}

def trigger_combat_sound(target, sound_id='clash', intensity=1.0):
    """
    Triggers a spatial combat sound for all observers within hearing range.
    V9.5: Proximity-based dispatch (Radius 7) via global player registry.
    """
    if not target.room or not target.room.world or not hasattr(target.room.world, 'game'):
        return

    game = target.room.world.game
    now = time.time()
    
    # [V9.5] Notify all players within hearing distance (Radius 7)
    # The ui_service.send_audio_event already prunes at R7, so we just iterate active players.
    for player in game.players.values():
        if not getattr(player.connection, 'is_web', False):
            continue
            
        # Per-player Throttle (prevent "sound machine gun" effect)
        last_time = _LAST_COMBAT_SOUND_TIME.get(player.name, 0)
        if now - last_time < 0.15: # 150ms lockout
            continue
            
        _LAST_COMBAT_SOUND_TIME[player.name] = now
        ui_service.send_audio_event(
            player, 
            sound_id, 
            target.room.x, 
            target.room.y, 
            target.room.z, 
            intensity=intensity
        )
