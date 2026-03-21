"""
logic/modules/mage/actions.py
Black Mage Skill Handlers: High-Damage Elemental offensive kit.
V7.2 Standard Refactor (Baking Branch).
"""
import asyncio
from logic.actions.registry import register
from logic.core import effects, resources, combat, perception
from logic.engines import action_manager, magic_engine
from utilities.colors import Colors
from logic import common

def _consume_resources(player, skill):
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)

def _ridge_check(player, target, skill_name):
    """[V7.2 Ridge Rule Protocol]"""
    if not perception.can_see(player, target):
        player.send_line(f"{Colors.YELLOW}Your {skill_name} is blocked by a ridge of terrain!{Colors.RESET}")
        return False
    return True

@register("triple_bolt")
def handle_triple_bolt(player, skill, args, target=None):
    """Setup/Builder: Instant cast."""
    target = common._get_target(player, args, target, "Unleash arcane bolts on whom?")
    if not target: return None, True
    
    if not _ridge_check(player, target, "Arcane Bolt"):
        return None, True

    player.send_line(f"{Colors.CYAN}You snap your fingers, launching three bolts of crackling force!{Colors.RESET}")
    
    for _ in range(3):
        if not combat.is_target_valid(player, target) or target.hp <= 0: break
        combat.handle_attack(player, target, player.room, player.game, blessing=skill)
        # [V7.2] URM
        resources.modify_resource(player, "concentration", 5, source="Triple Bolt")
        
    _consume_resources(player, skill)
    return target, True

@register("ignite")
def handle_ignite(player, skill, args, target=None):
    """Setup: 1.5s Cast."""
    target = common._get_target(player, args, target, "Ignite whom?")
    if not target: return None, True

    if not _ridge_check(player, target, "Ignite"):
        return None, True

    async def _unleash():
        if not target or target.room != player.room: return
        # Re-check Ridge Rule on unleash (V7.2)
        if not perception.can_see(player, target):
            player.send_line(f"{Colors.YELLOW}Your target has moved behind a ridge! The spell dissipates.{Colors.RESET}")
            return

        player.send_line(f"{Colors.RED}A searing ray of fire erupts from your hand!{Colors.RESET}")
        combat.handle_attack(player, target, player.room, player.game, blessing=skill)

    action_manager.start_action(player, 1.5, _unleash, tag="casting", fail_msg="Concentration broken!")
    _consume_resources(player, skill)
    return target, True

@register("frost_bolt")
def handle_frost_bolt(player, skill, args, target=None):
    """Setup: 1.5s Cast."""
    target = common._get_target(player, args, target, "Freeze whom?")
    if not target: return None, True

    if not _ridge_check(player, target, "Frost Bolt"):
        return None, True

    async def _unleash():
        if not target or target.room != player.room: return
        if not perception.can_see(player, target): return

        player.send_line(f"{Colors.PALE_BLUE}A jagged shard of ice streaks towards {target.name}!{Colors.RESET}")
        combat.handle_attack(player, target, player.room, player.game, blessing=skill)
        
        # [V7.2] Standard Logic: Interaction feedback
        if effects.has_effect(target, "wet"):
            effects.apply_effect(target, "frozen", 4)
            player.send_line(f"{Colors.CYAN}[SNAP FREEZE] The water on {target.name} solidifies instantly!{Colors.RESET}")

    action_manager.start_action(player, 1.5, _unleash, tag="casting", fail_msg="Concentration broken!")
    _consume_resources(player, skill)
    return target, True

@register("lightning_bolt")
def handle_lightning_bolt(player, skill, args, target=None):
    """Payoff/Grammar: 2s Cast. 2x vs Wet (JSON)."""
    target = common._get_target(player, args, target, "Strike whom with lightning?")
    if not target: return None, True

    if not _ridge_check(player, target, "Lightning Bolt"):
        return None, True

    async def _unleash():
        if not target or target.room != player.room: return
        if not perception.can_see(player, target): return
        
        player.send_line(f"{Colors.BOLD}{Colors.WHITE}KRAK-BOOM!{Colors.RESET} A jagged bolt of lightning descends!")
        if effects.has_effect(target, "wet"):
             player.send_line(f"{Colors.CYAN}[WET CIRCUIT] The current arcs through soaked flesh — SHATTERING FORCE!{Colors.RESET}")
        
        combat.handle_attack(player, target, player.room, player.game, blessing=skill)

    action_manager.start_action(player, 2.0, _unleash, tag="casting", fail_msg="Concentration broken!")
    _consume_resources(player, skill)
    return target, True

