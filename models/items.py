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
    def __init__(self, name, description, defense, value=10, flags=None, prototype_id=None, timer=None, tags=None, properties=None):
        super().__init__(name, description, value, flags, prototype_id, timer, tags, properties)
        self.defense = defense
        self.bonus_hp = 0

    def __str__(self):
        return f"{self.name} (DEF: {self.defense})"

    def clone(self):
        """Returns a deep copy of this armor."""
        return Armor(self.name, self.description, self.defense, self.value, self.flags.copy(), self.prototype_id, self.timer, self.tags.copy(), self.properties.copy())

    @classmethod
    def from_dict(cls, data):
        return cls(data['name'], data['description'], data['defense'], data.get('value', 10), data.get('flags'), data.get('prototype_id'), data.get('timer'), data.get('tags'), data.get('properties'))

    def to_dict(self):
        data = super().to_dict()
        data.update({"type": "armor", "defense": self.defense})
        return data

class Weapon(BaseItem):
    def __init__(self, name, description, damage_dice, scaling, value=10, flags=None, prototype_id=None, timer=None, tags=None, properties=None):
        super().__init__(name, description, value, flags, prototype_id, timer, tags, properties)
        self.damage_dice = damage_dice  # e.g., "2d3"
        self.scaling = scaling          # e.g., {"fire": 1.2}

    def clone(self):
        """Returns a deep copy of this weapon."""
        return Weapon(self.name, self.description, self.damage_dice, self.scaling.copy(), self.value, self.flags.copy(), self.prototype_id, self.timer, self.tags.copy(), self.properties.copy())

    @classmethod
    def from_dict(cls, data):
        return cls(data['name'], data['description'], data['damage_dice'], data['scaling'], data.get('value', 10), data.get('flags'), data.get('prototype_id'), data.get('timer'), data.get('tags'), data.get('properties'))

    def to_dict(self):
        data = super().to_dict()
        data.update({"type": "weapon", "damage_dice": self.damage_dice, "scaling": self.scaling})
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
