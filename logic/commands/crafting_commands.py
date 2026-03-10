import logic.handlers.command_manager as command_manager
import logic.engines.crafting_engine as crafting_engine
from utilities.colors import Colors

@command_manager.register("craft", category="interaction")
def craft(player, args):
    """
    Craft an item using ingredients.
    Usage: craft <item> | craft list
    """
    if not args:
        player.send_line("Usage: craft <item> | craft list")
        return
        
    if args.lower() == "list":
        player.send_line(f"\n--- {Colors.BOLD}Crafting Recipes{Colors.RESET} ---")
        recipes = player.game.world.recipes
        if not recipes:
            player.send_line("No recipes known.")
            return
            
        for r_id, data in recipes.items():
            # Check if craftable
            can_make, _ = crafting_engine.can_craft(player, data['ingredients'])
            status = f"{Colors.GREEN}[Ready]{Colors.RESET}" if can_make else f"{Colors.RED}[Missing]{Colors.RESET}"
            
            ingredients = []
            for name, count in data['ingredients'].items():
                ingredients.append(f"{count}x {name}")
            
            player.send_line(f"{status} {Colors.CYAN}{r_id.title()}{Colors.RESET}")
            player.send_line(f"      Requires: {', '.join(ingredients)}")
        return
        
    item_name = args.lower()
    recipe = crafting_engine.get_recipe(player, item_name)
    
    if not recipe:
        player.send_line("You don't know how to craft that.")
        return
        
    can_craft, missing = crafting_engine.can_craft(player, recipe)
    if not can_craft:
        player.send_line(f"You are missing ingredients: {missing}.")
        return
        
    result_item = crafting_engine.craft_item(player, item_name, recipe)
    player.send_line(f"You craft a {result_item.name}!")
    player.room.broadcast(f"{player.name} crafts a {result_item.name}.", exclude_player=player)

@command_manager.register("recipes", category="interaction")
def list_recipes(player, args):
    """List available crafting recipes."""
    player.send_line(f"\n--- {Colors.BOLD}Known Recipes{Colors.RESET} ---")
    
    recipes = player.game.world.recipes
    if not recipes:
        player.send_line("No recipes known.")
        return
        
    for r_id, data in recipes.items():
        ingredients = []
        for name, count in data['ingredients'].items():
            ingredients.append(f"{count}x {name}")
        player.send_line(f"{Colors.CYAN}{r_id.title()}{Colors.RESET}: {', '.join(ingredients)}")
