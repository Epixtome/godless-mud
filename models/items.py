import logging

logger = logging.getLogger("GodlessMUD")

class GameEntity:
    """Base class for all named objects in the world."""
    def __init__(self, name, description, flags=None, prototype_id=None):
        self.name = name
        self.description = description
        self.flags = flags or []
        self.prototype_id = prototype_id

class BaseItem(GameEntity):
    """Base class for carryable items (includes timer/decay logic)."""
    def __init__(self, name, description, value=0, flags=None, prototype_id=None, timer=None, tags=None, properties=None):
        super().__init__(name, description, flags, prototype_id)
        self.value = value
        self.timer = timer # Now ALL items support decay
        self.tags = tags or []
        self.properties = properties or {}
        self.metadata = {}

    def clone(self):
        raise NotImplementedError("Subclasses must implement clone")

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "value": self.value,
            "flags": self.flags,
            "prototype_id": self.prototype_id,
            "timer": self.timer,
            "tags": self.tags,
            "properties": self.properties
        }

class Item(BaseItem):
    """Generic items and Containers."""
    def __init__(self, name, description, value=10, flags=None, prototype_id=None, state='open', key_id=None, timer=None, tags=None, properties=None):
        super().__init__(name, description, value, flags, prototype_id, timer, tags, properties)
        self.state = state # open, closed, locked
        self.key_id = key_id

    def clone(self):
        return Item(self.name, self.description, self.value, self.flags.copy(), self.prototype_id, self.state, self.key_id, self.timer, self.tags.copy(), self.properties.copy())

    @classmethod
    def from_dict(cls, data):
        return cls(data['name'], data['description'], data.get('value', 10), data.get('flags'), data.get('prototype_id'), data.get('state', 'open'), data.get('key_id'), data.get('timer'), data.get('tags'), data.get('properties'))

    def to_dict(self):
        data = super().to_dict()
        data.update({"type": "item", "state": self.state, "key_id": self.key_id})
        return data

    def __str__(self):
        return self.name

class Armor(BaseItem):
    def __init__(self, name, description, defense=0, stability=None, weight_class="light", value=10, flags=None, prototype_id=None, timer=None, tags=None, properties=None, **kwargs):
        super().__init__(name, description, value, flags, prototype_id, timer, tags, properties)
        self.defense = defense
        self.stability = stability if stability is not None else defense
        self.weight_class = weight_class
        self.bonus_hp = 0
        
        # Set arbitrary attributes (slot, requirements, etc)
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __str__(self):
        return f"{self.name} (DEF: {self.defense})"

    def clone(self):
        """Returns a deep copy of this armor."""
        # Use __dict__ to ensure all arbitrary attributes are cloned
        new_armor = Armor(self.name, self.description, self.defense, self.stability, self.weight_class, self.value, self.flags.copy(), self.prototype_id, self.timer, self.tags.copy(), self.properties.copy())
        for key, value in self.__dict__.items():
            if key not in ['name', 'description', 'defense', 'stability', 'weight_class', 'value', 'flags', 'prototype_id', 'timer', 'tags', 'properties']:
                setattr(new_armor, key, value)
        return new_armor

    @classmethod
    def from_dict(cls, data):
        # Extract core fields
        core_fields = ['name', 'description', 'defense', 'stability', 'weight_class', 'value', 'flags', 'prototype_id', 'timer', 'tags', 'properties']
        base_data = {k: data[k] for k in core_fields if k in data}
        
        # Handle tags/gear_tags mapping
        if 'tags' not in base_data and 'gear_tags' in data:
            base_data['tags'] = data['gear_tags']
            
        # Pass remaining data as kwargs
        extra_data = {k: v for k, v in data.items() if k not in core_fields and k != 'type'}
        
        return cls(**base_data, **extra_data)

    def to_dict(self):
        data = super().to_dict()
        data.update({
            "type": "armor", 
            "defense": self.defense,
            "stability": self.stability,
            "weight_class": self.weight_class
        })
        # Add all other attributes
        for key, value in self.__dict__.items():
            if key not in data and not key.startswith('_'):
                data[key] = value
        return data

