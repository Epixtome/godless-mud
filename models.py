import logging
import json
import os

logger = logging.getLogger("GodlessMUD")

class Item:
    def __init__(self, name, description, value=10, flags=None, prototype_id=None, state='open', key_id=None):
        self.name = name
        self.description = description
        self.value = value
        self.flags = flags or []
        self.prototype_id = prototype_id
        self.state = state # open, closed, locked
        self.key_id = key_id

    def clone(self):
        return Item(self.name, self.description, self.value, self.flags.copy(), self.prototype_id, self.state, self.key_id)

    @classmethod
    def from_dict(cls, data):
        return cls(data['name'], data['description'], data.get('value', 10), data.get('flags'), data.get('prototype_id'), data.get('state', 'open'), data.get('key_id'))

    def to_dict(self):
        return {
            "type": "item",
            "name": self.name,
            "description": self.description,
            "value": self.value,
            "flags": self.flags,
            "prototype_id": self.prototype_id,
            "state": self.state,
            "key_id": self.key_id
        }

    def __str__(self):
        return self.name

class Armor:
    def __init__(self, name, description, defense, stat_bonuses=None, value=10, flags=None, prototype_id=None):
        self.name = name
        self.description = description
        self.defense = defense
        self.stat_bonuses = stat_bonuses or {}
        self.value = value
        self.flags = flags or []
        self.prototype_id = prototype_id

    def __str__(self):
        return f"{self.name} (DEF: {self.defense})"

    def clone(self):
        """Returns a deep copy of this armor."""
        return Armor(self.name, self.description, self.defense, self.stat_bonuses.copy(), self.value, self.flags.copy(), self.prototype_id)

    @classmethod
    def from_dict(cls, data):
        return cls(data['name'], data['description'], data['defense'], data.get('stat_bonuses'), data.get('value', 10), data.get('flags'), data.get('prototype_id'))

    def to_dict(self):
        return {
            "type": "armor",
            "name": self.name,
            "description": self.description,
            "defense": self.defense,
            "stat_bonuses": self.stat_bonuses,
            "value": self.value,
            "flags": self.flags,
            "prototype_id": self.prototype_id
        }

class Weapon:
    def __init__(self, name, description, damage_dice, scaling, stat_bonuses=None, value=10, flags=None, prototype_id=None):
        self.name = name
        self.description = description
        self.damage_dice = damage_dice  # e.g., "2d3"
        self.scaling = scaling          # e.g., {"str": 1.2}
        self.stat_bonuses = stat_bonuses or {}
        self.value = value
        self.flags = flags or []
        self.prototype_id = prototype_id

    def clone(self):
        """Returns a deep copy of this weapon."""
        return Weapon(self.name, self.description, self.damage_dice, self.scaling.copy(), self.stat_bonuses.copy(), self.value, self.flags.copy(), self.prototype_id)

    @classmethod
    def from_dict(cls, data):
        return cls(data['name'], data['description'], data['damage_dice'], data['scaling'], data.get('stat_bonuses'), data.get('value', 10), data.get('flags'), data.get('prototype_id'))

    def to_dict(self):
        return {
            "type": "weapon",
            "name": self.name,
            "description": self.description,
            "damage_dice": self.damage_dice,
            "scaling": self.scaling,
            "stat_bonuses": self.stat_bonuses,
            "value": self.value,
            "flags": self.flags,
            "prototype_id": self.prototype_id
        }

class Consumable:
    def __init__(self, name, description, effects, value=5, flags=None, prototype_id=None):
        self.name = name
        self.description = description
        self.effects = effects # {"hp": 20, "stamina": 10}
        self.value = value
        self.flags = flags or []
        self.prototype_id = prototype_id

    def clone(self):
        return Consumable(self.name, self.description, self.effects.copy(), self.value, self.flags.copy())

    @classmethod
    def from_dict(cls, data):
        return cls(data['name'], data['description'], data['effects'], data.get('value', 5), data.get('flags'), data.get('prototype_id'))

    def to_dict(self):
        return {
            "type": "consumable",
            "name": self.name,
            "description": self.description,
            "effects": self.effects,
            "value": self.value,
            "flags": self.flags,
            "prototype_id": self.prototype_id
        }

    def __str__(self):
        return self.name

class Blessing:
    def __init__(self, b_id, name, tier, base_power, scaling, requirements, identity_tags, charges, description, cost=0, deity_id=None):
        self.id = b_id
        self.name = name
        self.tier = tier
        self.base_power = base_power
        self.scaling = scaling          # {"str": 1.5}
        self.requirements = requirements # {"str": 12}
        self.identity_tags = identity_tags # ["paladin"]
        self.charges = charges
        self.description = description
        self.cost = cost
        self.deity_id = deity_id

    def __str__(self):
        return f"{self.name} (T{self.tier})"

