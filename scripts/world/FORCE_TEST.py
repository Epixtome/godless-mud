
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from scripts.world.master_architect import AethelgardArchitect

arch = AethelgardArchitect()
# AethelgardArchitect's run_phase_6 defines symbol_palettes locally...
# Wait, I need to see the code of run_phase_6.
import inspect
print(inspect.getsource(arch.run_phase_6))
