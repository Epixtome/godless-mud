import logic.handlers.command_manager as command_manager
from utilities.colors import Colors
from logic.core.utils import display_utils
from logic.constants import Tags
from logic.core.utils import combat_logic

@command_manager.register("score", "sc", category="information")
def score(player, args):
    """Character summary: Identity, Vitals, and Top Resonance."""
    width = 60
    player.send_line(f"\n{display_utils.render_header(player.name, width)}")
    
    # Identifiers removed from score per user request, moved to attributes.
    pass
    
    # 2. Vitals
    hp_pct = (player.hp / player.max_hp) * 100
    hp_color = Colors.GREEN if hp_pct > 50 else (Colors.YELLOW if hp_pct > 25 else Colors.RED)
    vitals = f"HP: {hp_color}{player.hp}/{player.max_hp}{Colors.RESET}"
    
    if hasattr(player, 'resources'):
        # Ensure resources are synced before display (Atomic cleanup)
        from logic.core.utils import player_logic
        player_logic.sync_resources(player)
        
        # Sort resources for consistent display
        order = ['stamina', 'concentration', 'heat', 'chi', 'momentum', 'balance']
        res_to_show = sorted(player.resources.items(), key=lambda x: order.index(x[0]) if x[0] in order else 99)
        
        for res, val in res_to_show:
            if val <= 0 and res not in ['stamina', 'balance', 'concentration']:
                continue # Hide empty specialized resources
                
            name = res.title()
            
            # Contextual Filtering & Renaming (GCA Standard)
            if res == 'concentration':
                if player.active_class in ['mage', 'wizard', 'sorcerer', 'red_mage', 'illusionist']:
                    name = 'Mana'
                elif player.active_class == 'warlock':
                    name = 'Void'
                    
            # Color Coding
            res_color = Colors.CYAN
            if res == 'stamina': res_color = Colors.GREEN
            elif res == 'balance': res_color = Colors.YELLOW
            elif res == Tags.HEAT: res_color = Colors.RED
            elif res == 'chi': res_color = Colors.WHITE
            elif res == 'momentum': res_color = Colors.YELLOW
            
            vitals += f" | {res_color}{name}: {val}{Colors.RESET}"

        # Class Specific Engine Resources (Entropy, Flow)
        if getattr(player, 'active_class', None) == 'warlock':
            ext = player.ext_state.get('warlock', {})
            ent = ext.get('entropy', 0)
            max_ent = ext.get('max_entropy', 100)
            player.send_line(f" {Colors.MAGENTA}Entropy: {Colors.BOLD}{ent}/{max_ent}{Colors.RESET}")
        elif getattr(player, 'active_class', None) == 'illusionist':
            ext = player.ext_state.get('illusionist', {})
            echoes = ext.get('echoes', 0)
            max_e = ext.get('max_echoes', 3)
            player.send_line(f" {Colors.CYAN}Echoes:  {Colors.BOLD}{echoes}/{max_e}{Colors.RESET}")

    player.send_line(f" {vitals}")

    # 2a. Active Status Effects (V4.5)
    if hasattr(player, 'status_effects') and player.status_effects:
        from logic.core import effects
        effect_list = []
        for eff_id in player.status_effects:
            eff_def = effects.get_effect_definition(eff_id, player.game)
            if eff_def:
                name = eff_def.get('name', eff_id).title()
                color = Colors.YELLOW
                if eff_id in effects.HARD_DEBUFFS or eff_id in effects.CRITICAL_STATES:
                    color = Colors.RED
                effect_list.append(f"{color}{name}{Colors.RESET}")
        if effect_list:
            player.send_line(f" Status: {', '.join(effect_list)}")

    # 2b. Beastmaster Pet (V4.5)
    if player.active_class == 'beastmaster':
        active_pet = None
        for mob in player.room.monsters:
            if getattr(mob, 'owner_id', None) == player.id:
                active_pet = mob
                break
        if active_pet:
            pet_hp_pct = (active_pet.hp / active_pet.max_hp) * 100
            p_color = Colors.GREEN if pet_hp_pct > 50 else Colors.RED
            player.send_line(f" {Colors.YELLOW}Pet: {Colors.CYAN}{active_pet.name}{Colors.RESET} [{p_color}HP: {active_pet.hp}/{active_pet.max_hp}{Colors.RESET}]")
            
    player.send_line(display_utils.render_line(width))
    
    # 3. Resonance Overview
    from logic.engines.resonance_engine import ResonanceAuditor
    ResonanceAuditor.calculate_resonance(player)
    
    player.send_line(f" {Colors.BOLD}ACTIVE RESONANCE (VOLTAGE){Colors.RESET}")
    if hasattr(player, 'current_tags') and player.current_tags:
        # Filter internal engine tags
        internal_tags = ['hidden', 'monk', 'mage', 'barbarian', 'knight', 'assassin', 'cleric', 'defiler', 'warlock', 'illusionist', 'beastmaster', 'red_mage']
        filtered = {k: v for k, v in player.current_tags.items() if v > 0 and k not in internal_tags}
        all_tags = sorted(filtered.items(), key=lambda x: x[1], reverse=True)
        
        # Show top 5 or all if fewer
        for tag, val in all_tags[:8]:
            bar = display_utils.render_progress_bar(val, 20, 20)
            player.send_line(f"  {tag.title():<15} {bar} {val}")
    
    # 4. Breakthroughs
    breakthroughs = [t.title() for t, v in player.current_tags.items() if v >= 10]
    if breakthroughs:
        player.send_line(f"\n {Colors.BOLD}BREAKTHROUGHS:{Colors.RESET} {', '.join(breakthroughs)}")
        
    # [V6.0] Combat Rating Display
    from logic.core.math import rating
    cr = rating.calculate_entity_rating(player)
    player.send_line(f"\n {Colors.BOLD}Combat Rating: {Colors.YELLOW}{cr}{Colors.RESET} GCR")
        
    player.send_line(f"\n {Colors.ITALIC}Resonance (Voltage) combines Soul power with Gear tags.{Colors.RESET}")
    player.send_line(f"{display_utils.render_line(width, '=')}")

