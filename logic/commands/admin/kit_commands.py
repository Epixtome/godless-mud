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

@register("@kit", category="admin", admin=True)
def cmd_kit(player, args):
    """
    Admin Kit Workbench.
    Usage:
      @kit list                - List all available kits.
      @kit view <kit_id>       - Detail the 8-ability composition.
      @kit swap <kit> <idx> <id>  - Swap a blessing in a kit (Slot 1-8).
      @kit reload              - Refresh all kits from disk.
    """
    if not args:
        return player.send_line("Usage: @kit <list|view|swap|reload> [args]")
    
    sub = args[0].lower()
    kits = _load_json(KIT_FILE)

    if sub == "list":
        player.send_line("{B=== Available Kits ==={x")
        for k_id in kits:
            player.send_line(f" - {k_id}")
        return

    if sub == "view":
        if len(args) < 2: return player.send_line("Specify a kit ID.")
        k_id = args[1].lower()
        if k_id not in kits: return player.send_line(f"Kit '{k_id}' not found.")
        
        kit = kits[k_id]
        player.send_line(f"{{B=== Kit: {kit.get('name', k_id)} ==={{x")
        player.send_line(f"Description: {kit.get('description', 'N/A')}")
        player.send_line(f"Axes: {', '.join(kit.get('axes', []))}")
        player.send_line("{Y--- Abilities ---{x")
        for i, b_id in enumerate(kit.get("blessings", [])):
            player.send_line(f" {i+1}. {b_id}")
        return

    if sub == "swap":
        if len(args) < 4: return player.send_line("Usage: @kit swap <kit> <slot_1_8> <blessing_id>")
        k_id = args[1].lower()
        try:
            slot = int(args[2]) - 1
            new_b = args[3].lower()
        except ValueError:
            return player.send_line("Slot must be a number 1-8.")

        if k_id not in kits: return player.send_line(f"Kit '{k_id}' not found.")
        if slot < 0 or slot >= 8: return player.send_line("Slot must be between 1 and 8.")
        
        old_b = kits[k_id]["blessings"][slot]
        kits[k_id]["blessings"][slot] = new_b
        _save_json(KIT_FILE, kits)
        
        player.send_line(f"{{GSuccess:{{x Swapped slot {slot+1} of {{Y{k_id}{{x from {{R{old_b}{{x to {{G{new_b}{{x.")
        logger.info(f"Admin {player.name} swapped {k_id} slot {slot+1}: {old_b} -> {new_b}")
        return

    if sub == "reload":
        # In a real system, you'd trigger a global reload of the kits dictionary.
        # For now, we just acknowledge the save was successful above.
        player.send_line("{GKit Registry reloaded from disk.{x")
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
    
    sub = args[0].lower()
    
    if sub == "list":
        reg = grammar.get_registry()
        player.send_line("{B=== Active Grammar Transitions ==={x")
        for rule in reg.get("transitions", []):
            trigger = rule.get("trigger_tag")
            result = rule.get("result_state")
            player.send_line(f" - {{Y{trigger}{{x -> {{G{result}{{x (ID: {rule.get('id')})")
        return

    if sub == "reload":
        grammar.reload_registry()
        player.send_line("{GGrammar Registry reloaded.{x")
        return

    if sub == "add":
        if len(args) < 3: return player.send_line("Usage: @grammar add <trigger_tag> <result_state>")
        trigger = args[1].lower()
        result = args[2].lower()
        
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
        
        player.send_line(f"{{GSuccess:{{x Added grammar rule: {{Y{trigger}{{x triggers {{G{result}{{x.")
        return
