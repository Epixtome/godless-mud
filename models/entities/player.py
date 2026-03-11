import logging
import time
import json
import os
from models.items import Armor, Weapon, Consumable, Item
from utilities.colors import Colors
from logic.constants import Tags
from logic import calibration
from logic.core import event_engine, effects
from logic.core.utils import persistence, messaging, combat_logic
from logic.engines.resonance_engine import ResonanceAuditor

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
        self.visited_rooms = set() # Set of room IDs visited
        self.locked_target = None # For ranged combat (Ranger)
        self.reputation = 0 # -100 to 100. < -10 is Criminal.
        self.is_mounted = False
        self.admin_vision = False
        
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
        self.ext_state = {}

        self.trigger_module_inits()

        self.resources = {'heat': 0, 'stamina': 100}
        
        # Kinetic Pacing Engine
        self.move_tokens = 5.0
        self.last_refill_time = time.time()
        
        # Add self to starting room
        self.room.players.append(self)
        # Mark start room as visited
        if self.room:
            self.visited_rooms.add(self.room.id)

    @property
    def id(self):
        """Technical identifier (lowercase name). Not an RPG stat."""
        return self.name.lower()

    @property
    def is_resting(self):
        """Returns True if the player is in the 'resting' state."""
        return self.state == "resting"

    @is_resting.setter
    def is_resting(self, value):
        if value:
            self.state = "resting"
        else:
            if self.state == "resting":
                self.state = "normal"


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
        """Removes class-specific stances and passives."""
        
        # Identify effects to remove
        to_remove = []
        if self.status_effects:
            for eff_id in self.status_effects:
                eff_def = effects.get_effect_definition(eff_id, self.game)
                if eff_def and eff_def.get('group') in ['stance', 'class_passive']:
                    to_remove.append(eff_id)
        
        for eff in to_remove:
            effects.remove_effect(self, eff)

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

    def is_in_combat(self):
        """Returns True if fighting."""
        return self.fighting is not None

    def load_kit(self, kit_name):
        """Applies a specific class kit."""
        success = persistence.load_kit(self, kit_name)
        if success: self.mark_tags_dirty()
        return success

    def get_class_bonus(self):
        """Returns bonus from current kit."""
        return self.active_kit.get('class_bonus', 0)

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
        return self.active_kit.get('heat_efficiency', 1.0)

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

    @property
    def perception(self):
        return self.base_perception

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

    def get_class_module(self):
        """[DEPRECATED] Use logic.core.class_service.get_class_module instead."""
        from logic.core import class_service
        return class_service.get_class_module(self.active_class)

    def send_raw(self, message, include_prompt=False):
        """Send raw text to this player's telnet client without prefix/suffix."""
        messaging.send_raw(self, message, include_prompt=include_prompt)

    def is_buffering_content(self):
        """Returns True if there is text in the output buffer."""
        return len(self.output_buffer) > 0

    def send_prompt(self):
        """Sends the prompt immediately and flushes the buffer."""
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
        """Flushes the connection's writer. (Telnet Protocol)"""
        if hasattr(self, 'connection') and hasattr(self.connection, 'writer'):
            try:
                await self.connection.writer.drain()
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
