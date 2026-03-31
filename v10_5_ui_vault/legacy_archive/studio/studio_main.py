import sys
import os

# Add parent (scripts/world) and current (scripts/world/studio) to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import studio_state
import studio_ui

def run_studio():
    """Boot sequence for the Divine Interface (V15.0)."""
    # 1. Initialize State (The Backend)
    state = studio_state.StudioState()
    
    # 2. Initialize UI (The Frontend)
    ui = studio_ui.StudioUI(state)
    
    # 3. Boot (Enters Tkinter loop)
    ui.boot()

if __name__ == "__main__":
    run_studio()
