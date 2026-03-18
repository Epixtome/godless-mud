
"""
logic/core/perception.py
Standard Perception Facade. Use this for all visibility, map, and scan requests.
[V6.8 Standard]
"""

from logic.engines import (vision_engine as engine)

# Re-export key context types for commands
Context = engine.VisionContext
NAVIGATION = engine.NAVIGATION_CONTEXT
TACTICAL = engine.TACTICAL_CONTEXT
INTELLIGENCE = engine.INTELLIGENCE_CONTEXT
Result = engine.PerceptionResult

def get_perception(observer, radius=7, context=None):
    """
    Primary entry point for world awareness.
    Returns a PerceptionResult containing filtered terrain and intelligence.
    """
    if context is None:
        context = TACTICAL
    return engine.get_perception(observer, radius=radius, context=context)

def can_see(observer, target):
    """Checks if an observer can physically see a target (entity or room)."""
    return engine.can_see(observer, target)

def can_detect(observer, target):
    """Checks if an observer senses a concealed target."""
    return engine.can_detect(observer, target)
