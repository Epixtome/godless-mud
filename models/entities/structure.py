# models/entities/structure.py
from .monster import Monster

class Structure(Monster):
    """
    [V6.5] Immobile Entity Archetype.
    Used for Turrets, Barricades, and Outposts.
    Inherits from Monster to leverage combat logic, but with movement disabled and fixed positioning.
    """
    def __init__(self, name, description, hp, damage=0, tags=None, **kwargs):
        super().__init__(name, description, hp, damage, tags=tags, **kwargs)
        self.is_stationary = True
        self.can_be_pushed = False
        self.can_be_prone = False 
        self.ai_type = "turret" # Signal for AI engine to skip movement
        self.owner_id = kwargs.get('owner_id') # Kingdom or Player ownership
        self.integrity = 1.0 # Optional secondary health layer for 'Armor' mechanics

    def to_dict(self):
        data = super().to_dict()
        data["is_stationary"] = True
        data["owner_id"] = self.owner_id
        return data