class Weapon(BaseItem):
    def __init__(self, name, description, damage_dice="1d4", scaling=None, value=10, flags=None, prototype_id=None, timer=None, tags=None, properties=None, **kwargs):
        super().__init__(name, description, value, flags, prototype_id, timer, tags, properties)
        self.damage_dice = damage_dice  # e.g., "2d3"
        self.scaling = scaling or {}     # e.g., {"fire": 1.2}
        
        # Set arbitrary attributes (slot, hands, etc)
        for key, value in kwargs.items():
            setattr(self, key, value)

    def clone(self):
        """Returns a deep copy of this weapon."""
        new_weapon = Weapon(self.name, self.description, self.damage_dice, self.scaling.copy(), self.value, self.flags.copy(), self.prototype_id, self.timer, self.tags.copy(), self.properties.copy())
        for key, value in self.__dict__.items():
            if key not in ['name', 'description', 'damage_dice', 'scaling', 'value', 'flags', 'prototype_id', 'timer', 'tags', 'properties']:
                setattr(new_weapon, key, value)
        return new_weapon

    @classmethod
    def from_dict(cls, data):
        # Extract core fields
        core_fields = ['name', 'description', 'damage_dice', 'scaling', 'value', 'flags', 'prototype_id', 'timer', 'tags', 'properties']
        base_data = {k: data[k] for k in core_fields if k in data}
        
        # Pass remaining data as kwargs
        extra_data = {k: v for k, v in data.items() if k not in core_fields and k != 'type'}
        
        return cls(**base_data, **extra_data)

    def to_dict(self):
        data = super().to_dict()
        data.update({"type": "weapon", "damage_dice": self.damage_dice, "scaling": self.scaling})
        # Add all other attributes
        for key, value in self.__dict__.items():
            if key not in data and not key.startswith('_'):
                data[key] = value
        return data

class Consumable(BaseItem):
    def __init__(self, name, description, effects, value=5, flags=None, prototype_id=None, timer=None, tags=None, properties=None):
        super().__init__(name, description, value, flags, prototype_id, timer, tags, properties)
        self.effects = effects # {"hp": 20, "stamina": 10}

    def clone(self):
        return Consumable(self.name, self.description, self.effects.copy(), self.value, self.flags.copy(), self.prototype_id, self.timer, self.tags.copy(), self.properties.copy())

    @classmethod
    def from_dict(cls, data):
        return cls(data['name'], data['description'], data['effects'], data.get('value', 5), data.get('flags'), data.get('prototype_id'), data.get('timer'), data.get('tags'), data.get('properties'))

    def to_dict(self):
        data = super().to_dict()
        data.update({"type": "consumable", "effects": self.effects})
        return data

    def __str__(self):
        return self.name

class Corpse(BaseItem):
    def __init__(self, name, description, inventory=None, flags=None, timer=None, tags=None, properties=None):
        # Corpses have 0 value by default
        super().__init__(name, description, 0, flags or ['decay'], None, timer, tags, properties)
        self.inventory = inventory or []

    def __str__(self):
        return self.name

    def clone(self):
        return Corpse(self.name, self.description, [i.clone() for i in self.inventory], self.flags.copy(), self.timer, self.tags.copy(), self.properties.copy())

    def to_dict(self):
        data = super().to_dict()
        data.update({"type": "corpse", "inventory": [i.to_dict() for i in self.inventory]})
        return data

    @classmethod
    def from_dict(cls, data):
        inv = [create_item_from_dict(i_data) for i_data in data.get('inventory', [])]
        return cls(data['name'], data['description'], inv, data.get('flags'), data.get('timer'), data.get('tags'), data.get('properties'))
class Currency(BaseItem):
    def __init__(self, amount=1, coin_type="gold", name=None, description=None, tags=None):
        name = name or f"{amount} {coin_type} coins"
        description = description or f"A small pile of {coin_type} currency."
        super().__init__(name, description, value=amount, flags=['currency'], tags=tags)
        self.amount = amount
        self.coin_type = coin_type

    def clone(self):
        return Currency(self.amount, self.coin_type, self.name, self.description, self.tags.copy())

    def to_dict(self):
        data = super().to_dict()
        data.update({"type": "currency", "amount": self.amount, "coin_type": self.coin_type})
        return data

    @classmethod
    def from_dict(cls, data):
        return cls(data.get('amount', 1), data.get('coin_type', 'gold'), data['name'], data['description'], data.get('tags'))

def create_item_from_dict(data):
    """Factory function to recreate an item from its dictionary representation."""
    i_type = data.get('type', 'item')
    if i_type == 'armor': return Armor.from_dict(data)
    elif i_type == 'weapon': return Weapon.from_dict(data)
    elif i_type == 'consumable': return Consumable.from_dict(data)
    elif i_type == 'currency': return Currency.from_dict(data)
    elif i_type == 'corpse': return Corpse.from_dict(data)
    return Item.from_dict(data)
