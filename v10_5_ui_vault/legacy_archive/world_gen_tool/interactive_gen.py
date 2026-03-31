import sys
import os
import importlib
import traceback
import copy

# 1. Setup Path to Project Root
# Current: utilities/world_gen_tool/interactive_gen.py
# Root:    ../../..
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))

# Set Working Directory to Project Root so relative paths (data/zones) work
os.chdir(project_root)

if project_root not in sys.path:
    sys.path.append(project_root)

# 2. Import Utilities
# We import these initially, but we will reload them in the execution loop
from utilities import reset_world
from utilities import generate_anchor
from utilities import resolve_hub
from utilities import pipeline_generator
from utilities import stitch_world
from utilities import visualize_world
from utilities import pipeline_config
from utilities import simple_noise

# Global State for Pipeline
GEN_STATE = None      # The working instance (dirty)
GEN_COMMITTED = None  # The snapshot from the previous successful step

def run_setup():
    """Runs the non-interactive setup phases automatically."""
    print("\n[Setup] Running automated setup (Reset, Anchor, Lock)...")
    try:
        # Reset
        importlib.reload(reset_world)
        reset_world.reset_generated_zones()
        
        # Anchor
        importlib.reload(generate_anchor)
        generate_anchor.generate_anchor()
        
        # Lock
        importlib.reload(resolve_hub)
        resolve_hub.resolve_hub()
        print("[Setup] Complete.")
    except Exception as e:
        print(f"[Setup] Failed: {e}")
        traceback.print_exc()
        sys.exit(1)

# --- Pipeline Sub-Phases ---

def commit_pipeline_state():
    """Updates the committed state to the current working state."""
    global GEN_COMMITTED, GEN_STATE
    if GEN_STATE:
        GEN_COMMITTED = copy.deepcopy(GEN_STATE)

def run_pipe_heightmap():
    """
    Phase 1: Heightmap.
    We handle this specially to allow re-seeding (Regen) on Retry.
    """
    global GEN_STATE
    print("\n[Phase 4.1] Pipeline: Heightmap (Perlin Noise)...")
    importlib.reload(pipeline_config)
    importlib.reload(simple_noise)
    importlib.reload(pipeline_generator)
    # Always create a new instance to get a new Seed/Noise map
    GEN_STATE = pipeline_generator.WorldGenerator(250, 250)
    GEN_STATE.phase_1_heightmap()
    GEN_STATE.visualize_scaled(scale=4)

def run_pipeline_step(step_name, method_name):
    global GEN_STATE, GEN_COMMITTED
    
    if GEN_COMMITTED is None:
        print("State missing! Cannot run intermediate step without previous state.")
        return

    print(f"\n[Phase 4.{step_name}] Pipeline: {step_name}...")
    
    # 1. Restore from last commit (Clean Slate for Retry)
    if GEN_COMMITTED:
        GEN_STATE = copy.deepcopy(GEN_COMMITTED)
    
    # 2. Reload Logic (Hot-Patching)
    importlib.reload(pipeline_config)
    importlib.reload(simple_noise)
    importlib.reload(pipeline_generator)
    NewClass = pipeline_generator.WorldGenerator
    
    # 3. Execute Method on Instance
    if hasattr(NewClass, method_name):
        func = getattr(NewClass, method_name)
        func(GEN_STATE) # Apply new method to existing instance
    else:
        raise AttributeError(f"Method {method_name} not found in WorldGenerator")

    # 4. Visualize
    if hasattr(NewClass, 'visualize_scaled'):
        getattr(NewClass, 'visualize_scaled')(GEN_STATE, scale=4)

def run_pipe_prune(): run_pipeline_step("Prune Voids", "_prune_internal_voids")
def run_pipe_topology(): run_pipeline_step("Topology", "phase_2_topology")
def run_pipe_tectonics(): run_pipeline_step("Tectonics", "phase_3_tectonics")
def run_pipe_hydrology(): run_pipeline_step("Hydrology", "phase_3b_hydrology")
def run_pipe_biomes(): run_pipeline_step("Biomes", "phase_4_biomes")
def run_pipe_stamping(): run_pipeline_step("Stamping", "phase_5_stamping")

def run_pipe_temperature():
    run_pipeline_step("Temperature", "generate_temperature_map")
    if GEN_STATE and hasattr(pipeline_generator.WorldGenerator, 'visualize_temperature'):
        getattr(pipeline_generator.WorldGenerator, 'visualize_temperature')(GEN_STATE, scale=4)

