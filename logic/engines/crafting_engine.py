from models import Item

def get_recipe(player, item_name):
    """Look up a recipe by result ID in the world data."""
    recipe_data = player.game.world.recipes.get(item_name.lower())
    return recipe_data['ingredients'] if recipe_data else None

def can_craft(player, recipe):
    """Checks if player has ingredients. Returns (Bool, Missing_Ingredient)."""
    inventory_map = {}
    for item in player.inventory:
        inventory_map[item.name.lower()] = inventory_map.get(item.name.lower(), 0) + 1
        
    for ingredient, count in recipe.items():
        if inventory_map.get(ingredient, 0) < count:
            return False, ingredient
            
    return True, None

def craft_item(player, result_name, recipe):
    """Consumes ingredients and creates the item."""
    # Consume ingredients
    for ingredient, count in recipe.items():
        removed = 0
        for item in list(player.inventory):
            if item.name.lower() == ingredient and removed < count:
                player.inventory.remove(item)
                removed += 1
                
    # Create Result (Placeholder: In real app, clone from world.items)
    new_item = Item(result_name.title(), "A crafted item.")
    player.inventory.append(new_item)
    return new_item