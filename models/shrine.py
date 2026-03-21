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
        self.kingdom = kingdom # light, dark, instinct
        self.coords = coords # (x, y, z)
        self.potency = potency
        self.decay = decay
        self.is_capital = is_capital
        self.favor_reservoir = 0 # Favor sacrificed to boost potency
        
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "deity_id": self.deity_id,
            "kingdom": self.kingdom,
            "coords": self.coords,
            "potency": self.potency,
            "decay": self.decay,
            "is_capital": self.is_capital,
            "favor_reservoir": self.favor_reservoir
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
        shrine.favor_reservoir = data.get('favor_reservoir', 0)
        return shrine