@register("pyroclasm")
def handle_pyroclasm(player, skill, args, target=None):
    """Finisher: 4s Cast. 3x vs Burning (JSON)."""
    target = common._get_target(player, args, target, "Select target for the end of everything.")
    if not target: return None, True

    if not _ridge_check(player, target, "Pyroclasm"):
        return None, True

    player.send_line(f"{Colors.BOLD}{Colors.RED}The air begins to boil around you...{Colors.RESET}")
    player.room.broadcast(f"{Colors.RED}The air around {player.name} begins to glow with an intense, white heat!{Colors.RESET}", exclude_player=player)

    async def _unleash():
        if not target or target.room != player.room: return
        if not perception.can_see(player, target): return
        
        has_burn = effects.has_effect(target, "burn")
        if has_burn:
            player.send_line(f"{Colors.BOLD}{Colors.RED}PYROCLASM!{Colors.RESET} The existing flames on {target.name} explode inward!")
            # [V7.2] Consume Status Protocol
            effects.remove_effect(target, "burn")
            effects.apply_effect(target, "staggered", 2)
        else:
            player.send_line(f"{Colors.RED}The fireball explodes with immense force.{Colors.RESET}")
            
        combat.handle_attack(player, target, player.room, player.game, blessing=skill)

    action_manager.start_action(player, 4.0, _unleash, tag="casting", fail_msg="Concentration broken!")
    _consume_resources(player, skill)
    return target, True

@register("blink")
def handle_blink(player, skill, args, target=None):
    """Mobility: Instant escape."""
    player.send_line(f"{Colors.CYAN}Blink!{Colors.RESET} You fold space and reappear nearby.")
    
    # [V7.2] URM Break CC
    for state in ["immobilized", "pinned", "stalled"]:
        if effects.has_effect(player, state):
            effects.remove_effect(player, state)
            player.send_line(f"{Colors.GREEN}You snap free of physical restraints!{Colors.RESET}")
            
    _consume_resources(player, skill)
    return None, True

@register("phase_shift")
def handle_phase_shift(player, skill, args, target=None):
    """Defense: Reaction."""
    player.send_line(f"{Colors.BOLD}{Colors.MAGENTA}You briefly shift into the Ethereal Plane.{Colors.RESET}")
    effects.apply_effect(player, "phase_shifted", 2)
    _consume_resources(player, skill)
    return None, True

@register("arcane_surge")
def handle_arcane_surge(player, skill, args, target=None):
    """Utility: Recovery."""
    player.send_line(f"{Colors.LIGHT_CYAN}You inhale raw mana currents!{Colors.RESET}")
    # [V7.2] URM
    resources.modify_resource(player, "concentration", 50, source="Arcane Surge")
    effects.apply_effect(player, "stalled", 2)
    _consume_resources(player, skill)
    return None, True

@register("artifice_view")
def handle_artifice_view(player, skill, args, target=None):
    """[V7.2] Artificer/Scholar: Detailed item analysis."""
    if not args:
        player.send_line("Analyze which item?")
        return None, True
        
    # Search inventory or room
    target_item = common.find_by_index(player.inventory + player.room.items, args)
    if not target_item:
        player.send_line(f"You don't see '{args}' here.")
        return None, True
        
    player.send_line(f"{Colors.CYAN}You channel arcane resonance into the structure of {target_item.name}...{Colors.RESET}\n")
    
    # Technical Data Extraction
    item_cr = getattr(target_item, 'combat_rating', 0)
    
    # 1. Header & ID
    player.send_line(f" {Colors.BOLD}Material Analysis: {Colors.RESET}{getattr(target_item, 'material', 'unknown').upper()}")
    player.send_line(f" {Colors.BOLD}Combat Rating:     {Colors.YELLOW}{item_cr}{Colors.RESET} GCR")
    
    # 2. Type Specifics
    if hasattr(target_item, 'damage_dice'): # Weapon
        player.send_line(f" {Colors.BOLD}Base Damage:       {Colors.RED}{target_item.damage_dice}{Colors.RESET}")
    if hasattr(target_item, 'defense'): # Armor
        player.send_line(f" {Colors.BOLD}Armor Defense:     {Colors.BLUE}{target_item.defense}{Colors.RESET}")
        player.send_line(f" {Colors.BOLD}Weight Class:      {getattr(target_item, 'weight_class', 'light').upper()}")
        
    # 3. Tags (The "Grammar")
    tags = getattr(target_item, 'tags', [])
    if isinstance(tags, dict):
        tag_str = ", ".join([f"{k}({v})" for k, v in tags.items()])
    else:
        tag_str = ", ".join(tags)
        
    player.send_line(f" {Colors.BOLD}Property Tags:     {Colors.MAGENTA}{tag_str}{Colors.RESET}")
    
    # 4. Resonance Details (Power Scaling)
    power = getattr(target_item, 'power', 1.0)
    if power > 1.0:
        player.send_line(f" {Colors.BOLD}Resonance Mult:    {power}x")
        
    _consume_resources(player, skill)
    return target_item, True
