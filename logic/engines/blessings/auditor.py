import logging
from utilities.colors import Colors
from logic.constants import Tags
from logic.core import event_engine
from logic.core import effects
from utilities import telemetry
# Re-export pacing functions to maintain API compatibility with blessings_engine
from .pacing import check_pacing, on_status_removed

logger = logging.getLogger("GodlessMUD")

KIT_RESOURCE_CONVERSIONS = {
    'physical_focus': ['knight', 'squire', 'paladin'], # Converts Conc -> Stamina
    'mental_focus': ['mage', 'wizard', 'sorcerer', 'red_mage'], # Converts Stamina -> Conc
    'free_focus': ['wanderer'] # No Concentration cost
}

class Auditor:
    """Handles validation of requirements and identity."""

    @staticmethod
    def calculate_costs(blessing, player=None, verbose=False):
        """
        Extracts resource costs directly from the blessing's JSON requirements.
        """
        reqs = blessing.requirements
        tags = getattr(blessing, 'identity_tags', [])
        
        # Base Costs
        stamina = reqs.get('stamina', 0)
        conc = reqs.get('concentration', 0)
        chi = reqs.get('chi', 0)
        
        # V4.5 Hybrid: Check top-level 'cost' as fallback
        if stamina == 0 and conc == 0:
            top_cost = getattr(blessing, 'cost', 0)
            if top_cost > 0:
                if any(t in tags for t in ["magic", "spell", "arcane", "elemental"]):
                    conc = top_cost
                else:
                    stamina = top_cost

        # Default Stamina Cost (Physical exertion for non-spells)
        if stamina == 0 and conc == 0 and "passive" not in tags:
            if "movement" in tags:
                stamina = 3
            elif not any(t in tags for t in ["magic", "spell", "arcane", "elemental"]):
                stamina = 10
            
        # V2 Resource Unification: Map legacy costs to Stamina (Heat)
        if reqs.get('heat', 0) > 0: stamina += reqs.get('heat', 0)
        if reqs.get('stability', 0) > 0: stamina += reqs.get('stability', 0)
            
        costs = {
            "stability": 0, # Deprecated
            Tags.CONCENTRATION: conc,
            "stamina": stamina,
            Tags.CHI: chi
        }
        
        if player and hasattr(player, 'active_kit'):
            kit_name = player.active_kit.get('name', '').lower()
            
            if kit_name in KIT_RESOURCE_CONVERSIONS['free_focus']:
                costs[Tags.CONCENTRATION] = 0
                
            elif kit_name in KIT_RESOURCE_CONVERSIONS['physical_focus']:
                # Convert all mental cost to physical exertion
                costs["stamina"] += costs[Tags.CONCENTRATION]
                costs[Tags.CONCENTRATION] = 0
                
            elif kit_name in KIT_RESOURCE_CONVERSIONS['mental_focus']:
                # Convert all physical cost to mental focus
                costs[Tags.CONCENTRATION] += costs["stamina"]
                costs["stamina"] = 0

        # Allow class passives to modify costs
        if player and blessing:
            ctx = {'player': player, 'blessing': blessing, 'costs': costs}
            event_engine.dispatch("on_calculate_skill_cost", ctx)

        return costs

    @staticmethod
    def check_requirements(blessing, player, command=None, args=None):
        """Checks if player meets stat, item, and resource requirements."""
        # Check Flow Bypass Availability (Data-Driven)
        has_flow_bypass = False
        bypass_cost = blessing.metadata.get('flow_bypass_cost', 0) if hasattr(blessing, 'metadata') else 0
        if bypass_cost > 0 and player.ext_state.get('monk', {}).get('flow_pips', 0) >= bypass_cost:
            has_flow_bypass = True

        # 0. Hard Gate: Stalled (Physical Lockout)
        if "stalled" in getattr(player, 'status_effects', {}) and not has_flow_bypass:
            # If a command was passed, queue it instead of failing.
            if command:
                if not hasattr(player, 'command_queue'):
                    player.command_queue = []
                # To prevent spam, only queue one command.
                if not player.command_queue:
                    player.command_queue.append(command)
                    player.send_line(f"{Colors.YELLOW}You are stalled. Your action has been queued.{Colors.RESET}")
                return False, "Command Queued"
            return False, f"{Colors.RED}You are too exhausted to act!{Colors.RESET}"
            
        # Class Gate (Strict Class-Based System)
        req_class = blessing.requirements.get('class')
        if req_class:
            if not hasattr(player, 'active_class') or player.active_class != req_class:
                return False, f"You must be a {req_class.title()} to use this."

        # Dynamic Cost Check (Calculated early for Shattered Mind logic)
        costs = Auditor.calculate_costs(blessing, player)

        # Event Hook for Logic Overrides (e.g. Monk Flow-Kick)
        ctx = {'player': player, 'blessing': blessing, 'costs': costs, 'command': command}
        event_engine.dispatch("on_check_requirements", ctx)

        # --- Pacing / Stalled Logic ---
        weight = 1.0
        pool = 'combat'
        tags = getattr(blessing, 'identity_tags', [])
        if "movement" in tags:
            weight = 0.5
            pool = 'travel'
        
        can_pace, reason_pace = check_pacing(player, weight=weight, limit=5.0, pool=pool)
        if not can_pace:
            return False, reason_pace

        # Terrain Check
        req_terrain = blessing.requirements.get('terrain')
        if req_terrain:
            if isinstance(req_terrain, str):
                req_terrain = [req_terrain]
            
            if player.room.terrain not in req_terrain:
                return False, f"Requires terrain: {', '.join(req_terrain)}"

        # State Check (Generalized for all classes)
        req_stance = blessing.requirements.get('stance')
        if req_stance:
            active_class = getattr(player, 'active_class', None)
            if active_class:
                # GCA Protocol: Class data lives in ext_state[class_name]
                p_stance = player.ext_state.get(active_class, {}).get('stance')
                if p_stance != req_stance:
                    return False, f"You must be in {req_stance.replace('_', ' ').title()} stance."
            else:
                return False, "This maneuver requires a combat stance."
            
        # [V4.5 Robustness] Boolean requirements should use truthy checks 
        # to account for variations in JSON encoders (True vs 1).
        if blessing.requirements.get('mount') and not getattr(player, 'is_mounted', False):
            return False, "You must be mounted to use this maneuver."

        # Weight Class Gate (MVP)
        req_weight = blessing.requirements.get('max_weight_class')
        if req_weight == 'light' and getattr(player, 'is_heavy', False):
            return False, "You are too heavy to perform this maneuver!"

        # Arbitrary Status Requirements (e.g. "concealed": True)
        for req_key, req_val in blessing.requirements.items():
            if req_key in ["stamina", "concentration", "chi", "stability", "class", "terrain", "stance", "mount", "shield", "equipped_weapon_type", "max_weight_class", "martial", "arcane", "divine", "nature", "instinct", "song"]:
                continue
            
            if req_val is True:
                if req_key not in getattr(player, 'status_effects', {}):
                    return False, f"Requires status: {req_key.replace('_', ' ').title()}"
            elif req_val is False:
                if req_key in getattr(player, 'status_effects', {}):
                    return False, f"Cannot have status: {req_key.replace('_', ' ').title()}"

        # Equipment Check
        req_shield = blessing.requirements.get('shield')
        if req_shield:
            has_shield = False
            # Check Body Armor (Legacy/Simple)
            if player.equipped_armor and ("shield" in player.equipped_armor.name.lower() or "buckler" in player.equipped_armor.name.lower()):
                has_shield = True
            # Check Offhand Slot (Standard)
            if player.equipped_offhand and ("shield" in player.equipped_offhand.name.lower() or "buckler" in player.equipped_offhand.name.lower()):
                has_shield = True
            
            if not has_shield:
                return False, "You must have a shield equipped."
                
        req_weapon_type = blessing.requirements.get('equipped_weapon_type')
        if req_weapon_type:
            if not player.equipped_weapon or req_weapon_type not in player.equipped_weapon.name.lower():
                return False, f"Requires a {req_weapon_type} to be equipped."

        # Stability check removed (Legacy)

        if costs[Tags.CONCENTRATION] > 0:
            # Mage Overcast Logic (Arcane Breakthrough)
            if getattr(player, 'breakthroughs', {}).get('arcane'):
                pass
            elif player.resources.get(Tags.CONCENTRATION, 0) < costs[Tags.CONCENTRATION]:
                return False, "You lack the Concentration!"

        # Strategic Balance: Double Stamina Cost if on GCD (Over-exertion)
        if hasattr(player, 'cooldowns') and 'gcd' in player.cooldowns:
            game = getattr(player, 'game', None)
            current_tick = game.tick_count if game else 0
            # Don't double if Flow Bypass is active
            is_flow_bypass = (bypass_cost > 0 and player.ext_state.get('monk', {}).get('flow_pips', 0) >= bypass_cost)
            
            if player.cooldowns['gcd'] > current_tick and not is_flow_bypass:
                costs["stamina"] *= 2

        if costs["stamina"] > 0:
            current_stamina = player.resources.get("stamina", 0)
            if current_stamina < costs["stamina"]:
                return False, "Not enough Stamina."

        if costs[Tags.CHI] > 0:
            if player.resources.get(Tags.CHI, 0) < costs[Tags.CHI]:
                return False, "Not enough Chi."

        # Mandatory Cooldown Check (Tactical Friction)
        if hasattr(player, 'cooldowns') and blessing.id in player.cooldowns:
            game = getattr(player, 'game', None)
            current_tick = game.tick_count if game else 0
            if player.cooldowns[blessing.id] > current_tick:
                remaining = player.cooldowns[blessing.id] - current_tick
                
                # Flow Synergy: Burn Momentum to bypass
                if has_flow_bypass:
                    player.ext_state['monk']['flow_pips'] -= bypass_cost
                    player.send_line(f"{Colors.MAGENTA}[FLOW] You burn momentum to bypass the delay!{Colors.RESET}")
                    player.cooldowns[blessing.id] = 0
                # Buttery Buffer: If < 0.5s (0.25 ticks), queue it
                elif remaining <= 0.25 and args is not None:
                    player.pending_skill = {'skill': blessing, 'args': args}
                    player.send_line(f"{Colors.YELLOW}[!] You're off-balance, but preparing to strike...{Colors.RESET}")
                    return False, f"BUFFERED|{remaining * 2.0}"
                else:
                    return False, f"{Colors.YELLOW}[!] Your balance is too unsettled to use that again so soon.{Colors.RESET}"

        # Global Cooldown Check (GCD)
        if hasattr(player, 'cooldowns') and 'gcd' in player.cooldowns:
            game = getattr(player, 'game', None)
            current_tick = game.tick_count if game else 0
            if player.cooldowns['gcd'] > current_tick:
                if not has_flow_bypass:
                    remaining = player.cooldowns['gcd'] - current_tick
                    if remaining <= 0.25 and args is not None:
                        player.pending_skill = {'skill': blessing, 'args': args}
                        return False, f"BUFFERED|{remaining * 2.0}"
                    else:
                        player.send_line(f"{Colors.RED}[!] You over-exert yourself to act! (Double Stamina){Colors.RESET}")

        return True, "OK"

    @staticmethod
    def check_identity(blessing, player):
        """Checks if blessing is in the player's active kit."""
        if not hasattr(player, 'active_kit') or not player.active_kit:
            return False, "You do not have an active kit."
        
        if blessing.id in player.active_kit.get('blessings', []):
            return True, "OK"
        
        return False, "Blessing not in active kit."

    @staticmethod
    def can_invoke(blessing, player, command=None):
        """Runs all checks."""
        # Lazy import to prevent circular dependency with magic_engine
        from logic.engines import magic_engine

        valid_id, reason_id = Auditor.check_identity(blessing, player)
        if not valid_id: return False, reason_id

        valid_req, reason_req = Auditor.check_requirements(blessing, player, command=command)
        if not valid_req: return False, reason_req

        valid_cd, reason_cd = magic_engine.check_cooldown(player, blessing)
        if not valid_cd: return False, reason_cd

        valid_chg, reason_chg = magic_engine.check_charges(player, blessing)
        if not valid_chg: return False, reason_chg

        valid_item, reason_item = magic_engine.check_items(player, blessing)
        if not valid_item: return False, reason_item

        return True, "OK"

event_engine.subscribe("on_status_removed", on_status_removed)
