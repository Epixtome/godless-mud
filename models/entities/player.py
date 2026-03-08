import logging
import time
import json
import os
from models.items import Armor, Weapon, Consumable, Item
from utilities.colors import Colors
from logic.constants import Tags
from logic import calibration

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
        self.minions = [] # List of mobs following this player
        self.friendship = {} # npc_id -> level (0-100)
        self.visited_rooms = set() # Set of room IDs visited
        self.locked_target = None # For ranged combat (Ranger)
        self.reputation = 0 # -100 to 100. < -10 is Criminal.
        self.is_mounted = False
        self.is_resting = False
        self.admin_vision = False
        self.base_concealment = 0
        self.base_perception = 10
        self.current_action = None # Reference to active ActionTask (Action Manager)
        self.last_hit_tick = 0 # Tick when last damage was taken
        self.last_action = "none" # Last command entered
        self.last_action_time = 0 # Timestamp of last action (Hard Floor)
        self.suppress_engine_prompt = False
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
        from logic.core import status_effects_engine
        
        # Identify effects to remove
        to_remove = []
        if self.status_effects:
            for eff_id in self.status_effects:
                eff_def = status_effects_engine.get_effect_definition(eff_id, self.game)
                if eff_def and eff_def.get('group') in ['stance', 'class_passive']:
                    to_remove.append(eff_id)
        
        for eff in to_remove:
            status_effects_engine.remove_effect(self, eff)

    def trigger_module_inits(self):
        """Initializes state for all active modules."""
        from logic.core.utils import persistence
        persistence.trigger_module_inits(self)

    def refresh_tokens(self):
        """Refills movement tokens based on time elapsed."""
        current_time = time.time()
        delta = current_time - self.last_refill_time
        
        REFILL_RATE = 4.0 # Comfortable Walk Speed
        self.move_tokens = min(5.0, self.move_tokens + (delta * REFILL_RATE))
        self.last_refill_time = current_time

    def to_dict(self):
        """Serializes player state to a dictionary."""
        from logic.core.utils import persistence
        return persistence.to_dict(self)

    def load_data(self, data):
        """Hydrates player state from a dictionary."""
        from logic.core.utils import persistence
        persistence.load_data(self, data)

    def is_in_combat(self):
        """Returns True if the player is currently in a fight."""
        return self.fighting is not None

    def load_kit(self, kit_name):
        """Loads a kit from data/kits.json and applies it."""
        from logic.core.utils import persistence
        return persistence.load_kit(self, kit_name)

    def get_class_bonus(self):
        """
        Returns a flat bonus based on the current kit.
        """
        kit_name = self.active_kit.get('name', '').lower()
        return self.active_kit.get('class_bonus', 0)

    def get_global_tag_count(self, tag):
        """
        Retrieves the total tag count (Voltage) for a specific tag.
        Wrapper for ResonanceAuditor to maintain compatibility.
        """
        # Inline import to prevent circular dependency
        from logic.engines.resonance_engine import ResonanceAuditor
        return ResonanceAuditor.get_voltage(self, tag)

    def get_heat_efficiency(self):
        """Returns heat cost multiplier based on kit."""
        return self.active_kit.get('heat_efficiency', 1.0)

    @property
    def max_hp(self):
        """Calculates Max HP."""
        kit_name = self.active_kit.get('name', '').lower()
        if kit_name == 'wanderer':
            return 150
        return calibration.MaxValues.HP

    def get_max_resource(self, resource_name):
        """Calculates max resource value."""
        if resource_name == 'chi': 
            return self.active_kit.get('max_chi', 5)
        
        if resource_name == Tags.HEAT:
            return self.active_kit.get('max_heat', 100)
                
        return 100

    def reset_resources(self):
        """Fully restores and resets all resources to base state."""
        self.hp = self.max_hp
        if 'concentration' in self.resources:
            self.resources['concentration'] = self.get_max_resource('concentration')
        if Tags.HEAT in self.resources:
            self.resources[Tags.HEAT] = 0
        if 'stability' in self.resources:
            self.resources['stability'] = self.get_max_resource('stability')
        if 'chi' in self.resources:
            self.resources['chi'] = 0
        if 'stamina' in self.resources:
            self.resources['stamina'] = self.get_max_resource('stamina')
        
        self.send_line(f"{Colors.CYAN}Your vitals and resources have been reset.{Colors.RESET}")

    def take_damage(self, amount, source=None, context="Combat"):
        """
        Applies damage to the player and dispatches events.
        """
        from logic.core import event_engine
        
        # Dispatch Pre-Damage (For shielding/reduction)
        ctx = {'target': self, 'damage': amount, 'source': source, 'context': context}
        event_engine.dispatch("on_take_damage", ctx)
        
        actual_damage = ctx['damage']
        self.hp = max(0, self.hp - actual_damage)
        
        if self.hp <= 0:
            from logic.engines import combat_lifecycle
            combat_lifecycle.handle_death(self.game, self, source)

        return actual_damage

    def stop_combat(self):
        """Clears combat state."""
        from logic.core.utils import combat_logic
        combat_logic.stop_combat(self)

    def get_defense(self):
        """Calculates total defense from Armor + Buffs."""
        from logic.core.utils import combat_logic
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
        from logic.core.utils import messaging
        sent = self.flush()
        self.is_buffering = False
        if sent:
            try:
                self.connection.flush()
            except Exception:
                pass

    def flush(self):
        """Sends all buffered output immediately."""
        from logic.core.utils import messaging
        return messaging.flush(self)

    def send_line(self, message, include_prompt=False):
        """Send text to this player's telnet client."""
        self.send_raw(f"\r\n{message}", include_prompt=include_prompt)

    def send_raw(self, message, include_prompt=False):
        """Send raw text to this player's telnet client without prefix/suffix."""
        from logic.core.utils import messaging
        messaging.send_raw(self, message, include_prompt=include_prompt)

    def send_prompt(self):
        """Sends the prompt immediately."""
        self.send_line(self.get_prompt())
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
        from logic.core.utils import messaging
        return messaging.get_prompt(self)

    def save(self):
        """Saves the player data to disk."""
        from logic.core.utils import persistence
        persistence.save(self)

    def send_paginated(self, text):
        """Queues text for paginated display."""
        lines = text.strip().split('\n')
        self.pagination_buffer = lines
        self.show_next_page()

    def show_next_page(self):
        """Displays the next chunk of text from the buffer."""
        from logic.core.utils import messaging
        messaging.show_next_page(self)
