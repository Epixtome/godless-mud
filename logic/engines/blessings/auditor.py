import logging
from utilities.colors import Colors
from logic.constants import Tags
from logic.core import event_engine
from logic.core import effects
from logic import calibration
from utilities import telemetry
# Re-export pacing functions to maintain API compatibility with blessings_engine
from .pacing import check_pacing, on_status_removed

logger = logging.getLogger("GodlessMUD")

class Auditor:
    """Handles validation of requirements and identity."""

    @staticmethod
    def calculate_costs(blessing, player=None, verbose=False, ctx=None):
        """
        [V6.0] Extracts resource costs directly from data.
        Pillar: Systems should be agnostic to the 'Name' of the resource.
        """
        reqs = getattr(blessing, 'requirements', {})
        
        # 1. Harvest all numeric requirements as costs
        costs = {}
        for key, val in reqs.items():
            if isinstance(val, (int, float)) and key not in ["class", "cooldown", "count", "tier", "terrain", "mount", "shield"]:
                costs[key] = val
        
        # 2. Dynamic Rule Evaluation (Passives)
        if player and hasattr(player, 'equipped_blessings'):
            for b_id in player.equipped_blessings:
                pass_blessing = player.game.world.blessings.get(b_id) if hasattr(player, 'game') else None
                if pass_blessing and getattr(pass_blessing, 'logic_type', None) == 'passive':
                    rules = getattr(pass_blessing, 'potency_rules', [])
                    for rule in rules:
                        if rule.get('type') == 'cost_mod':
                            status_id = rule.get('status_id')
                            if not status_id or effects.has_effect(player, status_id):
                                target_res = rule.get('resource', 'stamina')
                                if target_res in costs:
                                    costs[target_res] = int(costs[target_res] * rule.get('multiplier', 1.0))
                        
                        elif rule.get('type') == 'cooldown_mod' and ctx is not None and 'cooldown' in ctx:
                             status_id = rule.get('status_id')
                             if not status_id or effects.has_effect(player, status_id):
                                 ctx['cooldown'] *= rule.get('multiplier', 1.0)
        
        # 3. Weight Class Stamina Penalties (Physical Law)
        if player and "stamina" in costs:
            from logic.core.utils import combat_logic
            w_class = combat_logic.get_weight_class(player)
            if w_class == "heavy":
                costs["stamina"] = int(costs["stamina"] * calibration.CombatBalance.STAMINA_PENALTY_HEAVY)
            elif w_class == "medium":
                costs["stamina"] = int(costs["stamina"] * calibration.CombatBalance.STAMINA_PENALTY_MEDIUM)

        # Legacy Hook
        if player and blessing:
            event_ctx = {'player': player, 'blessing': blessing, 'costs': costs}
            event_engine.dispatch("on_calculate_skill_cost", event_ctx)
        
        return costs

    @staticmethod
    def check_requirements(blessing, player, command=None, args=None):
        """Checks if player meets stat, item, and resource requirements."""
        has_flow_bypass = False
        bypass_cost = blessing.metadata.get('flow_bypass_cost', 0) if hasattr(blessing, 'metadata') else 0
        if bypass_cost > 0 and player.ext_state.get('monk', {}).get('flow_pips', 0) >= bypass_cost:
            has_flow_bypass = True

        if "stalled" in getattr(player, 'status_effects', {}) and not has_flow_bypass:
            if command:
                if not hasattr(player, 'command_queue'):
                    player.command_queue = []
                if not player.command_queue:
                    player.command_queue.append(command)
                    player.send_line(f"{Colors.YELLOW}You are stalled. Your action has been queued.{Colors.RESET}")
                return False, "Command Queued"
            return False, f"{Colors.YELLOW}[!] You are momentarily off-balance and cannot use skills.{Colors.RESET}"
            
        req_class = blessing.requirements.get('class')
        if req_class:
            if not hasattr(player, 'active_class') or player.active_class != req_class:
                return False, f"You must be a {req_class.title()} to use this."

        ctx = {'player': player, 'blessing': blessing, 'command': command}
        costs = Auditor.calculate_costs(blessing, player, ctx=ctx)
        ctx['costs'] = costs

        event_engine.dispatch("on_check_requirements", ctx)

        weight = 1.0
        pool = 'combat'
        tags = getattr(blessing, 'identity_tags', [])
        if "movement" in tags:
            weight = 0.5
            pool = 'travel'
        
        can_pace, reason_pace = check_pacing(player, weight=weight, limit=5.0, pool=pool)
        if not can_pace: return False, reason_pace

        req_terrain = blessing.requirements.get('terrain')
        if req_terrain:
            if isinstance(req_terrain, str): req_terrain = [req_terrain]
            if player.room.terrain not in req_terrain:
                return False, f"Requires terrain: {', '.join(req_terrain).replace('_', ' ').title()}"

        # [V6.3] Environmental Gate: Weather Requirements
        req_weather = blessing.requirements.get('weather')
        if req_weather:
            if isinstance(req_weather, str): req_weather = [req_weather]
            current_weather = player.room.get_weather()
            if current_weather not in req_weather:
                 return False, f"The environmental conditions ({current_weather.replace('_', ' ')}) are unsuitable for {blessing.name}."

        req_stance = blessing.requirements.get('stance')
        if req_stance:
            active_class = getattr(player, 'active_class', None)
            if active_class:
                p_stance = player.ext_state.get(active_class, {}).get('stance')
                if p_stance != req_stance:
                    return False, f"You must be in {req_stance.replace('_', ' ').title()} stance."
            else:
                return False, "This maneuver requires a combat stance."
            
        req_mount = blessing.requirements.get('mount')
        if req_mount and not getattr(player, 'is_mounted', False):
            return False, "You must be mounted to use this maneuver."

        req_weight = blessing.requirements.get('max_weight_class')
        if req_weight == 'light' and getattr(player, 'is_heavy', False):
            if player.get_global_tag_count("juggernaut") == 0:
                return False, "You are too heavy to perform this maneuver!"

        # These requirement keys are evaluated on the TARGET, not the player.
        TARGET_STATUS_REQUIREMENTS = {"prone", "blinded", "dazed", "confused", "stunned", "off_balance", "wet", "frozen", "burning"}

        for req_key, req_val in blessing.requirements.items():
            if req_key in ["stamina", "concentration", "chi", "stability", "class", "terrain", "stance",
                           "mount", "shield", "equipped_weapon_type", "max_weight_class", "cooldown",
                           "weapon", "fighting"] or req_key in TARGET_STATUS_REQUIREMENTS:
                continue
            
            if req_val is True:
                if req_key not in getattr(player, 'status_effects', {}):
                    return False, f"Requires status: {req_key.replace('_', ' ').title()}"
            elif req_val is False:
                if req_key in getattr(player, 'status_effects', {}):
                    return False, f"Cannot use while: {req_key.replace('_', ' ').title()}"
            
            elif isinstance(req_val, (int, float)):
                curr_val = 0
                if player.active_class and req_key in player.ext_state.get(player.active_class, {}):
                    curr_val = player.ext_state[player.active_class].get(req_key, 0)
                elif req_key in player.resources:
                    curr_val = player.resources[req_key]
                
                if curr_val < req_val:
                    return False, f"Not enough {req_key.title()} ({curr_val}/{req_val})"

        req_fighting = blessing.requirements.get('fighting')
        if req_fighting is True and not getattr(player, 'fighting', None):
            return False, f"You must be in combat to use {blessing.name}."
        elif req_fighting is False and getattr(player, 'fighting', None):
             return False, f"You cannot be in combat to use {blessing.name}."

        # --- TARGET STATUS GATE ---
        # Check status requirements that apply to the CURRENT TARGET (player.fighting)
        target = getattr(player, 'fighting', None)
        for req_key in TARGET_STATUS_REQUIREMENTS:
            req_val = blessing.requirements.get(req_key)
            if req_val is None:
                continue
            if req_val is True:
                if not target:
                    return False, f"You must be in combat to use {blessing.name}."
                t_effects = getattr(target, 'status_effects', {})
                if req_key not in t_effects:
                    status_name = req_key.replace('_', ' ').title()
                    return False, f"Target must be [{status_name}]. Set it up first."
            elif req_val is False:
                if target:
                    t_effects = getattr(target, 'status_effects', {})
                    if req_key in t_effects:
                        return False, f"Cannot use while target is [{req_key.replace('_', ' ').title()}]."

        req_weapon = blessing.requirements.get('weapon')
        if req_weapon and not player.equipped_weapon:
            return False, f"You must have a weapon equipped to use {blessing.name}."

        req_shield = blessing.requirements.get('shield')
        if req_shield:
            has_shield = False
            if player.equipped_armor and any(s in player.equipped_armor.name.lower() for s in ["shield", "buckler", "pavise", "targe"]):
                has_shield = True
            if player.equipped_offhand and any(s in player.equipped_offhand.name.lower() for s in ["shield", "buckler", "pavise", "targe"]):
                has_shield = True
            if not has_shield:
                return False, f"You must have a shield equipped to use {blessing.name}."
                
        req_weapon_type = blessing.requirements.get('equipped_weapon_type')
        if req_weapon_type:
            if not player.equipped_weapon or req_weapon_type not in player.equipped_weapon.name.lower():
                return False, f"Requires a {req_weapon_type} to be equipped to use {blessing.name}."

        if costs:
            for res_name, res_cost in costs.items():
                curr_val = player.resources.get(res_name, 0)
                if curr_val < res_cost:
                    return False, f"Not enough {res_name.title()}."

        if hasattr(player, 'cooldowns') and blessing.id in player.cooldowns:
            game = getattr(player, 'game', None)
            current_tick = game.tick_count if game else 0
            if player.cooldowns[blessing.id] > current_tick:
                remaining = player.cooldowns[blessing.id] - current_tick
                if has_flow_bypass:
                    player.ext_state['monk']['flow_pips'] -= bypass_cost
                    player.send_line(f"{Colors.MAGENTA}[FLOW] You burn momentum to bypass the delay!{Colors.RESET}")
                    player.cooldowns[blessing.id] = 0
                elif remaining <= 0.25 and args is not None:
                    player.pending_skill = {'skill': blessing, 'args': args}
                    player.send_line(f"{Colors.YELLOW}[!] Skill queued. Preparing to strike...{Colors.RESET}")
                    return False, f"BUFFERED|{remaining * 2.0}"
                else:
                    return False, f"{Colors.YELLOW}[!] You are still recovering your focus. ({remaining * 2.0:.1f}s remaining){Colors.RESET}"

        if hasattr(player, 'cooldowns') and 'gcd' in player.cooldowns:
            game = getattr(player, 'game', None)
            current_tick = game.tick_count if game else 0
            if player.cooldowns['gcd'] > current_tick:
                if not has_flow_bypass:
                    remaining = player.cooldowns['gcd'] - current_tick
                    if remaining <= 0.25 and args is not None:
                        player.pending_skill = {'skill': blessing, 'args': args}
                        player.send_line(f"{Colors.YELLOW}[!] Skill queued. Preparing to strike...{Colors.RESET}")
                        return False, f"BUFFERED|{remaining * 2.0}"
                    else:
                        player.send_line(f"{Colors.RED}[!] You over-exert yourself to act! (Double Stamina){Colors.RESET}")

        return True, "OK"

    @staticmethod
    def check_identity(blessing, player):
        if not hasattr(player, 'active_kit') or not player.active_kit:
            return False, "You do not have an active kit."
        if blessing.id in player.active_kit.get('blessings', []):
            return True, "OK"
        return False, "Blessing not in active kit."

    @staticmethod
    def can_invoke(blessing, player, command=None):
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
