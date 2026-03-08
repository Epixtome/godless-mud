import logging
from utilities import telemetry

logger = logging.getLogger("GodlessMUD")

class ResonanceAuditor:
    """
    Central authority for calculating Unified Tag Synergy (UTS).
    Aggregates 'Voltage' (Tag Counts) from Deck, Gear, and Effects.
    """
    @staticmethod
    def calculate_resonance(player, preferred_class=None):
        """
        Sums all tags and updates player.current_tags.
        Triggers Class Engine to snap identity based on new totals.
        """
        # 1. Reset Breakthroughs
        player.breakthroughs = {}
        player.synergies = {}
        player.momentum_pips_enabled = False
        # Other flags can be added here
        
        # old_class = getattr(player, 'active_class', None) # No longer needed
        if not hasattr(player, 'equipped_blessings'):
            return {}
            
        total_tags = {}

        # 1. Sum Tags from Active Deck (Class Blessings)
        if hasattr(player, 'equipped_blessings'):
            for b_id in player.equipped_blessings:
                blessing = player.game.world.blessings.get(b_id)
                if blessing:
                    # UTS Standard: identity_tags is a list of strings
                    for tag in blessing.identity_tags:
                        total_tags[tag] = total_tags.get(tag, 0) + 1

        # 2. Sum Tags from Equipped Gear
        gear_slots = []
        
        # Primary: Check individual attributes (Weapon, Armor, Offhand)
        attrs = [
            "equipped_weapon", "equipped_offhand", "equipped_armor",
            "equipped_head", "equipped_neck", "equipped_shoulders",
            "equipped_arms", "equipped_hands", "equipped_finger_l",
            "equipped_finger_r", "equipped_legs", "equipped_feet",
            "equipped_floating", "equipped_mount"
        ]
        for attr in attrs:
            item = getattr(player, attr, None)
            if item:
                gear_slots.append(item)

        # Secondary: Support for player.equipment dict if used
        if hasattr(player, 'equipment') and isinstance(player.equipment, dict):
            for item in player.equipment.values():
                if item and item not in gear_slots:
                    gear_slots.append(item)
        
        for item in gear_slots:
            if item:
                # UTS Standard: Items have 'tags' list
                tags = getattr(item, 'tags', [])
                if isinstance(tags, dict):
                    # Weighted Tags (e.g. {"dark": 3})
                    for tag, count in tags.items():
                        total_tags[tag] = total_tags.get(tag, 0) + count
                else:
                    # Simple List (e.g. ["dark", "magic"])
                    for tag in tags:
                        total_tags[tag] = total_tags.get(tag, 0) + 1

        # 3. Sum Tags from Status Effects
        if hasattr(player, 'status_effects'):
            for effect_id in player.status_effects:
                effect = player.game.world.status_effects.get(effect_id)
                if effect and 'tags' in effect:
                    for tag in effect['tags']:
                        total_tags[tag] = total_tags.get(tag, 0) + 1
                        
        # 4. Add Debug Tags (Admin Overrides)
        if hasattr(player, 'debug_tags'):
            for tag, val in player.debug_tags.items():
                total_tags[tag] = total_tags.get(tag, 0) + val

        # 5. Check for Breakthroughs from base tags
        # Breakthroughs represent passive power levels (Potency)
        if total_tags.get('martial', 0) >= 10:
            player.breakthroughs['martial'] = True
        if total_tags.get('arcane', 0) >= 10:
            player.breakthroughs['arcane'] = True
        if total_tags.get('instinct', 0) >= 10:
            player.breakthroughs['instinct'] = True
        if total_tags.get('holy', 0) >= 10:
            player.breakthroughs['holy'] = True
        if total_tags.get('dark', 0) >= 10:
            player.breakthroughs['dark'] = True

        # 5.5 Check Synergies
        ResonanceAuditor.check_synergies(player, total_tags)

        # 6. Apply Resonant Gear bonuses
        for item in gear_slots:
            if item and hasattr(item, 'resonance_bonus'):
                for condition, bonus in item.resonance_bonus.items():
                    # e.g. "if_arcane_10"
                    parts = condition.split('_')
                    if len(parts) == 3 and parts[0] == 'if':
                        tag_req = parts[1]
                        threshold = 10 # Default to breakthrough
                        try:
                            threshold = int(parts[2])
                        except ValueError:
                            pass
                        
                        # Check against actual tag count
                        if total_tags.get(tag_req, 0) >= threshold:
                            bonus_tags = bonus.get('tags', {})
                            if isinstance(bonus_tags, dict):
                                for tag, count in bonus_tags.items():
                                    total_tags[tag] = total_tags.get(tag, 0) + count
                            elif isinstance(bonus_tags, list):
                                for tag in bonus_tags:
                                    total_tags[tag] = total_tags.get(tag, 0) + 1

        player.current_tags = total_tags

        # Simplified identity update
        player.identity_tags = list(set(["adventurer"] + list(total_tags.keys())))
        
        # [KIT_SYNC] Snapshot
        # Deduplicate logs: Only log if tags changed
        last_tags = getattr(player, '_last_logged_tags', None)
        if last_tags != total_tags:
            kit_name = player.active_kit.get('name', 'Wanderer')
            weapon_name = player.equipped_weapon.name if player.equipped_weapon else "Unarmed"
            # telemetry.log_stat_snapshot(player, total_tags) # Moved to event triggers
            telemetry.telemetry_logger.info(
                f"[KIT_SYNC] Player: {player.name} | Kit: {kit_name} | Weapon: {weapon_name}"
            )
            player._last_logged_tags = total_tags.copy()

        return total_tags

    @staticmethod
    def check_synergies(player, total_tags):
        """
        Checks for Passive Synergies based on tag combinations.
        Note: These are tag-driven bonuses, not character classes.
        """
        # Example Passive Synergy (Hidden Bonus)
        # if (total_tags.get('martial', 0) >= 5 and total_tags.get('arcane', 0) >= 5):
        #     player.synergies['battlemage'] = True
        pass

    @staticmethod
    def get_voltage(player, tag):
        """
        Returns the total voltage (count) for a specific tag.
        Ensures resonance is calculated if cache is empty.
        """
        if not player.current_tags:
            ResonanceAuditor.calculate_resonance(player)
        return player.current_tags.get(tag, 0)