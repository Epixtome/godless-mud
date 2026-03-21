"""
logic/commands/admin/kit_commands.py
Admin Workbench for Class & Grammar Development.
Allows real-time modification of kits and grammar rules to save tokens and speed up iteration.
"""
import json
import os
import logging
from logic.handlers.command_manager import register
from logic.core.math import grammar
from utilities.colors import Colors

logger = logging.getLogger("GodlessMUD")

KIT_FILE = "data/kits.json"
GRAMMAR_FILE = "data/grammar_rules.json"

def _load_json(path):
    if not os.path.exists(path): return {}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def _save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

@register("@classkit", "@ckit", category="admin", admin=True)
def cmd_class_kit(player, args):
    """
    Admin Class Kit Workbench (Enhanced V7.2).
    Usage:
      @classkit list                     - List all available kits.
      @classkit catalog [tag/axis/name]  - Search all blessings in the registry.
      @classkit view <kit_id>            - Detail the 8-ability composition.
      @classkit swap <kit_id> <slot_1_8> <blessing_id> - Swap a blessing in a kit.
      @classkit reload                   - Refresh all kits from disk.
    """
    if not args:
        return player.send_line("Usage: @classkit <list|catalog|view|swap|reload> [args]")
    
    parts = args.split()
    sub = parts[0].lower()
    kits = _load_json(KIT_FILE)

    if sub == "catalog":
        search = parts[1].lower() if len(parts) > 1 else None
        player.send_line(f"{Colors.BOLD}{Colors.BLUE}=== Blessing Registry Catalog ==={Colors.RESET}")
        count = 0
        for b_id, b in sorted(player.game.world.blessings.items()):
            tags = getattr(b, 'identity_tags', [])
            axis = getattr(b, 'axis', 'N/A')
            
            if search:
                match = (search in b_id or 
                         search in b.name.lower() or 
                         search == axis.lower() or 
                         any(search in t for t in tags))
                if not match: continue
            
            tag_str = f" {Colors.DGREY}[{', '.join(tags)}]{Colors.RESET}" if tags else ""
            axis_color = Colors.MAGENTA if axis != 'N/A' else Colors.DGREY
            player.send_line(f" {Colors.CYAN}{b.name:<25}{Colors.RESET} ID: {Colors.YELLOW}{b_id:<20}{Colors.RESET} {axis_color}{axis:<10}{Colors.RESET}{tag_str}")
            count += 1
            if count >= 150:
                player.send_line(f"{Colors.YELLOW}... too many results, try a more specific search.{Colors.RESET}")
                break
        
        if count == 0:
            player.send_line(" No blessings found matching your search.")
        return
        
    if sub == "list":
        player.send_line(f"{Colors.BOLD}{Colors.BLUE}=== Available Kits ==={Colors.RESET}")
        for k_id in sorted(kits.keys()):
            player.send_line(f" - {k_id}")
        return

    if sub == "view":
        if len(parts) < 2: return player.send_line("Specify a kit ID.")
        k_id = parts[1].lower()
        if k_id not in kits: return player.send_line(f"Kit '{k_id}' not found.")
        
        kit = kits[k_id]
        player.send_line(f"{Colors.BOLD}{Colors.BLUE}=== Kit: {kit.get('name', k_id)} (v{kit.get('version', 1)}) ==={Colors.RESET}")
        player.send_line(f"Description: {Colors.WHITE}{kit.get('description', 'N/A')}{Colors.RESET}")
        player.send_line(f"Axes: {Colors.CYAN}{', '.join(kit.get('axes', []))}{Colors.RESET}")
        player.send_line(f"{Colors.YELLOW}--- Abilities ---{Colors.RESET}")
        
        blessings = kit.get("blessings", [])
        for i in range(8):
            b_id = blessings[i] if i < len(blessings) else "---"
            # Attempt to resolve name from world
            b_obj = player.game.world.blessings.get(b_id)
            b_display = f"{b_obj.name} ({b_id})" if b_obj else b_id
            player.send_line(f" {i+1}. {b_display}")
        return

    if sub == "swap":
        if len(parts) < 4: return player.send_line("Usage: @classkit swap <kit> <slot_1_8> <blessing_id>")
        k_id = parts[1].lower()
        try:
            slot = int(parts[2]) - 1
            new_b = parts[3].lower()
        except ValueError:
            return player.send_line("Slot must be a number 1-8.")

        if k_id not in kits: return player.send_line(f"Kit '{k_id}' not found.")
        if slot < 0 or slot >= 8: return player.send_line("Slot must be between 1 and 8.")
        
        # Ensure new blessing exists
        if new_b not in player.game.world.blessings:
            player.send_line(f"{Colors.RED}[!] Blessing '{new_b}' not found in World Registry.{Colors.RESET}")
            return

        blessings = kits[k_id].get("blessings", [])
        # Ensure list is at least 8 long
        while len(blessings) < 8: blessings.append("---")
        
        old_b = blessings[slot]
        blessings[slot] = new_b
        kits[k_id]["blessings"] = blessings
        
        # [V7.2] Auto-Increment Version to trigger Migration for all players
        new_version = kits[k_id].get('version', 1) + 1
        kits[k_id]["version"] = new_version
        
        _save_json(KIT_FILE, kits)
        
        player.send_line(f"{Colors.GREEN}Success:{Colors.RESET} Swapped slot {slot+1} of {Colors.YELLOW}{k_id}{Colors.RESET} from {Colors.RED}{old_b}{Colors.RESET} to {Colors.GREEN}{new_b}{Colors.RESET}.")
        player.send_line(f"Kit {k_id} version bumped to {Colors.CYAN}v{new_version}{Colors.RESET}.")
        
        # [V7.2] Live Sync Protocol: Update active players immediately
        sync_count = 0
        for p in player.game.players.values():
            if getattr(p, 'active_class', None) == k_id:
                # Force reload which will trigger migrate_kit due to version bump
                p.load_kit(k_id)
                p.send_line(f"{Colors.BOLD}{Colors.MAGENTA}[OOC] Your class kit ({k_id}) has been updated by an Admin.{Colors.RESET}")
                sync_count += 1
        
        if sync_count > 0:
            player.send_line(f"{Colors.CYAN}Synchronized {sync_count} active players to the new kit composition.{Colors.RESET}")
            
        logger.info(f"Admin {player.name} swapped {k_id} slot {slot+1}: {old_b} -> {new_b} (v{new_version})")
        return

    if sub == "reload":
        # persistence.load_kit reads from disk every time, so this just confirms sync
        player.send_line(f"{Colors.GREEN}Kit Registry refreshed. Changes to kits.json are now live for new loads.{Colors.RESET}")
        return

