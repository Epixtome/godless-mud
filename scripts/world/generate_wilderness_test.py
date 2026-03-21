
import os
import sys

# Ensure we can import from the project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import scripts.world.master_architect as ma
from scripts.world.master_architect import AethelgardArchitect

print(f"DEBUG: Importing AethelgardArchitect from {ma.__file__}")

def generate_test_world():
    print("--- Starting Wilderness Test Generation (10k, 10k) ---")
    
    # Initialize with 10,000 unit offset and a 'test_' prefix
    architect = AethelgardArchitect(width=100, height=100, offset_x=10000, offset_y=10000, zone_prefix="test_")
    
    # Run all phases sequentially
    phases = [
        ("Phase 0", architect.run_phase_0),
        ("Phase 1", architect.run_phase_1),
        ("Phase 2", architect.run_phase_2),
        ("Phase 3", architect.run_phase_3),
        ("Phase 4", architect.run_phase_4),
        ("Phase 5", architect.run_phase_5)
    ]
    
    for name, func in phases:
        print(f"Running {name}...")
        func()
            
    print("Finalizing Phase 6: Export...")
    architect.run_phase_6()
    
    print("\nSUCCESS: Wilderness test generated at (10000, 10000).")

if __name__ == "__main__":
    generate_test_world()
