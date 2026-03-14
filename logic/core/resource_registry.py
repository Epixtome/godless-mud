"""
logic/core/resource_registry.py
Central registry for all class-specific resources.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
from utilities.colors import Colors

@dataclass
class ResourceDefinition:
    id: str
    display_name: str
    max: int = 100
    regen: int = 0
    decay: int = 0
    decay_threshold_ticks: int = 0  # Ticks of inactivity before decay starts
    storage_key: str = "" # Key in ext_state[class_name]
    color: str = Colors.RESET
    max_getter: Optional[Callable] = None # Optional dynamic max lookup
    shorthand: str = "" # 3-character display name for bars
    always_show: bool = False # If true, shows even at 0

# Kit ID -> List of ResourceDefinitions
RESOURCE_REGISTRY: Dict[str, List[ResourceDefinition]] = {}

def register_resource(kit_id: str, definition: ResourceDefinition):
    """Registers a resource behavior for a kit."""
    if kit_id not in RESOURCE_REGISTRY:
        RESOURCE_REGISTRY[kit_id] = []
    
    # Avoid duplicates
    if not any(d.id == definition.id for d in RESOURCE_REGISTRY[kit_id]):
        RESOURCE_REGISTRY[kit_id].append(definition)

def get_resources_for_kit(kit_id: str) -> List[ResourceDefinition]:
    """Retrieves all registered resources for a specific kit."""
    return RESOURCE_REGISTRY.get(kit_id, [])

def get_definition(kit_id: str, resource_id: str) -> Optional[ResourceDefinition]:
    """Retrieves a specific resource definition."""
    for res in RESOURCE_REGISTRY.get(kit_id, []):
        if res.id == resource_id:
            return res
    return None