def run_pipe_moisture():
    run_pipeline_step("Moisture", "generate_moisture_map")
    if GEN_STATE and hasattr(pipeline_generator.WorldGenerator, 'visualize_moisture'):
        getattr(pipeline_generator.WorldGenerator, 'visualize_moisture')(GEN_STATE, scale=4)

def run_pipe_population(): 
    run_pipeline_step("Population", "phase_6_population")
    # Visualize Kingdoms after population
    if GEN_STATE and hasattr(pipeline_generator.WorldGenerator, 'visualize_kingdoms'):
        getattr(pipeline_generator.WorldGenerator, 'visualize_kingdoms')(GEN_STATE, scale=4)

def run_pipe_save():
    print("\n[Phase 4.End] Pipeline: Saving Data...")
    if GEN_STATE:
        GEN_STATE.export_map()
        GEN_STATE.save_zones()
    else:
        print("No generator state to save!")

# Configuration of Phases
# Easy to modify order or add new ones here
PHASES = [
    # Pipeline Phases (Visible Changes)
    {"name": "Pipe: Heightmap (Perlin)", "func": run_pipe_heightmap, "on_complete": commit_pipeline_state},
    {"name": "Pipe: Prune Voids", "func": run_pipe_prune, "on_complete": commit_pipeline_state},
    {"name": "Pipe: Tectonics", "func": run_pipe_tectonics, "on_complete": commit_pipeline_state},
    {"name": "Pipe: Hydrology", "func": run_pipe_hydrology, "on_complete": commit_pipeline_state},
    {"name": "Pipe: Temperature", "func": run_pipe_temperature, "on_complete": commit_pipeline_state},
    {"name": "Pipe: Moisture", "func": run_pipe_moisture, "on_complete": commit_pipeline_state},
    {"name": "Pipe: Biomes", "func": run_pipe_biomes, "on_complete": commit_pipeline_state},
    {"name": "Pipe: Topology", "func": run_pipe_topology, "on_complete": commit_pipeline_state},
    {"name": "Pipe: Stamping", "func": run_pipe_stamping, "on_complete": commit_pipeline_state},
    {"name": "Pipe: Population", "func": run_pipe_population, "on_complete": commit_pipeline_state},
    {"name": "Pipe: Save", "func": run_pipe_save}
]

def main():
    print("==========================================")
    print("   GODLESS INTERACTIVE GENERATOR TOOL     ")
    print("==========================================")
    
    # Run Setup Automatically
    run_setup()
    
    print(f"Loaded {len(PHASES)} phases.")
    
    idx = 0
    while idx < len(PHASES):
        phase = PHASES[idx]
        print(f"\n------------------------------------------")
        print(f"NEXT PHASE: [{idx+1}/{len(PHASES)}] {phase['name']}")
        print("------------------------------------------")
        
        cmd = input("Command ([Enter]=Run, [S]kip, [J]ump <#>, [Q]uit): ").strip().lower()
        
        if cmd == 'q':
            print("Exiting generator.")
            break
        
        if cmd == 's':
            print(f"Skipping {phase['name']}...")
            idx += 1
            continue
            
        if cmd.startswith('j'):
            try:
                # Parse jump target (1-based index)
                target = int(cmd.split()[1]) - 1
                if 0 <= target < len(PHASES):
                    idx = target
                    continue
                else:
                    print(f"Invalid phase number. Range: 1-{len(PHASES)}")
            except (IndexError, ValueError):
                print("Usage: j <phase_number>")
            continue

        # Execute Phase Loop (allows retrying the same phase)
        while True:
            try:
                phase['func']()
                # If successful, ask what to do next
                post_cmd = input(f"\nPhase '{phase['name']}' Done. ([Enter]=Next, [R]etry, [Q]uit): ").strip().lower()
                if post_cmd == 'r':
                    print(f"\nRetrying {phase['name']}...")
                    continue # Loops back to try block
                elif post_cmd == 'q':
                    print("Exiting generator.")
                    return
                else:
                    # Next phase
                    # Execute completion hook if present (e.g., commit state)
                    if "on_complete" in phase:
                        phase["on_complete"]()
                    idx += 1
                    break
            except Exception as e:
                print(f"\n!!! ERROR in {phase['name']}: {e}")
                traceback.print_exc()
                retry = input("\nAn error occurred. [R]etry or [S]kip? ").strip().lower()
                if retry == 's':
                    idx += 1
                    break
                # Else loop back and retry

    print("\n=== GENERATION SEQUENCE COMPLETE ===")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n!!! CRITICAL ERROR: {e}")
        traceback.print_exc()
        input("\nPress Enter to exit...") # Pause the console window
