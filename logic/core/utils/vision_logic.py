def can_see(observer, target):
    if observer == target: return True
    if getattr(observer, 'admin_vision', False): return True
    if hasattr(target, 'status_effects') and "concealed" in target.status_effects:
        return can_detect(observer, target)
    return True

def can_detect(observer, target):
    perception_score = getattr(observer, 'perception', 10)
    concealment_score = getattr(target, 'concealment', 10)
    return perception_score >= concealment_score
