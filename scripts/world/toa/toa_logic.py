# [TOA_LOGIC] The V20.0 Negotiation Engine (Omnipresent Architect)
import sys
import os

# Ensure the parent directory (scripts/world) is in the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import architect_logic as core
import architect_climate as climate

def synchronize_negotiation(state, roi=None):
    """
    [V20.0] The Heartbeat of TOA.
    Directly bridges painted intent into the live architectural foundation.
    """
    # 1. Sync weights and layers
    config = state.to_json()
    
    # 2. Run the Biomatic Foundation (Climate Pass)
    # The engine updates the 'grid' based on noise + designer authority
    res = climate.run_climate_pass(state.grid, state.width, state.height, config)
    
    # 3. Cache the realityfoundation for Telemetry
    state.debug_stats = {
        "elev": res.get("elev_map"),
        "moist": res.get("moist_map")
    }
    
    # 4. ROI OPTIMIZATION: If we are painting, we only care about the biomatic shift
    # Infrastructure (Roads/Rivers) can be manually triggered or pulsed
    if not roi:
        # Full Simulation Pulse (Rivers, Tectonics, etc.)
        core.run_phase_1_logic(state.grid, state.width, state.height, config) # Tectonics
        core.run_phase_2_logic(state.grid, state.width, state.height, config, state.debug_stats) # Rivers
        core.run_phase_3_logic(state.grid, state.width, state.height, config) # Civ
        core.run_phase_5_logic(state.grid, state.width, state.height, config) # Landmarks/Scatter

    return True
