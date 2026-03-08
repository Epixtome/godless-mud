from logic.actions.registry import register
import utilities.telemetry as telemetry

# Example Skill
@register("skill_name")
async def do_example_skill(player, skill, args):
    if getattr(player, 'active_class', None) != 'guardian':
        return None, True
        
    return None, True
