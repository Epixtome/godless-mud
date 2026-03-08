import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scripts.world import reset_world
# from scripts.world import generate_anchor
# from scripts.world import resolve_hub
from scripts.world import pipeline_generator
# from scripts.world import stitch_world
from scripts.world import visualize_world

def run():
    print("=== GODLESS WORLD GENERATION MASTER SCRIPT ===")
    
    # 1. Reset
    print("\n[Step 1] Resetting World...")
    # We call the function directly to bypass the "Are you sure?" prompt in __main__
    reset_world.reset_generated_zones()
    
    # 2. Anchor
    print("\n[Step 2] Generating Anchor (Hub)...")
    # generate_anchor.generate_anchor()
    
    # 3. Lock
    print("\n[Step 3] Locking Hub...")
    # resolve_hub.resolve_hub()
    
    # 4. Generate Pipeline Map
    print("\n[Step 4] Generating Pipeline Map...")
    gen = pipeline_generator.WorldGenerator(250, 250)
    gen.run_generation()
    
    # 6. Stitch
    print("\n[Step 6] Stitching Zones...")
    # stitch_world.stitch_world()
    
    # 7. Visualize
    print("\n[Step 7] Visualizing...")
    visualize_world.visualize_world()
    
    print("\n=== GENERATION COMPLETE ===")

if __name__ == "__main__":
    run()
