import logic.handlers.command_manager as command_manager
from models import Monster
from logic.commands.admin.editors.mob_editor import EDITING_SESSIONS, show_editor_status

@command_manager.register("@createmob", admin=True, category="admin_building")
def create_mob(player, args):
    """Create a new mob prototype."""
    if not args:
        player.send_line("Usage: @createmob <id>")
        return
        
    mob_id = args.lower().strip()
    if mob_id in player.game.world.monsters:
        player.send_line(f"Mob ID '{mob_id}' already exists. Use @editmob to modify it.")
        return
        
    # Create default
    new_mob = Monster(
        name="New Mob",
        description="A newly created creature.",
        hp=10,
        damage=1,
        tags=[],
        max_hp=10,
        prototype_id=mob_id
    )
    new_mob.vulnerabilities = {}
    new_mob.states = {}
    new_mob.triggers = []
    new_mob.current_state = "normal"
    new_mob.loadout = []
    
    player.game.world.monsters[mob_id] = new_mob
    
    # Enter Editor
    player.state = "mob_editor"
    EDITING_SESSIONS[player.name] = {"target_id": mob_id, "unsaved": True}
    player.send_line(f"Created mob '{mob_id}'. Entering Mob Editor.")
    show_editor_status(player, mob_id)

