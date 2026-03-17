def can_see(observer, target):
    if observer == target: return True
    if getattr(observer, 'admin_vision', False): return True
    if hasattr(target, 'status_effects') and "concealed" in target.status_effects:
        return can_detect(observer, target)
    return True

def can_detect(observer, target):
    perception_score = getattr(observer, 'perception', 10)
    # [V6.0] Concealment is significantly bolstered by the status effect
    concealment_score = getattr(target, 'concealment', 10)
    if hasattr(target, 'status_effects') and "concealed" in target.status_effects:
        concealment_score += 20
        
    return perception_score >= concealment_score
