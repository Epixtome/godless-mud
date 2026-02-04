import logging
import json
import os
from .items import Armor, Weapon, Consumable, Item

logger = logging.getLogger("GodlessMUD")

class Monster:
    def __init__(self, name, description, hp, damage, tags=None, max_hp=None, prototype_id=None, home_room_id=None):
        self.name = name
        self.description = description
        self.hp = hp
        self.max_hp = max_hp if max_hp is not None else hp
        self.damage = damage
        self.fighting = None
        self.attackers = [] # List of entities attacking this mob
        self.inventory = []
        self.tags = tags or []
        self.prototype_id = prototype_id
        self.quests = [] # List of quest IDs this mob can give
        self.home_room_id = home_room_id
        self.leader = None # Entity this mob follows
        self.can_be_companion = False # If True, can be recruited via friendship
        self.room = None # Reference to the Room object containing this mob
        self.status_effects = {} # effect_id -> expiry_tick
        self.body_parts = {} # name -> {hp, max_hp, defense_bonus, destroyed}
        self.base_concealment = 0
        self.base_perception = 10

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "damage": self.damage,
            "tags": self.tags,
            "prototype_id": self.prototype_id,
            "home_room_id": self.home_room_id,
            "can_be_companion": self.can_be_companion
            # Note: We aren't saving inventory deeply here for simplicity, but could.
        }

    def is_in_combat(self):
        """Returns True if the monster is currently in a fight."""
        return self.fighting is not None

    def get_defense(self):
        """Calculates total defense. Currently 0 for mobs, but allows for future armor/buffs."""
        total_def = 0
        # Add defense from intact body parts
        for part in self.body_parts.values():
            if not part.get('destroyed', False):
                total_def += part.get('defense_bonus', 0)
        return total_def

    def get_damage_modifier(self):
        """Calculates incoming damage multiplier based on body parts."""
        multiplier = 1.0
        for part in self.body_parts.values():
            if part.get('destroyed', False):
                multiplier *= part.get('broken_mult', 1.0)
            else:
                multiplier *= part.get('intact_mult', 1.0)
        return multiplier
        
    @property
    def concealment(self):
        return self.base_concealment

    @property
    def perception(self):
        return self.base_perception

