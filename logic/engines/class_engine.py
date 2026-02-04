import logging

logger = logging.getLogger("GodlessMUD")

def calculate_identity(player):
    """
    Determines the player's active class based on EQUIPPED blessings.
    Sets player.active_class to the class ID or None.
    """
    # 1. Count tags in equipped deck
    tag_counts = {}
    for b_id in player.equipped_blessings:
        blessing = player.game.world.blessings.get(b_id)
        if not blessing: continue
        for tag in blessing.identity_tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
            
    logger.info(f"Class Calc for {player.name}: Deck Tags: {tag_counts}")
            
    # 2. Check against class requirements
    found_class_id = None
    best_score = 0
    
    # Iterate all classes in the world
    for cls in player.game.world.classes.values():
        match = True
        score = 0
        reqs = cls.requirements.get('tags', {})
        stat_reqs = cls.requirements.get('stats', {})
        
        if not reqs and not stat_reqs: 
            continue
        
        # 1. Check Tag Requirements
        for tag, required_count in reqs.items():
            if tag_counts.get(tag, 0) < required_count:
                # logger.debug(f"Failed {cls.id}: Need {required_count} {tag}, have {tag_counts.get(tag, 0)}")
                match = False
                break
            score += required_count
            
        # 2. Check Stat Requirements (Base Stats)
        if match and stat_reqs:
            for stat, min_val in stat_reqs.items():
                if player.base_stats.get(stat, 0) < min_val:
                    match = False
                    break
        
        if match and score > best_score:
            found_class_id = cls.id
            best_score = score
            
    logger.info(f"Class Calc Result: {found_class_id}")
            
    player.active_class = found_class_id
    
    # 3. Update Player Identity Tags based on loadout
    current_tags = {"adventurer"}
    current_tags.update(tag_counts.keys())
    
    if found_class_id:
        current_tags.add(found_class_id)
        
    player.identity_tags = list(current_tags)

def check_unlocks(player):
    """
    Checks if player qualifies for any new classes based on KNOWN blessings.
    Adds to player.unlocked_classes.
    Returns list of newly unlocked Class objects.
    """
    # 1. Count tags in known collection
    tag_counts = {}
    for b_id in player.known_blessings:
        blessing = player.game.world.blessings.get(b_id)
        if not blessing: continue
        for tag in blessing.identity_tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
            
    newly_unlocked = []
    
    for cls in player.game.world.classes.values():
        if cls.id in player.unlocked_classes:
            continue
            
        match = True
        reqs = cls.requirements.get('tags', {})
        
        if not reqs: 
            continue
        
        for tag, required_count in reqs.items():
            if tag_counts.get(tag, 0) < required_count:
                match = False
                break
        
        if match:
            player.unlocked_classes.append(cls.id)
            newly_unlocked.append(cls)
            
    return newly_unlocked