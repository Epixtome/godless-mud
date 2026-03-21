import logging
import asyncio
import random
from logic.core import event_engine, effects
from utilities.colors import Colors
from logic.core import combat
from utilities import combat_formatter
from utilities import telemetry
from logic.constants import Tags
from logic.engines import synergy_engine

logger = logging.getLogger("GodlessMUD")

def check_cooldown(player, blessing, game=None):
    """Checks if the blessing is on cooldown."""
    game_ref = game if game else getattr(player, 'game', None)
    if not hasattr(player, 'cooldowns'):
        return True, "OK"
    
    current_tick = game_ref.tick_count if game_ref else 0

    # 1. Global Cooldown Check
    if 'gcd' in player.cooldowns:
        remaining_gcd = player.cooldowns['gcd'] - current_tick
        if remaining_gcd > 0:
            # Note: Auditor.check_requirements allows acting with Double Stamina during GCD.
            # This check here acts as the strict final gate for automated actions.
            pass # We let Auditor handle GCD logic for flexibility, but update set_cooldown to be reliable.

    # 2. Skill Specific Check
    if blessing.id in player.cooldowns:
        remaining = player.cooldowns[blessing.id] - current_tick
        if remaining > 0:
            return False, f"{blessing.name} is on cooldown for {remaining}s."
            
    return True, "OK"

def set_cooldown(player, blessing, game=None):
    """Sets the cooldown for a blessing."""
    game_ref = game if game else getattr(player, 'game', None)
    if not hasattr(player, 'cooldowns'):
        player.cooldowns = {}
    
    cd_ticks = blessing.requirements.get('cooldown', 0)
    if cd_ticks == 0:
        cd_ticks = getattr(blessing, 'cooldown', 0)
    
    # EVENT: Calculate Cooldown
    ctx = {'player': player, 'skill': blessing, 'cooldown': cd_ticks}
    event_engine.dispatch("magic_calculate_cooldown", ctx)
    final_ticks = max(0, int(ctx['cooldown']))
    
    # Set Skill Specific Cooldown
    if final_ticks > 0 and game_ref:
        target_tick = game_ref.tick_count + final_ticks
        current_tick = player.cooldowns.get(blessing.id, 0)
        player.cooldowns[blessing.id] = max(current_tick, target_tick)
        
    # [V5.6] Enforce Global Cooldown (1 Tick = 2.0s) ALWAYS
    if game_ref:
        gcd_target = game_ref.tick_count + 1
        player.cooldowns['gcd'] = max(player.cooldowns.get('gcd', 0), gcd_target)

def clear_all_cooldowns(player):
    """[V7.2] Resets all skill-specific cooldowns. Preserves GCD."""
    if not hasattr(player, 'cooldowns'):
        return
        
    gcd = player.cooldowns.get('gcd', 0)
    player.cooldowns = {'gcd': gcd}
    player.send_line(f"{Colors.BOLD}{Colors.GREEN}FEEL THE RUSH! All your skill cooldowns have been reset!{Colors.RESET}")

def check_resources(player, blessing):
    """
    Checks if player has resources. 
    UTS Directive: Concentration/Stamina checks removed.
    Only checks Chi if applicable.
    """
    reqs = blessing.requirements
    
    # Hard check for Chi (Preserved for specific mechanics)
    chi_cost = reqs.get('chi', 0)
    if player.resources.get('chi', 0) < chi_cost:
        return False, "Not enough Chi."
        
    return True, "OK"

def check_items(player, blessing):
    """Checks if player has required reagents."""
    # Placeholder for reagent logic
    return True, "OK"

def check_charges(player, blessing):
    """Checks if the blessing has charges remaining."""
    max_charges = getattr(blessing, 'charges', 0)
    if max_charges <= 0:
        return True, "OK"
        
    if not hasattr(player, 'blessing_charges'):
        player.blessing_charges = {}
        
    current = player.blessing_charges.get(blessing.id, max_charges)
    if current <= 0:
        return False, f"Not enough charges for {blessing.name}."
    return True, "OK"

def get_potency_multiplier(player, blessing):
    """Calculates potency reduction based on mental state."""
    # Absolute Restoration Penalty: 50% healing if in Mental Debt
    if Tags.RESTORATION in blessing.identity_tags:
        if player.resources.get(Tags.CONCENTRATION, 0) <= 0:
            return 0.5
    return 1.0