class Player:
    def __init__(self, game, writer, name, start_room):
        self.game = game
        self.writer = writer
        self.name = name
        self.room = start_room
        self.inventory = []
        self.inventory_limit = 20
        self.equipped_armor = None
        self.equipped_weapon = None
        self.equipped_offhand = None
        self.base_stats = {'str': 10, 'dex': 10, 'con': 10, 'wis': 10, 'int': 10, 'luk': 10}
        self.hp = 100
        self.max_hp = 100
        self.fighting = None
        self.attackers = [] # List of entities attacking this player
        self.identity_tags = ["adventurer"] # Default tag
        self.known_blessings = [] # List of blessing IDs
        self.equipped_blessings = [] # List of equipped blessing IDs (Deck)
        self.blessing_charges = {} # ID -> current charges
        self.blessing_xp = {} # ID -> xp amount
        self.resources = {'stamina': 100, 'concentration': 100, 'momentum': 0, 'chi': 0}
        self.favor = {} # Deity ID -> Amount
        self.gold = 0
        self.aliases = {}
        self.cooldowns = {} # ID -> tick when ready
        self.pagination_buffer = [] # Lines of text waiting to be displayed
        self.active_class = None
        self.unlocked_classes = []
        self.is_resting = False
        self.rest_until = 0
        self.active_quests = {} # {quest_id: {obj_id: progress}}
        self.completed_quests = [] # [quest_id]
        self.password = None
        self.is_admin = False
        self.is_building = False
        self.status_effects = {} # effect_id -> expiry_tick
        self.interaction_context = None # For multi-step interactions
        self.state = "normal" # normal, commune, combat, etc.
        self.round_actions = {'skill': 0, 'spell': 0} # Resets every heartbeat
        self.minions = [] # List of mobs following this player
        self.friendship = {} # npc_id -> level (0-100)
        self.visited_rooms = set() # Set of room IDs visited
        self.locked_target = None # For ranged combat (Ranger)
        self.reputation = 0 # -100 to 100. < -10 is Criminal.
        self.is_mounted = False
        self.stance = None
        self.admin_vision = False
        self.base_concealment = 0
        self.base_perception = 10
        
        # Add self to starting room
        self.room.players.append(self)
        # Mark start room as visited
        if self.room:
            self.visited_rooms.add(self.room.id)

    def to_dict(self):
        return {
            "name": self.name,
            "room_id": self.room.id,
            "gold": self.gold,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "identity_tags": self.identity_tags,
            "known_blessings": self.known_blessings,
            "equipped_blessings": self.equipped_blessings,
            "blessing_charges": self.blessing_charges,
            "blessing_xp": self.blessing_xp,
            "base_stats": self.base_stats,
            "inventory": [item.to_dict() for item in self.inventory],
            "favor": self.favor,
            "aliases": self.aliases,
            "cooldowns": self.cooldowns,
            "active_class": self.active_class,
            "unlocked_classes": self.unlocked_classes,
            "is_resting": self.is_resting,
            "rest_until": self.rest_until,
            "active_quests": self.active_quests,
            "completed_quests": self.completed_quests,
            "status_effects": self.status_effects,
            "password": self.password,
            "is_admin": self.is_admin,
            "is_building": self.is_building,
            "equipped_armor": self.equipped_armor.to_dict() if self.equipped_armor else None,
            "equipped_weapon": self.equipped_weapon.to_dict() if self.equipped_weapon else None,
            "equipped_offhand": self.equipped_offhand.to_dict() if self.equipped_offhand else None,
            "friendship": self.friendship,
            "visited_rooms": list(self.visited_rooms),
            "reputation": self.reputation,
            "stance": self.stance,
            "admin_vision": self.admin_vision
        }

    def load_data(self, data):
        """Hydrates player state from a dictionary."""
        self.hp = data.get('hp', self.hp)
        self.gold = data.get('gold', 0)
        self.max_hp = data.get('max_hp', self.max_hp)
        
        if 'base_stats' in data:
            self.base_stats.update(data['base_stats'])
            
        self.identity_tags = data.get('identity_tags', self.identity_tags)
        self.known_blessings = data.get('known_blessings', [])
        self.equipped_blessings = data.get('equipped_blessings', [])
        
        if 'blessing_charges' in data:
            self.blessing_charges.update(data['blessing_charges'])
            
        if 'blessing_xp' in data:
            self.blessing_xp.update(data['blessing_xp'])
            
        if 'resources' in data:
            self.resources.update(data['resources'])
        
        favor_data = data.get('favor', {})
        if isinstance(favor_data, dict):
            self.favor.update(favor_data)
            
        self.active_class = data.get('active_class')
        self.unlocked_classes = data.get('unlocked_classes', [])
        if 'aliases' in data:
            self.aliases.update(data['aliases'])
        
        if 'cooldowns' in data:
            self.cooldowns.update(data['cooldowns'])
            
        self.is_resting = data.get('is_resting', False)
        self.rest_until = data.get('rest_until', 0)

        self.active_quests = data.get('active_quests', {})
        self.completed_quests = data.get('completed_quests', [])

        if 'status_effects' in data:
            self.status_effects.update(data['status_effects'])
        
        self.password = data.get('password')
        self.is_admin = data.get('is_admin', False)
        self.is_building = data.get('is_building', False)
        
        if 'friendship' in data:
            self.friendship.update(data['friendship'])
            
        self.visited_rooms = set(data.get('visited_rooms', []))
        self.reputation = data.get('reputation', 0)
        self.stance = data.get('stance')
        self.admin_vision = data.get('admin_vision', False)
        
        # Reconstruct Inventory
        self.inventory = []
        for item_data in data.get('inventory', []):
            if item_data.get('type') == 'armor':
                self.inventory.append(Armor.from_dict(item_data))
            elif item_data.get('type') == 'weapon':
                self.inventory.append(Weapon.from_dict(item_data))
            elif item_data.get('type') == 'consumable':
                self.inventory.append(Consumable.from_dict(item_data))
            elif item_data.get('type') == 'item':
                self.inventory.append(Item.from_dict(item_data))
        
        if data.get('equipped_armor'):
            self.equipped_armor = Armor.from_dict(data['equipped_armor'])
        if data.get('equipped_weapon'):
            self.equipped_weapon = Weapon.from_dict(data['equipped_weapon'])
        if data.get('equipped_offhand'):
            self.equipped_offhand = Armor.from_dict(data['equipped_offhand'])

    def is_in_combat(self):
        """Returns True if the player is currently in a fight."""
        return self.fighting is not None

    def get_stat(self, stat_name):
        """Calculate total stat value from base + gear."""
        # 1. Base Value
        base_val = self.base_stats.get(stat_name, 0)
        
        # 2. Additive Bonuses (Gear, Synergies)
        add_bonus = 0
        if self.equipped_armor:
            add_bonus += self.equipped_armor.stat_bonuses.get(stat_name, 0)
        if self.equipped_weapon:
            add_bonus += self.equipped_weapon.stat_bonuses.get(stat_name, 0)
        if self.equipped_offhand:
            add_bonus += self.equipped_offhand.stat_bonuses.get(stat_name, 0)
            
        # Class Bonuses
        if self.active_class:
            cls_obj = self.game.world.classes.get(self.active_class)
            if cls_obj and cls_obj.bonuses and 'stats' in cls_obj.bonuses:
                add_bonus += cls_obj.bonuses['stats'].get(stat_name, 0)

        # Apply Synergies (if any)
        # This logic would live in synergy_engine, but for now, we can simulate it
        
        # 3. Multiplicative Bonuses (Buffs, Stances, Debuffs)
        mult_bonus = 1.0
        for effect_id in self.status_effects:
            # Assuming world.status_effects is a dict for O(1) lookup
            effect_data = self.game.world.status_effects.get(effect_id)
            if effect_data:
                mods = effect_data.get('modifiers', {})
                
                # Multiplicative: "str_mult": 1.2
                mult_key = f"{stat_name}_mult"
                if mult_key in mods:
                    mult_bonus *= mods[mult_key]
                
                # Additive from Effects: "str_add": 5
                add_key = f"{stat_name}_add"
                if add_key in mods:
                    add_bonus += mods[add_key]
            
        # 4. Final Calculation
        final_val = int((base_val + add_bonus) * mult_bonus)
        return final_val

    def get_max_resource(self, resource_name):
        """Calculates max resource value including passives."""
        base = 100
        if resource_name == 'momentum': base = 100
        if resource_name == 'chi': base = 5
        
        # Class Passives
        if self.active_class and resource_name == 'concentration':
            cls = self.game.world.classes.get(self.active_class)
            if cls and cls.bonuses and 'passive' in cls.bonuses:
                if "Max Concentration +10" in cls.bonuses['passive']:
                    base += 10
        return base

    def get_defense(self):
        """Calculates total defense from Armor + Buffs."""
        # 1. Base Defense (Could be derived from stats later, e.g. DEX / 4)
        total_def = 0
        
        # 2. Additive (Armor)
        if self.equipped_armor:
            total_def += self.equipped_armor.defense
        if self.equipped_offhand:
            total_def += self.equipped_offhand.defense
            
        # 3. Buffs/Effects
        for effect_id in self.status_effects:
            effect_data = self.game.world.status_effects.get(effect_id)
            if effect_data:
                mods = effect_data.get('modifiers', {})
                total_def += mods.get('defense_add', 0)
                
        return int(total_def)

    @property
    def concealment(self):
        return self.base_concealment + (self.get_stat('dex') // 2)

    @property
    def perception(self):
        return self.base_perception + (self.get_stat('wis') // 2)

    def send_line(self, message):
        """Send text to this player's telnet client."""
        try:
            self.writer.write(f"{message}\r\n".encode('utf-8'))
        except Exception as e:
            logger.error(f"Error sending to {self.name}: {e}")

    async def drain(self):
        try:
            await self.writer.drain()
        except Exception:
            pass

    def get_prompt(self):
        """Returns the command prompt string."""
        # Resources
        parts = [f"HP: {self.hp}/{self.max_hp}"]
        if 'stamina' in self.resources:
            parts.append(f"ST: {self.resources['stamina']}")
        if 'concentration' in self.resources:
            parts.append(f"MN: {self.resources['concentration']}")
        if self.resources.get('chi', 0) > 0:
            parts.append(f"CHI: {self.resources['chi']}")
            
        prompt = f"[{' '.join(parts)}]"
        
        # Combat Status
        if self.fighting:
            target = self.fighting
            t_max = getattr(target, 'max_hp', target.hp) or 1
            pct = (target.hp / t_max) * 100
            
            condition = "Excellent"
            if pct < 15: condition = "Critical"
            elif pct < 30: condition = "Bad"
            elif pct < 50: condition = "Wounded"
            elif pct < 75: condition = "Hurt"
            elif pct < 100: condition = "Scratched"
            
            prompt += f" <{target.name}: {condition}>"
            
        return prompt + " > "

    def save(self):
        """Saves the player data to disk."""
        try:
            os.makedirs("data/saves", exist_ok=True)
            filename = f"data/saves/{self.name.lower()}.json"
            with open(filename, 'w') as f:
                json.dump(self.to_dict(), f, indent=4)
            logger.info(f"Saved {self.name}")
        except Exception as e:
            logger.error(f"Failed to save {self.name}: {e}")

    def send_paginated(self, text):
        """Queues text for paginated display."""
        lines = text.strip().split('\n')
        self.pagination_buffer = lines
        self.show_next_page()

    def show_next_page(self):
        """Displays the next chunk of text from the buffer."""
        PAGE_SIZE = 20
        if not self.pagination_buffer:
            return
        
        chunk = self.pagination_buffer[:PAGE_SIZE]
        self.pagination_buffer = self.pagination_buffer[PAGE_SIZE:]
        
        for line in chunk:
            self.send_line(line)
            
        if self.pagination_buffer:
            self.writer.write(b"[Press Enter for more, 'q' to quit] ")
