"""
[GODLESS V8 ARCHITECT LOGIC]
FACADE MODULE - Delegating to Domain Shards:
- architect_terrain: Landmass & Spines
- architect_natural: Rivers, Biomes, Shrines
- architect_infrastructure: Roads, Bridges, Pathfinding
- architect_export: Quadrant Splitting & Formatting
- architect_common: Shared Utilities
"""

# Facade Imports
from architect_terrain import run_phase_0_logic, run_phase_1_logic
from architect_climate import run_climate_pass
from architect_natural import run_phase_2_logic, run_phase_5_logic, run_phase_1_5_logic
from architect_infrastructure import run_phase_3_logic, run_phase_4_logic
from architect_export import run_phase_6_export
from architect_common import run_road_pathfinding, get_biome_description, get_direction_text

# [LEGACY WRAPPERS] - For compatibility with any direct calls
def run_phase_x_logic(*args, **kwargs):
    """Facade for future expansions."""
    return True
