import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scripts.world.master_architect import AethelgardArchitect

def run_auto_gen():
    print("=== Aethelgard Blueprint Generation Started ===")
    architect = AethelgardArchitect()
    
    phases = [
        "Initial Landmass & Blueprint",
        "Mountain Spines",
        "Rivers & Lakes",
        "Cities & Roads",
        "Bridge Detection",
        "Terrain Detailing",
        "Sharded Export"
    ]
    
    run_funcs = [
        architect.run_phase_0,
        architect.run_phase_1,
        architect.run_phase_2,
        architect.run_phase_3,
        architect.run_phase_4,
        architect.run_phase_5,
        architect.run_phase_6
    ]
    
    for i, phase_name in enumerate(phases):
        print(f"[Phase {i}] {phase_name}...")
        if run_funcs[i]():
            print(f"  - Done.")
        else:
            print(f"  - FAILED!")
            return False
            
    print("\n=== Generation Complete! ===")
    return True

if __name__ == "__main__":
    run_auto_gen()
