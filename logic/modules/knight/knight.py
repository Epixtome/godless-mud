"""
logic/modules/knight/knight.py
The Knight Domain: Defense, Mounted Combat, and Protection.
"""
from logic.actions.registry import register
from logic.core import event_engine, effects, resources
from logic.engines import action_manager, blessings_engine, magic_engine
from logic.actions.skill_utils import _apply_damage
from utilities.colors import Colors
from logic import common

def _consume_resources(player, skill):
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)

# --- SKILL HANDLERS ---

@register("brace")
def handle_brace(player, skill, args, target=None):
    """Increase mitigation for a short duration."""
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}You plant your feet and brace for impact!{Colors.RESET}")
    # Use generic executor to apply status effects (braced) from JSON
    from logic.actions.base_executor import execute as handle_generic
    handle_generic(player, skill, args, target=player)
    return None, True

@register("shield_bash")
def handle_shield_bash(player, skill, args, target=None):
    """Slam target with a shield, potentially knocking them off-balance."""
    target = common._get_target(player, args, target, "Shield bash whom?")
    if not target: return None, True

    # Shield Check already handled by Auditor.check_requirements.
    
    # Delegate to processor for damage and on_hit (off_balance)
    from logic.engines import combat_processor
    prompts = set()
    combat_processor.execute_attack(player, target, player.room, player.game, prompts, blessing=skill)
    
    _consume_resources(player, skill)
    return target, True

@register("mount")
def handle_mount(player, skill, args, target=None):
    """Summon/Mount a steed."""
    if player.is_mounted:
        player.is_mounted = False
        player.send_line("You dismount your steed.")
        player.room.broadcast(f"{player.name} dismounts.", exclude_player=player)
    else:
        player.is_mounted = True
        player.send_line(f"{Colors.YELLOW}You mount your noble steed!{Colors.RESET}")
        player.room.broadcast(f"{player.name} mounts a noble steed!", exclude_player=player)
    
    _consume_resources(player, skill)
    return None, True

@register("charge")
def handle_charge(player, skill, args, target=None):
    """High speed rush into a target."""
    target = common._get_target(player, args, target, "Charge at whom?")
    if not target: return None, True

    player.send_line(f"{Colors.BOLD}{Colors.CYAN}You charge at {target.name}!{Colors.RESET}")
    player.room.broadcast(f"{player.name} charges at {target.name}!", exclude_player=player)

    power = blessings_engine.calculate_power(skill, player, target)
    if player.is_mounted:
        power = int(power * 1.5)
        player.send_line(f"{Colors.YELLOW}[Mounted Charge Bonus!]{Colors.RESET}")

    _apply_damage(player, target, power, "Charge")
    
    # Initialize combat if not fighting
    if not player.fighting:
        player.fighting = target
        player.state = "combat"

    _consume_resources(player, skill)
    return target, True

@register("intervene")
def handle_intervene(player, skill, args, target=None):
    """Protect an ally by redirecting aggro or taking hits."""
    target_player = None
    if args:
        target_player = player.room.find_player(args)
    
    if not target_player:
        # If in combat, try to find an ally being attacked
        allies = [p for p in player.room.players if p != player and p.attackers]
        if allies: target_player = allies[0]

    if not target_player or target_player == player:
        player.send_line("You cannot Intervene for yourself. You are already the center of your own attention.")
        return None, True

    player.send_line(f"{Colors.WHITE}You place yourself between {target_player.name} and their foes!{Colors.RESET}")
    player.room.broadcast(f"{player.name} leaps to protect {target_player.name}!", exclude_player=player)

    # Aggro Redirection: Take over attackers
    for attacker in target_player.attackers[:]:
        attacker.fighting = player
        if player not in attacker.attackers: # Wait, attackers list is on the target.
            # attacker is a mob or player.
            # victim = target_player.
            pass
        
        # Mobs have .fighting = player.
        # Player (attacker) has .fighting = player.
        
        if attacker not in player.attackers:
            player.attackers.append(attacker)
        if attacker in target_player.attackers:
            target_player.attackers.remove(attacker)

    _consume_resources(player, skill)
    return target_player, True

@register("rescue")
def handle_rescue(player, skill, args, target=None):
    """Legacy alias for Intervene."""
    return handle_intervene(player, skill, args, target)

@register("stand")
def handle_stand(player, skill, args, target=None):
    """Recover from prone/resting state."""
    if player.state == "resting":
        player.state = "normal"
        player.send_line("You stand up.")
        player.room.broadcast(f"{player.name} stands up.", exclude_player=player)
    else:
        player.send_line("You are already standing.")
    
    _consume_resources(player, skill)
    return None, True

def handle_stomp(player, skill, args, target=None):
    """AoE Stomp."""
    player.send_line(f"{Colors.BOLD}You stomp the ground with massive force!{Colors.RESET}")
    player.room.broadcast(f"{player.name} stomps the ground, causing a shockwave!", exclude_player=player)
    
    targets = [m for m in player.room.monsters] + [p for p in player.room.players if p != player]
    power = blessings_engine.calculate_power(skill, player)
    
    for t in targets:
        _apply_damage(player, t, int(power * 0.5), "Stomp")
        effects.apply_effect(t, "off_balance", 2)
        
    _consume_resources(player, skill)
    return None, True

@register("execute")
def handle_execute(player, skill, args, target=None):
    """Payoff: Finishing blow on a Prone target. Deals 3x damage."""
    target = common._get_target(player, args, target, "Execute whom?")
    if not target: return None, True

    # The prone:true requirement is already gated in auditor.check_requirements.
    # We know they're prone if we get here.
    player.send_line(f"{Colors.BOLD}{Colors.RED}EXECUTE! You bring your weapon down with crushing finality!{Colors.RESET}")
    player.room.broadcast(f"{Colors.RED}{player.name} executes a devastating finishing blow on the prone {target.name}!{Colors.RESET}", exclude_player=player)

    # Apply 3x damage multiplier for this strike only
    player.execute_multiplier = 3.0
    try:
        from logic.engines import combat_processor
        prompts = set()
        combat_processor.execute_attack(player, target, player.room, player.game, prompts, blessing=skill)
    finally:
        if hasattr(player, 'execute_multiplier'):
            del player.execute_multiplier

    # Knock them out of prone — the execution ends their grounded state
    effects.remove_effect(target, "prone", verbose=False)

    _consume_resources(player, skill)
    return target, True