@command_manager.register("attributes", "attr", "sheet", category="information")
def attributes(player, args):
    """Detailed breakdown of all active tags (Soul vs Gear)."""
    width = 60
    player.send_line(f"\n{display_utils.render_header('Resonance Breakdown', width, '-')}")
    
    from logic.engines.resonance_engine import ResonanceAuditor
    ResonanceAuditor.calculate_resonance(player)
    
    # 1. Identity (Moved from Score)
    cls_name = (player.game.world.classes.get(player.active_class).name if player.active_class in player.game.world.classes else "Wanderer")
    player.send_line(f" Name:     {Colors.BOLD}{player.name}{Colors.RESET}")
    player.send_line(f" Class:    {Colors.CYAN}{cls_name}{Colors.RESET}")
    player.send_line(f" Kingdom:  {Colors.BOLD}{player.kingdom.upper()}{Colors.RESET}")
    player.send_line(f" Wealth:   {Colors.YELLOW}{getattr(player, 'gold', 0)} gold{Colors.RESET}")
    player.send_line(display_utils.render_line(width, "-"))
    
    total_tags = player.current_tags or {}
    gear_tags = {}
    slots = ["equipped_weapon", "equipped_offhand", "equipped_armor", "equipped_head", 
             "equipped_neck", "equipped_arms", "equipped_hands", "equipped_legs", 
             "equipped_feet", "equipped_floating", "equipped_mount"]
             
    for slot in slots:
        item = getattr(player, slot, None)
        if item:
            tags = getattr(item, 'tags', [])
            if isinstance(tags, dict):
                for t, v in tags.items(): gear_tags[t] = gear_tags.get(t, 0) + v
            else:
                for t in tags: gear_tags[t] = gear_tags.get(t, 0) + 1
    
    header = display_utils.render_table_header(["TAG", "TOTAL", "SOUL", "GEAR"], [20, 8, 8, 8])
    player.send_line(f" {header}")
    player.send_line(display_utils.render_line(width, "-"))

    for tag in sorted(set(total_tags.keys()) | set(gear_tags.keys())):
        total = total_tags.get(tag, 0)
        gear = gear_tags.get(tag, 0)
        soul = total - gear
        if total <= 0: continue
        
        col = Colors.MAGENTA if soul > gear else (Colors.YELLOW if gear > soul else Colors.WHITE)
        row = display_utils.render_table_row([tag.title(), total, soul, gear], [20, 8, 8, 8], [col, "", "", ""])
        player.send_line(f" {row}")

    player.send_line(display_utils.render_line(width, "-"))
    # Determine Weight Class
    w_class = combat_logic.get_weight_class(player)
    crit_chance = combat_logic.get_crit_chance(player)

    player.send_line(f" Weight:   {w_class.upper()}")
    player.send_line(f" Crit:     {crit_chance:>3.1f}%")

    # [V6.0] Combat Rating Integration
    from logic.core.math import rating
    cr = rating.calculate_entity_rating(player)
    player.send_line(f" Rating:   {Colors.BOLD}{Colors.YELLOW}{cr}{Colors.RESET} GCR")
    
    player.send_line(display_utils.render_line(width, "-"))
    player.send_line(f" {Colors.ITALIC}Attributes: Soul = Deck/Passives | Gear = Equipped Items{Colors.RESET}")