class Corpse:
    def __init__(self, name, description, inventory=None, flags=None):
        self.name = name
        self.description = description
        self.inventory = inventory or []
        self.flags = flags or ['decay']

    def __str__(self):
        return self.name

    def clone(self):
        return Corpse(self.name, self.description, [i.clone() for i in self.inventory], self.flags.copy())

    def to_dict(self):
        return {
            "type": "corpse",
            "name": self.name,
            "description": self.description,
            "inventory": [i.to_dict() for i in self.inventory],
            "flags": self.flags
        }

    @classmethod
    def from_dict(cls, data):
        inv = []
        for i_data in data.get('inventory', []):
            if i_data.get('type') == 'armor': inv.append(Armor.from_dict(i_data))
            elif i_data.get('type') == 'weapon': inv.append(Weapon.from_dict(i_data))
            elif i_data.get('type') == 'consumable': inv.append(Consumable.from_dict(i_data))
            elif i_data.get('type') == 'item': inv.append(Item.from_dict(i_data))
        return cls(data['name'], data['description'], inv, data.get('flags'))

class Quest:
    def __init__(self, q_id, name, giver_text, log_text, objectives, rewards):
        self.id = q_id
        self.name = name
        self.giver_text = giver_text
        self.log_text = log_text
        self.objectives = objectives
        self.rewards = rewards

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

class Room:
    def __init__(self, room_id, name, description):
        self.id = room_id
        self.name = name
        self.description = description
        self.exits = {}  # Direction -> Room
        self.doors = {}  # Direction -> Door object
        self.items = []  # List of Armor/Items
        self.monsters = [] # List of Monster objects
        self.players = [] # List of Player objects currently in room
        self.x = 0
        self.y = 0
        self.z = 0
        self.zone_id = None
        self.shop_inventory = [] # List of item IDs sold here
        self.deity_id = None # ID of deity present here (for commune)
        self.static_items = [] # List of prototype IDs/dicts for zone generation
        self.static_monsters = [] # List of prototype IDs/dicts for zone generation
        self.terrain = "indoors"
        self.opacity = 0 # 0.0 (Transparent) to 1.0 (Opaque)
        self.traversal_cost = 1 # 1 (Road) to 10 (Swamp)

    def add_exit(self, direction, room):
        self.exits[direction] = room

    def to_definition(self):
        """Returns the static definition of the room for saving to JSON."""
        data = {
            "id": self.id,
            "zone_id": self.zone_id,
            "name": self.name,
            "description": self.description,
            "exits": {d: (r.id if hasattr(r, 'id') else r) for d, r in self.exits.items()},
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "terrain": self.terrain,
            "opacity": self.opacity,
            "traversal_cost": self.traversal_cost
        }
        if self.shop_inventory: data["shop_inventory"] = self.shop_inventory
        if self.deity_id: data["deity_id"] = self.deity_id
        if self.static_items: data["items"] = self.static_items
        if self.static_monsters: data["monsters"] = self.static_monsters
        return data

    def serialize_state(self):
        """Returns the dynamic state of the room (items, monsters)."""
        return {
            "items": [item.to_dict() for item in self.items],
            "monsters": [mob.to_dict() for mob in self.monsters]
        }

    def broadcast(self, message, exclude_player=None):
        """Send a message to everyone in the room except the sender."""
        for player in self.players:
            if player != exclude_player:
                player.send_line(message)

class Door:
    def __init__(self, name, state='closed', key_id=None, transparency=0.0):
        self.name = name
        self.state = state # open, closed, locked
        self.key_id = key_id
        self.transparency = transparency # 0.0 (Solid) to 1.0 (Glass)

class Zone:
    def __init__(self, zone_id, name, security_level='safe'):
        self.id = zone_id
        self.name = name
        self.security_level = security_level

class Class:
    def __init__(self, c_id, name, description, requirements, bonuses):
        self.id = c_id
        self.name = name
        self.description = description
        self.requirements = requirements # {'tags': {'light': 3}}
        self.bonuses = bonuses # {'str': 2}

class Deity:
    def __init__(self, d_id, name, kingdom, stat):
        self.id = d_id
        self.name = name
        self.kingdom = kingdom
        self.stat = stat

class Synergy:
    def __init__(self, s_id, name, requirements, bonuses):
        self.id = s_id
        self.name = name
        self.requirements = requirements
        self.bonuses = bonuses

class HelpEntry:
    def __init__(self, keywords, title, body):
        self.keywords = keywords
        self.title = title
        self.body = body

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
        self.resources = {'stamina': 100, 'concentration': 10, 'momentum': 0, 'chi': 0}
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

    def get_defense(self):
        """Calculates total defense from Armor + Buffs."""
        # 1. Base Defense (Could be derived from stats later, e.g. DEX / 4)
        total_def = 0
        
        # 2. Additive (Armor)
        if self.equipped_armor:
            total_def += self.equipped_armor.defense
            
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