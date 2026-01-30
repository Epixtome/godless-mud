import logging
from logic.engines import magic_engine

logger = logging.getLogger("GodlessMUD")

TIER_LIMITS = {
    1: 4, # Foundations
    2: 3, # Sparks
    3: 2, # Masteries
    4: 1  # Ultimates
}

class MathBridge:
    """Handles scaling logic for blessings."""
    
    @staticmethod
    def calculate_power(blessing, player):
        """
        Calculates the final power output based on base_power and stat scaling.
        """
        total_power = blessing.base_power
        
        # T1 and T2 scaling logic
        if blessing.tier <= 2:
            for stat, multiplier in blessing.scaling.items():
                player_stat = player.get_stat(stat)
                bonus = player_stat * multiplier
                total_power += bonus
        
        return int(total_power)

class Auditor:
    """Handles validation of requirements and identity."""

    @staticmethod
    def check_requirements(blessing, player):
        """Checks if player meets stat, item, and resource requirements."""
        # Stats are no longer a hard requirement for invoking, only for learning/equipping (if we enforce that there).
        # For now, we remove the check entirely as requested.
        # stats = ['str', 'dex', 'con', 'wis', 'int', 'luk']
        # for stat, min_val in blessing.requirements.items():
        #     if stat in stats and player.get_stat(stat) < min_val:
        #         return False, f"Requires {min_val} {stat.upper()}."
        
        # Terrain Check
        req_terrain = blessing.requirements.get('terrain')
        if req_terrain:
            if isinstance(req_terrain, str):
                req_terrain = [req_terrain]
            
            if player.room.terrain not in req_terrain:
                return False, f"Requires terrain: {', '.join(req_terrain)}"

        # State Check
        req_stance = blessing.requirements.get('stance')
        if req_stance and player.stance != req_stance:
            return False, f"You must be in {req_stance} stance."
            
        if blessing.requirements.get('mount') is True and not player.is_mounted:
            return False, "You must be mounted."

        # Equipment Check
        req_shield = blessing.requirements.get('shield')
        if req_shield:
            has_shield = False
            # Assuming shields are a type of armor for now
            if player.equipped_armor and ("shield" in player.equipped_armor.name.lower() or "buckler" in player.equipped_armor.name.lower()):
                has_shield = True
            if not has_shield:
                return False, "You must have a shield equipped."
                
        req_weapon_type = blessing.requirements.get('equipped_weapon_type')
        if req_weapon_type:
            if not player.equipped_weapon or req_weapon_type not in player.equipped_weapon.name.lower():
                # In future, we'd use tags on weapons, not name checks
                return False, f"Requires a {req_weapon_type} to be equipped."
                
        return True, "OK"

    @staticmethod
    def check_identity(blessing, player):
        """Checks if player has at least one matching identity tag."""
        if not blessing.identity_tags:
            return True, "OK"
            
        player_tags = set(player.identity_tags)
        blessing_tags = set(blessing.identity_tags)
        
        if player_tags.intersection(blessing_tags):
            return True, "OK"
        
        return False, f"Requires one of: {', '.join(blessing.identity_tags)}"

    @staticmethod
    def can_invoke(blessing, player):
        """Runs all checks."""
        valid_id, reason_id = Auditor.check_identity(blessing, player)
        if not valid_id: return False, reason_id

        valid_req, reason_req = Auditor.check_requirements(blessing, player)
        if not valid_req: return False, reason_req

        # Note: We can add more checks here like check_equipment, etc.
        # For now, it's integrated into check_requirements.

        # Cooldown Check
        valid_cd, reason_cd = magic_engine.check_cooldown(player, blessing)
        if not valid_cd: return False, reason_cd

        # Resource Check
        valid_res, reason_res = magic_engine.check_resources(player, blessing)
        if not valid_res: return False, reason_res

        # Item Check
        valid_item, reason_item = magic_engine.check_items(player, blessing)
        if not valid_item: return False, reason_item

        return True, "OK"