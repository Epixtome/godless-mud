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
    def __init__(self, name, description, value=0, flags=None, prototype_id=None, timer=None):
        super().__init__(name, description, flags, prototype_id)
        self.value = value
        self.timer = timer # Now ALL items support decay

    def clone(self):
        raise NotImplementedError("Subclasses must implement clone")

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "value": self.value,
            "flags": self.flags,
            "prototype_id": self.prototype_id,
            "timer": self.timer
        }

class Item(BaseItem):
    """Generic items and Containers."""
    def __init__(self, name, description, value=10, flags=None, prototype_id=None, state='open', key_id=None, timer=None):
        super().__init__(name, description, value, flags, prototype_id, timer)
        self.state = state # open, closed, locked
        self.key_id = key_id

    def clone(self):
        return Item(self.name, self.description, self.value, self.flags.copy(), self.prototype_id, self.state, self.key_id, self.timer)

    @classmethod
    def from_dict(cls, data):
        return cls(data['name'], data['description'], data.get('value', 10), data.get('flags'), data.get('prototype_id'), data.get('state', 'open'), data.get('key_id'), data.get('timer'))

    def to_dict(self):
        data = super().to_dict()
        data.update({"type": "item", "state": self.state, "key_id": self.key_id})
        return data

    def __str__(self):
        return self.name

class Armor(BaseItem):
    def __init__(self, name, description, defense, stat_bonuses=None, value=10, flags=None, prototype_id=None, timer=None):
        super().__init__(name, description, value, flags, prototype_id, timer)
        self.defense = defense
        self.stat_bonuses = stat_bonuses or {}

    def __str__(self):
        return f"{self.name} (DEF: {self.defense})"

    def clone(self):
        """Returns a deep copy of this armor."""
        return Armor(self.name, self.description, self.defense, self.stat_bonuses.copy(), self.value, self.flags.copy(), self.prototype_id, self.timer)

    @classmethod
    def from_dict(cls, data):
        return cls(data['name'], data['description'], data['defense'], data.get('stat_bonuses'), data.get('value', 10), data.get('flags'), data.get('prototype_id'), data.get('timer'))

    def to_dict(self):
        data = super().to_dict()
        data.update({"type": "armor", "defense": self.defense, "stat_bonuses": self.stat_bonuses})
        return data

class Weapon(BaseItem):
    def __init__(self, name, description, damage_dice, scaling, stat_bonuses=None, value=10, flags=None, prototype_id=None, timer=None):
        super().__init__(name, description, value, flags, prototype_id, timer)
        self.damage_dice = damage_dice  # e.g., "2d3"
        self.scaling = scaling          # e.g., {"str": 1.2}
        self.stat_bonuses = stat_bonuses or {}

    def clone(self):
        """Returns a deep copy of this weapon."""
        return Weapon(self.name, self.description, self.damage_dice, self.scaling.copy(), self.stat_bonuses.copy(), self.value, self.flags.copy(), self.prototype_id, self.timer)

    @classmethod
    def from_dict(cls, data):
        return cls(data['name'], data['description'], data['damage_dice'], data['scaling'], data.get('stat_bonuses'), data.get('value', 10), data.get('flags'), data.get('prototype_id'), data.get('timer'))

    def to_dict(self):
        data = super().to_dict()
        data.update({"type": "weapon", "damage_dice": self.damage_dice, "scaling": self.scaling, "stat_bonuses": self.stat_bonuses})
        return data

class Consumable(BaseItem):
    def __init__(self, name, description, effects, value=5, flags=None, prototype_id=None, timer=None):
        super().__init__(name, description, value, flags, prototype_id, timer)
        self.effects = effects # {"hp": 20, "stamina": 10}

    def clone(self):
        return Consumable(self.name, self.description, self.effects.copy(), self.value, self.flags.copy(), self.prototype_id, self.timer)

    @classmethod
    def from_dict(cls, data):
        return cls(data['name'], data['description'], data['effects'], data.get('value', 5), data.get('flags'), data.get('prototype_id'), data.get('timer'))

    def to_dict(self):
        data = super().to_dict()
        data.update({"type": "consumable", "effects": self.effects})
        return data

    def __str__(self):
        return self.name

class Corpse(BaseItem):
    def __init__(self, name, description, inventory=None, flags=None, timer=None):
        # Corpses have 0 value by default
        super().__init__(name, description, 0, flags or ['decay'], None, timer)
        self.inventory = inventory or []

    def __str__(self):
        return self.name

    def clone(self):
        return Corpse(self.name, self.description, [i.clone() for i in self.inventory], self.flags.copy(), self.timer)

    def to_dict(self):
        data = super().to_dict()
        data.update({"type": "corpse", "inventory": [i.to_dict() for i in self.inventory]})
        return data

    @classmethod
    def from_dict(cls, data):
        inv = []
        for i_data in data.get('inventory', []):
            if i_data.get('type') == 'armor': inv.append(Armor.from_dict(i_data))
            elif i_data.get('type') == 'weapon': inv.append(Weapon.from_dict(i_data))
            elif i_data.get('type') == 'consumable': inv.append(Consumable.from_dict(i_data))
            elif i_data.get('type') == 'item': inv.append(Item.from_dict(i_data))
        return cls(data['name'], data['description'], inv, data.get('flags'), data.get('timer'))
