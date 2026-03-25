
import os
import sys

# Ensure we can import from the project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scripts.world.master_architect import AethelgardArchitect

def generate_500_world():
    print("--- Starting V7.2 World Generation (150x150 @ 500, 500) ---")
    
    # Initialize with 500 unit offset and a 'test_' prefix
    architect = AethelgardArchitect(width=150, height=150, offset_x=500, offset_y=500, zone_prefix="test_")
    
    # Run all phases sequentially
    phases = [
        ("Phase 0: Landmass", architect.run_phase_0),
        ("Phase 1: Mountains", architect.run_phase_1),
        ("Phase 2: Hydrology", architect.run_phase_2),
        ("Phase 3: Roads", architect.run_phase_3),
        ("Phase 4: Bridges", architect.run_phase_4),
        ("Phase 5: Detailing", architect.run_phase_5)
    ]
    
    for name, func in phases:
        print(f"Running {name}...")
        if not func():
             print(f"ERROR: {name} failed.")
             return
            
    print("Finalizing Phase 6: Sharded Export & Influence Registration...")
    if architect.run_phase_6():
        print("\nSUCCESS: World generated at (500, 500).")
    else:
        print("\nERROR: Export failed.")

if __name__ == "__main__":
    generate_500_world()
