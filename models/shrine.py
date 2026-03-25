from .items import GameEntity

class Shrine(GameEntity):
    """
    A passive data container representing a Sovereignty Emitter.
    Anchored to specific coordinates, Shrines project the Influence Tide.
    """
    def __init__(self, id, name, description, deity_id, kingdom, coords, potency=1000, decay=5, is_capital=False):
        super().__init__(name, description, prototype_id=id)
        self.id = id
        self.deity_id = deity_id
        self.kingdom = kingdom # Default/Home kingdom (if any)
        self.captured_by = kingdom # The current controlling kingdom
        self.coords = coords # (x, y, z)
        self.potency = potency
        self.decay = decay
        self.is_capital = is_capital
        self.favor_reservoir = 0 # Favor sacrificed to boost potency
        self.favor_cost_mult = 1.0 # Multiplier for class swap ritual cost
        
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "deity_id": self.deity_id,
            "kingdom": self.kingdom,
            "captured_by": self.captured_by,
            "coords": self.coords,
            "potency": self.potency,
            "decay": self.decay,
            "is_capital": self.is_capital,
            "favor_reservoir": self.favor_reservoir,
            "favor_cost_mult": self.favor_cost_mult
        }

    @classmethod
    def from_dict(cls, data):
        shrine = cls(
            data['id'],
            data['name'],
            data.get('description', ''),
            data['deity_id'],
            data['kingdom'],
            data['coords'],
            data.get('potency', 1000),
            data.get('decay', 5),
            data.get('is_capital', False)
        )
        shrine.captured_by = data.get('captured_by', data['kingdom'])
        shrine.favor_reservoir = data.get('favor_reservoir', 0)
        shrine.favor_cost_mult = data.get('favor_cost_mult', 1.0)
        return shrine
