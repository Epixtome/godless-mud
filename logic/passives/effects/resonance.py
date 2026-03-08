import logging
from logic.core import event_engine
from logic.constants import Tags

logger = logging.getLogger("GodlessMUD")

def apply_tag_resonance(ctx):
    """
    Universal Scaling Hook: calculate_damage_modifier
    Context: attacker, blessing, target, multiplier, bonus_flat
    
    Increases blessing power based on matching identity tags 'Voltage' score.
    """
    attacker = ctx.get('attacker') or ctx.get('player')
    blessing = ctx.get('blessing')
    
    if not attacker or not blessing:
        return
        
    # Get attacker's resonance profile
    if not hasattr(attacker, 'current_tags') or not attacker.current_tags:
        # If tags aren't calculated, trigger calculation (expensive but ensures correctness)
        from logic.engines.resonance_engine import ResonanceAuditor
        ResonanceAuditor.calculate_resonance(attacker)
        
    voltages = attacker.current_tags
    blessing_tags = getattr(blessing, 'identity_tags', [])
    
    # Scaling Constant: 1% per voltage point
    # We sum the voltage of all matching tags.
    total_scaling = 0.0
    
    for tag in blessing_tags:
        voltage = voltages.get(tag, 0)
        if voltage > 0:
            # Formula: 1% per point. 
            # Note: For multiple tags (e.g. Martial + Strike), they stack.
            total_scaling += (voltage * 0.01)
            
    # Apply to multiplier
    if total_scaling > 0:
        ctx['multiplier'] = ctx.get('multiplier', 1.0) + total_scaling
        # logger.debug(f"[RESONANCE] {attacker.name} scaled {blessing.name} by +{total_scaling*100:.1f}%")

def register():
    """Register resonance hooks."""
    event_engine.subscribe("calculate_damage_modifier", apply_tag_resonance)
