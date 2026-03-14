import logging
from utilities.colors import Colors
from logic.core import event_engine
from logic.core.utils import mob_logic, combat_logic

logger = logging.getLogger("GodlessMUD")

class Monster:
    def __init__(self, name, description, hp, damage, tags=None, max_hp=None, prototype_id=None, home_room_id=None, game=None, base_mitigation=0, loot_table=None):
        self.name = name
        self.game = game
        self.description = description
        self.hp = hp
        self.max_hp = max_hp if max_hp is not None else hp
        self.damage = damage
        self.base_mitigation = base_mitigation
        self.fighting = None
        self.attackers = [] # List of entities attacking this mob
        self.inventory = []
        self.loot_table = loot_table or [] # List of item IDs
        self.loadout = [] # List of item IDs to equip on spawn
        self.equipped_offhand = None # For the Lantern
        self.tags = tags or []
        self.prototype_id = prototype_id
        self.quests = [] # List of quest IDs this mob can give
        self.home_room_id = home_room_id
        self.leader = None # Entity this mob follows
        self.owner_id = None # ID of the player who created this mob
        self.can_be_companion = False # If True, can be recruited via friendship
        self.is_shopkeeper = False
        self.room = None # Reference to the Room object containing this mob
        self.status_effects = {} # effect_id -> expiry_tick
        self.body_parts = {} # name -> {hp, max_hp, defense_bonus, destroyed}
        self.base_concealment = 0
        self.base_perception = 10
        self.current_action = None # Reference to active ActionTask (Action Manager)
        self.skills = [] # List of blessing IDs this mob can use
        self.level = max(1, int(self.max_hp / 20)) # Estimate level from HP
        self.resources = {
            'stamina': 100, 
            'concentration': 100, 
            'heat': 0, 
            'chi': 0, 
            'balance': 20 + (self.level * 5)
        }
        self.active_class = None
        self.cooldowns = {} # ID -> tick when ready
        self.ext_state = {}
        self.shouts = {} # aggro: [], victory: [], etc.
        self.dialogue = {} # node-based conversation data
        self.shop_inventory = [] # List of item IDs for sale
        self.known_blessings = [] # For class logic compatibility
        self.active_kit = {}

        # UTS Cache (V4.5 Optimization)
        self._cached_tags = {}
        self.tags_are_dirty = True

        # Advanced States (Linter Satisfied)
        self.vulnerabilities = {}
        self.states = {}
        self.triggers = []
        self.is_player = False
        self.state = "normal" 
        self.current_state = "normal" # Legacy support

    @property
    def equipped_blessings(self):
        """Standardized access for MathBridge and synergy logic."""
        return self.skills or self.known_blessings
        self.temporary = False
        self.ai_state = "idle"
        self.flags = []

    def refresh_class(self):
        """Initializes class-specific state for the mob via persistence facade."""
        if not self.active_class:
            return
            
        # Ensure we have a dummy kit for compatibility if needed
        if not self.active_kit:
            self.active_kit = {'id': self.active_class}
            
        # Centralized GCA initialization
        from logic.core.utils import persistence
        persistence.trigger_module_inits(self)

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "damage": self.damage,
            "base_mitigation": self.base_mitigation,
            "tags": self.tags,
            "prototype_id": self.prototype_id,
            "home_room_id": self.home_room_id,
            "can_be_companion": self.can_be_companion,
            "loadout": self.loadout,
            "equipped_offhand": self.equipped_offhand.to_dict() if self.equipped_offhand else None,
            "skills": self.skills,
            "loot_table": self.loot_table,
            "is_shopkeeper": self.is_shopkeeper,
            "inventory": [item.to_dict() if hasattr(item, 'to_dict') else item for item in self.inventory]
        }

    def is_in_combat(self):
        """Returns True if the monster is currently in a fight."""
        return self.fighting is not None

    def get_defense(self):
        """Calculates total defense via facade."""
        return mob_logic.get_defense(self)

    def get_damage_modifier(self):
        """Calculates incoming damage multiplier based on body parts."""
        multiplier = 1.0
        for part in self.body_parts.values():
            if part.get('destroyed', False):
                multiplier *= part.get('broken_mult', 1.0)
            else:
                multiplier *= part.get('intact_mult', 1.0)
        return multiplier

    def get_damage(self):
        """Calculates damage via facade."""
        return mob_logic.get_damage(self)

    def take_damage(self, amount, source=None, context="Combat Hit"):
        """
        [DEPRECATED] Use logic.core.combat.apply_damage instead.
        Applies damage to the monster via the combat facade.
        """
        from logic.core import combat
        return combat.apply_damage(self, amount, source=source, context=context)
        

    def stop_combat(self):
        """Clears combat state via centralized facade."""
        combat_logic.stop_combat(self)

    def die(self):
        """Handles death via facade."""
        mob_logic.die(self)
        
    def mark_tags_dirty(self):
        """Invalidates the Unified Tag Synergy (UTS) cache."""
        self.tags_are_dirty = True

    def get_global_tag_count(self, tag):
        """
        Retrieves the total tag count (Voltage) for a specific tag.
        Uses cached resonance result if available.
        """
        if self.tags_are_dirty:
            from logic.engines.resonance_engine import ResonanceAuditor
            self._cached_tags = ResonanceAuditor.calculate_resonance(self)
            self.tags_are_dirty = False
            
        return self._cached_tags.get(tag, 0)

    def get_max_resource(self, resource_name):
        """Returns max resource. Defaults to 100 for mobs."""
        return 100

    @property
    def concealment(self):
        return self.base_concealment

    @property
    def perception(self):
        return self.base_perception
