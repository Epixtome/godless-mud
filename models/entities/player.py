import logging
import time
import json
import os
import asyncio
from datetime import datetime
from models.items import Armor, Weapon, Consumable, Item
from utilities.colors import Colors
from logic.constants import Tags
from logic import calibration
from logic.core import event_engine, effects
from logic.core.utils import persistence, messaging, combat_logic
from logic.engines.resonance_engine import ResonanceAuditor
# No Gender import needed (Legacy)

logger = logging.getLogger("GodlessMUD")

class Player:
    def __init__(self, game, connection, name, start_room):
        self.game = game
        self.connection = connection
        self.name = name
        self.room = start_room
        self.inventory = []
        self.inventory_limit = 20
        self.equipped_armor = None
        self.equipped_weapon = None
        self.equipped_offhand = None
        self.equipped_head = None
        self.hp = 100
        self.fighting = None
        self.attackers = [] # List of entities attacking this player
        self.identity_tags = ["adventurer"]
        self.known_blessings = [] # List of blessing IDs
        self.equipped_blessings = [] # List of equipped blessing IDs (Deck)
        self.blessing_charges = {} # ID -> current charges
        self.blessing_xp = {} # ID -> xp amount
        self.favor = {} # Deity ID -> Amount
        self.daily_favor_gain = 0
        self.last_favor_gain_tick = 0
        self.total_favor_gain = 0 # Lifetime tracking (milestones)
        self.gold = 0
        self.aliases = {}
        self.cooldowns = {} # ID -> tick when ready
        self.pagination_buffer = [] # Lines of text waiting to be displayed
        self._active_class = None
        self.unlocked_classes = []
        self.rest_until = 0
        self.active_quests = {} # {quest_id: {obj_id: progress}}
        self.completed_quests = [] # [quest_id]
        self.password = None
        self.is_admin = False
        self.is_building = False
        self.status_effects = {} # effect_id -> expiry_tick
        self.interaction_context = None # For multi-step interactions
        self.state = "normal" # normal, commune, combat, etc.
        self.is_player = True
        self.minions = [] # List of mobs following this player
        self.friendship = {} # npc_id -> level (0-100)
        self.visited_rooms = [] # List of room IDs (MRU, max 200)
        self.discovered_rooms = [] # List of room IDs (MRU, max 1000) Uncolored Persistent
        self.locked_target = None # For ranged combat (Ranger)
        self.reputation = 0 # -100 to 100. < -10 is Criminal.
        self.kingdom = "instinct" # light, dark, instinct (V6.0 Calibration)
        self.is_mounted = False
        self.admin_vision = False
        self.is_hydrated = False
        self.is_web = getattr(connection, 'is_web', False) # [V7.2] UI Tuning Flag
        
        # UTS Cache (V4.5 Optimization)
        self._cached_tags = {}
        self.tags_are_dirty = True

        self.interaction_data = {}
        self.current_tags = {}
        self.base_concealment = 0
        self.base_perception = 10
        self.current_action = None # Reference to active ActionTask (Action Manager)
        self.last_hit_tick = 0 # Tick when last damage was taken
        self.last_action = "none" # Last command entered
        self.last_action_time = 0 # Timestamp of last action (Hard Floor)
        self.suppress_engine_prompt = False
        self.prompt_requested = False
        self.output_buffer = []
        self.is_buffering = False
        self.active_statuses_display = []
        
        # Modular Socket Architecture
        self.active_kit = {} 
        self.kit_version = 0 # Track which version of the kit is applied
        self.ext_state = {}

        self.trigger_module_inits()

        self.resources = {'heat': 0, 'stamina': 100, 'balance': 100}
        
        # Kinetic Pacing Engine
        self.move_tokens = 5.0
        self.last_refill_time = time.time()
        
        # Add self to starting room
        self.room.players.append(self)
        # Mark start room as visited
        if self.room:
            self.mark_room_visited(self.room.id)

    def mark_room_visited(self, room_id):
        """Adds a room and its immediate neighbors to history via facade."""
        from logic.core.utils import player_logic
        player_logic.mark_room_visited(self, room_id)

    @property
    def id(self):
        """Technical identifier (lowercase name). Not an RPG stat."""
        return self.name.lower()

    @property
    def is_resting(self):
        return self.state == "resting"

    @is_resting.setter
    def is_resting(self, value):
        self.state = "resting" if value else "normal"


    @property
    def active_class(self):
        return self._active_class

    @active_class.setter
    def active_class(self, value):
        if self._active_class != value:
            self._active_class = value
            self.flush_class_state()
            self.trigger_module_inits()

    def flush_class_state(self):
        """Removes class-specific stances via facade."""
        from logic.core.utils import player_logic
        player_logic.flush_class_state(self)

    def trigger_module_inits(self):
        """Initializes state for active modules."""
        persistence.trigger_module_inits(self)
        self.mark_tags_dirty()

    def refresh_tokens(self):
        """Refills movement tokens via facade."""
        from logic.core.utils import player_logic
        player_logic.refresh_tokens(self)

    def to_dict(self):
        """Serializes player state."""
        return persistence.to_dict(self)

    def load_data(self, data):
        """Hydrates player state."""
        persistence.load_data(self, data)
        self.is_hydrated = True

    def is_in_combat(self):
        """Returns True if fighting."""
        return self.fighting is not None

    def load_kit(self, kit_name):
        """Applies a specific class kit."""
        from logic.core.utils import player_logic
        return player_logic.load_kit(self, kit_name)

    def get_class_bonus(self):
        """Returns bonus from current kit."""
        from logic.core.utils import player_logic
        return player_logic.get_class_bonus(self)

    def mark_tags_dirty(self):
        """Invalidates UTS cache."""
        self.tags_are_dirty = True

    def get_global_tag_count(self, tag):
        """Retrieves UTS voltage via facade."""
        if self.tags_are_dirty:
            self._cached_tags = ResonanceAuditor.calculate_resonance(self)
            self.tags_are_dirty = False
        return self._cached_tags.get(tag, 0)

    def get_heat_efficiency(self):
        """Returns heat cost multiplier."""
        from logic.core.utils import player_logic
        return player_logic.get_heat_efficiency(self)

    @property
    def max_hp(self):
        """Returns calculated Max HP."""
        from logic.core.utils import player_logic
        return player_logic.get_max_hp(self)

    def get_max_resource(self, resource_name):
        """Returns max resource via facade."""
        from logic.core.utils import player_logic
        return player_logic.get_max_resource(self, resource_name)

    def reset_resources(self):
        """Resets vitals via facade."""
        from logic.core.utils import player_logic
        player_logic.reset_resources(self)

    def take_damage(self, amount, source=None, context="Combat"):
        """
        [DEPRECATED] Use logic.core.combat.apply_damage instead.
        Applies damage to the player via the combat facade.
        """
        from logic.core import combat
        return combat.apply_damage(self, amount, source=source, context=context)

    def stop_combat(self):
        """Clears combat state."""
        combat_logic.stop_combat(self)

    def get_defense(self):
        """Calculates total defense from Armor + Buffs."""
        return combat_logic.get_total_defense(self)

    @property
    def concealment(self):
        return self.base_concealment

    @concealment.setter
    def concealment(self, value):
        self.base_concealment = value

    @property
    def perception(self):
        return self.base_perception

    @perception.setter
    def perception(self, value):
        self.base_perception = value

    def start_buffering(self):
        """Starts buffering output to send in a single packet."""
        self.is_buffering = True
        self.output_buffer = []

    def stop_buffering(self):
        """Flushes the buffer and stops buffering."""
        sent = self.flush()
        self.is_buffering = False
        if sent:
            try:
                self.connection.flush()
            except Exception:
                pass

    def flush(self):
        """Sends all buffered output immediately."""
        return messaging.flush(self)

    def send_line(self, message, include_prompt=False):
        """Standard output entry point."""
        messaging.send_line(self, message, include_prompt=include_prompt)


    def send_raw(self, message, include_prompt=False):
        """Send raw text to this player's telnet client without prefix/suffix."""
        messaging.send_raw(self, message, include_prompt=include_prompt)

    def send_json(self, data):
        """[V8.0] Dispatches a structured event via the GES standard."""
        if self.connection and hasattr(self.connection, 'send_event'):
            # If we're already passing a GES-style dict, unwrap the data
            e_type = data.get('type', 'generic_event')
            e_data = data.get('data', {})
            asyncio.create_task(self.connection.send_event(e_type, e_data))
        elif self.connection and hasattr(self.connection, 'write'):
            # Legacy fallback
            msg = json.dumps(data)
            self.connection.write(msg)

    def send_ui_update(self):
        """[V8.9] Delegates UI synchronization to the UI service."""
        from logic.core.services import ui_service
        ui_service.send_ui_update(self)

    def send_status_update(self):
        """[V8.9] Delegates status synchronization to the UI service."""
        from logic.core.services import ui_service
        ui_service.send_status_update(self)


    def is_buffering_content(self):
        """Returns True if there is text in the output buffer."""
        return len(self.output_buffer) > 0

    def send_prompt(self):
        """Sends the prompt immediately and flushes the buffer."""
        if self.is_web:
            # [V7.2] Web clients receive prompts as structured data.
            # This allows the React client to strip it from the log or update a HUD.
            self.send_json({"type": "prompt", "data": self.get_prompt()})
        else:
            self.send_raw(self.get_prompt())
            
        self.prompt_requested = False
        
        # Force flush if not in a complex command buffer
        # (Heartbeat-based flush will handle this if pulsed)
        if not self.is_buffering:
            try:
                self.connection.flush()
            except Exception:
                pass

    async def drain(self):
        """Flushes the connection's writer."""
        if hasattr(self, 'connection'):
            try:
                await self.connection.drain()
            except Exception:
                pass

    def get_prompt(self):
        """Returns the command prompt string."""
        return messaging.get_prompt(self)

    def save(self):
        """Saves the player data to disk."""
        persistence.save(self)

    def send_paginated(self, text):
        """Queues text for paginated display."""
        lines = text.strip().split('\n')
        self.pagination_buffer = lines
        self.show_next_page()

    def show_next_page(self):
        """Displays the next chunk of text from the buffer."""
        messaging.show_next_page(self)
