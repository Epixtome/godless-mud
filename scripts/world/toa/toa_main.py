# [TOA_MAIN] The Omnipresent Architect Bootloader
import sys
import os

# Add local directory to path for sibling imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from toa_core import TOAState
from toa_ui import TOAUI

def boot_omnipresent():
    """Initializes the V20.0 Architectural Suite."""
    print("--- [TOA V1.0] INITIALIZING OMNIPRESENT ARCHITECT ---")
    
    # 1. State Foundation
    state = TOAState(width=125, height=125)
    
    # 2. UI Viewport
    app = TOAUI(state)
    
    # 3. Execution (Tkinter Loop)
    app.boot()

if __name__ == "__main__":
    boot_omnipresent()
