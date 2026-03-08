"""
logic/modules/beastmaster/pet.py
The Pet entity for the Beastmaster class.
Inherits from Monster to leverage existing combat and room logic.
"""
from models.entities import Monster
from utilities.colors import Colors

class Pet(Monster):
    """
    Tamed Pet entity.
    """
    def __init__(self, owner, name, archetype_data):
        self.owner = owner
        self.archetype = archetype_data.get('name', 'Pet')
        self.archetype_key = archetype_data.get('key', 'sentinel')
        
        # Calculate Stats based on Archetype multipliers
        max_hp = int(owner.max_hp * archetype_data.get('hp_mult', 1.0))
        damage = int(15 * archetype_data.get('damage_mult', 1.0)) 
        
        # Call Monster's __init__
        # Monster(name, description, hp, damage, tags, max_hp, prototype_id=None, home_room_id=None, game=None)
        short_desc = f"{name}, the {archetype_data.get('name')} of {owner.name}"
        long_desc = f"A {archetype_data.get('special_desc')} {self.archetype} that follows {owner.name} loyally."
        
        super().__init__(
            short_desc, 
            long_desc, 
            max_hp, 
            damage, 
            archetype_data.get('tags', []), 
            max_hp, 
            prototype_id=f"pet:{self.archetype_key}",
            game=owner.game
        )
        
        self.id = f"pet_{owner.id}_{name.lower().replace(' ', '_')}"
        self.tamed_name = name
        self.sync_val = 0 # Individual pet sync? No, we use global bm_state['sync']
        self.owner_id = owner.id
        self.is_pet = True
        
        # Register in game's global monster list (if needed for tracking)
        if owner.game:
            # We don't necessarily want to put it in world.monsters (which are prototypes)
            # but we can track it on the owner or room.
            pass

    def to_dict(self):
        """Serialization for the Pet state."""
        data = super().to_dict()
        data.update({
            "owner_id": self.owner_id,
            "tamed_name": self.tamed_name,
            "archetype_key": self.archetype_key,
            "is_pet": True
        })
        return data

    @classmethod
    def from_dict(cls, data, owner):
        # We'd need archetype metadata here to reconstruct correctly if we wanted to fully deserialize.
        # But usually we re-instantiate pets from the 'tamed_library' on '@call'.
        pass
