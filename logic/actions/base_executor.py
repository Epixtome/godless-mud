"""
logic/actions/base_executor.py
The Generic Engine: Handles standard skills (Damage, Healing, Buffs) via Data.
"""
from logic.core import effects
from logic.engines import blessings_engine, magic_engine, combat_processor
from logic.actions.skill_utils import _apply_damage
from logic.common import find_by_index
from utilities.colors import Colors
from logic.constants import Tags

# --- Atomic Handlers ---

def do_damage(player, target, skill, power, **kwargs):
    """Deals damage to the target."""
    # Delegate to Combat Processor for Momentum/Telemetry/Messaging
    players_to_prompt = set()
    combat_processor.execute_attack(player, target, player.room, player.game, players_to_prompt, blessing=skill)
    
    # Process prompts immediately for command feedback
    for p in players_to_prompt:
        p.send_line("")
        p.send_line(p.get_prompt())
    
    if target.hp > 0 and not player.fighting:
        player.fighting = target
        player.state = "combat"

def do_heal(player, target, skill, power, **kwargs):
    """Heals the target."""
    amount = kwargs.get("amount", power)
    if isinstance(amount, float):
        amount = int(power * amount)
    from logic.core import resources
    resources.modify_resource(target, "hp", amount, source=player, context="Heal")
    
    player.send_line(f"{Colors.GREEN}You heal {target.name} for {amount}.{Colors.RESET}")
    if target != player and hasattr(target, 'send_line'):
        target.send_line(f"{Colors.GREEN}{player.name} heals you for {amount}.{Colors.RESET}")

STATUS_MAP = {
    'hidden': 'concealed',
    'sneaking': 'concealed',
    'stealth': 'concealed'
}

def do_status(player, target, skill, power, **kwargs):
    """Applies a status effect."""
    duration = blessings_engine.MathBridge.calculate_duration(skill, player)
    if "duration" in kwargs:
        duration = kwargs["duration"]

    effect_id = kwargs.get("effect_id", skill.id)
    
    # Redirect legacy status effects
    if effect_id in STATUS_MAP:
        effect_id = STATUS_MAP[effect_id]
    
    effects.apply_effect(target, effect_id, duration)
    player.send_line(f"You apply {skill.name} to {target.name}.")

def do_resource(player, target, skill, power, **kwargs):
    """Grants resources to the caster."""
    resource = kwargs.get("resource")
    amount = kwargs.get("amount", 1)
    
    if resource and hasattr(player, 'resources'):
        from logic.core import resources
        resources.modify_resource(player, resource, amount, source=player, context="Resource Skill")
        player.send_line(f"{Colors.YELLOW}You gain {amount} {resource.title()}.{Colors.RESET}")

COMMAND_MAP = {
    "damage": do_damage,
    "heal": do_heal,
    "status": do_status,
    "resource": do_resource
}

def execute(player, skill, args, target=None):
    """
    Standard execution flow:
    1. Identify Target
    2. Calculate Power
    3. Apply Effects (Iterate through Data)
    4. Consume Resources
    """
    # 1. Target Resolution
    if not target:
        if args:
            target = find_by_index(player.room.monsters + player.room.players, args)
            if not target:
                player.send_line("You don't see them here.")
                return None, True
        elif player.fighting:
            target = player.fighting
        else:
            # Self-targeting for beneficial skills if no args
            is_beneficial = "healing" in skill.identity_tags or "buff" in skill.identity_tags
            if is_beneficial:
                target = player
            else:
                player.send_line("Use skill on whom?")
                return None, True

    # 2. Calculate Power
    power = blessings_engine.MathBridge.calculate_power(skill, player, target)

    # 3. Resolve Effects
    # Check for explicit effects list in skill object or metadata
    effects = getattr(skill, 'effects', [])
        
    # Legacy Fallback: Construct effects from tags if missing
    if not effects:
        effects = []
        if Tags.HEALING in skill.identity_tags or Tags.RESTORATION in skill.identity_tags:
            effects.append({"type": "heal"})
        elif any(tag in skill.identity_tags for tag in [Tags.BUFF, Tags.PROTECTION, Tags.STANCE, Tags.MAGIC_DEF]):
            effects.append({"type": "status"})
        else:
            # Default to damage if not purely utility
            if Tags.UTILITY not in skill.identity_tags:
                effects.append({"type": "damage"})
        
        if "chi_builder" in skill.identity_tags:
            effects.append({"type": "resource", "resource": Tags.CHI, "amount": 1})

    # 4. Execute Effects
    for effect in effects:
        eff_type = effect.get("type")
        handler = COMMAND_MAP.get(eff_type)
        if handler:
            handler(player, target, skill, power, **effect)

    # Resources are consumed by the generic handler wrapper in skill_commands.py or here.
    # On-hit effects are already handled inside do_damage via execute_attack.
    # We only need to apply them here if the skill did NOT deal damage (e.g. a pure status skill).
    if target and "damage" not in [e.get("type") for e in effects]:
        blessings_engine.MathBridge.apply_on_hit(player, target, skill)

    # 5. Consume Resources
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)

    return target, True