@register("@grammar", category="admin", admin=True)
def cmd_grammar(player, args):
    """
    Admin Grammar Workbench.
    Usage:
      @grammar list                - List all active transitions.
      @grammar add <tag> <state>   - (Simplistic) add a trigger->result rule.
      @grammar reload              - Sync memory with data/grammar_rules.json.
    """
    if not args:
        return player.send_line("Usage: @grammar <list|reload|add>")
    
    parts = args.split()
    sub = parts[0].lower()
    
    if sub == "list":
        reg = grammar.get_registry()
        player.send_line(f"{Colors.BOLD}{Colors.BLUE}=== Active Grammar Transitions ==={Colors.RESET}")
        for rule in reg.get("transitions", []):
            trigger = rule.get("trigger_tag")
            result = rule.get("result_state")
            player.send_line(f" - {Colors.YELLOW}{trigger}{Colors.RESET} -> {Colors.GREEN}{result}{Colors.RESET} (ID: {rule.get('id')})")
        return

    if sub == "reload":
        grammar.reload_registry()
        player.send_line(f"{Colors.GREEN}Grammar Registry reloaded.{Colors.RESET}")
        return

    if sub == "add":
        if len(parts) < 3: return player.send_line("Usage: @grammar add <trigger_tag> <result_state>")
        trigger = parts[1].lower()
        result = parts[2].lower()
        
        reg = _load_json(GRAMMAR_FILE)
        new_id = f"{trigger}_{result}_{len(reg.get('transitions', []))}"
        new_rule = {
            "id": new_id,
            "trigger_tag": trigger,
            "result_state": result,
            "duration": 5,
            "message": f"Grammar Shift: {trigger} has induced {result}."
        }
        reg.setdefault("transitions", []).append(new_rule)
        _save_json(GRAMMAR_FILE, reg)
        grammar.reload_registry()
        
        player.send_line(f"{Colors.GREEN}Success:{Colors.RESET} Added grammar rule: {Colors.YELLOW}{trigger}{Colors.RESET} triggers {Colors.GREEN}{result}{Colors.RESET}.")
        return