def consume_resources(player, blessing):
    """
    Consumes resources and handles Overcast penalties.
    """
    if getattr(player, 'godmode', False):
        return

    consume_charges(player, blessing)

    # Calculate Dynamic Costs
    from logic.engines.blessings.auditor import Auditor
    costs = Auditor.calculate_costs(blessing, player, verbose=True)
    reqs = blessing.requirements

    # Prepare Cost Context
    ctx = {
        'player': player,
        'skill': blessing,
        'costs': {} 
    }
    
    # [V6.0] Hybrid Cost/CD Harvesting
    costs = Auditor.calculate_costs(blessing, player, ctx=ctx)
    ctx['costs'] = costs

    # Trigger Synergy Hooks (Red Mage Charge Generation)
    synergy_engine.on_blessing_cast(player, blessing)

    # Trigger Class Mechanics (Decoupled via Events)
    event_engine.dispatch("magic_on_blessing_cast", ctx)
    
    # EVENT: Calculate Cost
    event_engine.dispatch("magic_calculate_cost", ctx)
    final_costs = ctx['costs']
    
    # Determine primary cost for logging (Stability for Martial, Conc for Spells)
    primary_cost = final_costs.get('concentration', 0)
    if final_costs.get('stamina', 0) > 0:
        primary_cost = final_costs.get('stamina', 0)

    # TELEMETRY HOOK: Log calculated costs before application
    if primary_cost > 0:
        telemetry.log_resource_delta(
            player, 
            "COST_CALC", 
            -primary_cost, 
            blessing.name, 
            context=f"Stamina:{final_costs.get('stamina',0)} Conc:{final_costs.get('concentration',0)}"
        )

    # [V6.0] Unified Resource Consumption via Centralized logic
    from logic.core import resources
    for res_name, cost_val in final_costs.items():
        if cost_val > 0 and res_name not in [Tags.CONCENTRATION]:
            resources.modify_resource(player, res_name, -cost_val, source=blessing.name, context="Consumed")

    # Concentration Consumption & Negative Dip
    conc_cost = final_costs.get('concentration', 0)
    if conc_cost > 0:
        current = player.resources.get('concentration', 0)
        
        if current < conc_cost:
            # Overcast Logic (Arcane Breakthrough)
            # We assume check_requirements already validated the breakthrough exists
            deficit = conc_cost - current
            
            # Set Concentration to 0
            player.resources[Tags.CONCENTRATION] = -deficit # Go into debt
            
            # HP Drain (Burn)
            from logic.core import resources
            resources.modify_resource(player, "hp", -deficit, source="Overcast", context="HP Burn")
            player.send_line(f"{Colors.YELLOW}You burn {deficit} HP to fuel the spell!{Colors.RESET}")
            
            # Transcendent Will: Generate +20 Heat per cast
            heat_surge = 20
            from logic.core import resources
            resources.modify_resource(player, Tags.HEAT, heat_surge, source="Overcast", context="Heat Surge")
            player.send_line(f"{Colors.RED}The surge of raw magic overheats you! (+{heat_surge} Heat){Colors.RESET}")
            
            # Telemetry for Burn
            telemetry.log_resource_delta(
                player,
                "OVERCAST",
                -deficit,
                blessing.name,
                context=f"HP Burn: {deficit} | Heat Surge: {heat_surge}"
            )
        else:
            player.resources['concentration'] = current - conc_cost
            
            # TELEMETRY HOOK: Log actual subtraction
            telemetry.log_resource_delta(
                player,
                "CONC",
                -conc_cost,
                blessing.name,
                context="Consumed"
            )

def consume_charges(player, blessing):
    """Decrements a charge from the blessing."""
    max_charges = getattr(blessing, 'charges', 0)
    if max_charges <= 0:
        return
        
    if not hasattr(player, 'blessing_charges'):
        player.blessing_charges = {}
        
    current = player.blessing_charges.get(blessing.id, max_charges)
    player.blessing_charges[blessing.id] = max(0, current - 1)

def check_pacing(player, blessing):
    """
    Checks if the player has exceeded their actions per round.
    UTS Directive: Pacing is governed strictly by cooldowns.
    Legacy round-based pacing is disabled.
    """
    return True, "OK"

def consume_pacing(player, blessing):
    """
    Legacy pacing consumption.
    UTS Directive: Pacing is governed strictly by cooldowns.
    """
    pass