@command_manager.register("stats", category="information")
def stats(player, args):
    """Displays combat mathematics (Power, Crit, Defense)."""
    width = 40
    player.send_line(f"\n{display_utils.render_header('Combat Math', width)}")
    
    from logic.core import combat
    
    est_dmg = combat.estimate_player_damage(player)
    crit = combat.estimate_crit_chance(player)
    defense = combat.estimate_defense(player)
    
    player.send_line(display_utils.render_labeled_value("Attack Power", est_dmg, 15, Colors.RED))
    player.send_line(display_utils.render_labeled_value("Crit Chance", f"{crit:.1f}%", 15, Colors.YELLOW))
    player.send_line(display_utils.render_labeled_value("Defense", defense, 15, Colors.CYAN))
    
    player.send_line(display_utils.render_line(width))
    hp_color = Colors.GREEN if player.hp > player.max_hp * 0.5 else Colors.RED
    player.send_line(display_utils.render_labeled_value("HP", f"{player.hp}/{player.max_hp}", 15, hp_color))
    player.send_line(display_utils.render_line(width))

@command_manager.register("favor", category="information")
def favor(player, args):
    """List favor with deities."""
    player.send_line(f"\n{display_utils.render_header('Divine Favor', 60)}")
    
    kingdoms = {"light": [], "dark": [], "instinct": []}
    for d in player.game.world.deities.values():
        if d.kingdom in kingdoms: kingdoms[d.kingdom].append(d)
            
    for k, deities in kingdoms.items():
        player.send_line(f"\n {Colors.BOLD}{k.title()} Kingdom{Colors.RESET}")
        for d in sorted(deities, key=lambda x: x.name):
            amount = player.favor.get(d.id, 0)
            player.send_line(f"  {d.name:<25}: {amount}")

@command_manager.register("synergies", "syn", category="information")
def list_synergies(player, args):
    """List active synergy bonuses."""
    player.send_line(f"\n{display_utils.render_header('Active Synergies', 60)}")
    
    if not hasattr(player, 'active_synergies') or not player.active_synergies:
        player.send_line(" No active synergies.")
        return

    for s_id in player.active_synergies:
        syn = player.game.world.synergies.get(s_id)
        if syn:
            bonuses = [f"+{val} {stat.upper()}" for stat, val in syn.bonuses.items()]
            player.send_line(f" {Colors.CYAN}{syn.name:<20}{Colors.RESET} {', '.join(bonuses)}")

@command_manager.register("effects", "afflictions", "aff", "manifestations", category="information")
def list_effects(player, args):
    """Detailed breakdown of active status effects and their durations."""
    if not player.status_effects:
        player.send_line("You have no active status effects.")
        return

    width = 60
    player.send_line(f"{display_utils.render_header('Status Effects', width)}")
    
    from logic.core import effects as fx_engine
    
    header = f" {Colors.CYAN}{'Effect':<20}{Colors.RESET} | {Colors.YELLOW}{'Time Remaining':<15}{Colors.RESET}"
    player.send_line(header)
    player.send_line(display_utils.render_line(width, "-"))

    current_tick = player.game.tick_count
    for eff_id, expiry in player.status_effects.items():
        eff_def = fx_engine.get_effect_definition(eff_id, player.game)
        if not eff_def: continue
        
        name = eff_def.get('name', eff_id).title()
        remaining = max(0, int((expiry - current_tick) * 2.0)) # 2s per tick
        
        color = Colors.WHITE
        if eff_id in fx_engine.HARD_DEBUFFS or eff_id in fx_engine.CRITICAL_STATES:
            color = Colors.RED
        elif eff_id in fx_engine.SOFT_DEBUFFS:
            color = Colors.YELLOW
            
        player.send_line(f" {color}{name:<20}{Colors.RESET} | {remaining:>3}s")

    player.send_line(display_utils.render_line(width))
