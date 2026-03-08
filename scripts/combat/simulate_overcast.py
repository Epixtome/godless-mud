import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from models import Player, Blessing
from logic.engines import magic_engine
from logic.constants import Tags

# Mock classes to satisfy dependencies
class MockWriter:
    def write(self, data): pass
    async def drain(self): pass

class MockWorld:
    def __init__(self):
        self.blessings = {}
        self.status_effects = {}
        self.classes = {}

class MockGame:
    def __init__(self):
        self.tick_count = 0
        self.world = MockWorld()

def run_simulation():
    print("=== Starting Overcast Simulation ===")
    
    # Setup Environment
    game = MockGame()
    player = Player(game, MockWriter(), "TestMage", None)
    
    # Monkeypatch send_line to see engine output
    player.send_line = lambda msg: print(f"[GAME MSG] {msg}")
    
    # Initialize Stats
    player.max_hp = 2000
    player.hp = 2000
    player.resources[Tags.CONCENTRATION] = 100 # Start at Max
    
    # Define a spell with 50 Concentration cost
    spell = Blessing("void_blast", "Void Blast", 
                     tier=1, 
                     requirements={"concentration": 50}, 
                     identity_tags=[Tags.MAGIC, Tags.VOID])
    
    print(f"Initial State: HP={player.hp}, Conc={player.resources[Tags.CONCENTRATION]}")
    print(f"Spell Cost: 50 Concentration")
    
    # Cast Loop
    # We expect:
    # Cast 1: 100 -> 50 (Safe)
    # Cast 2: 50 -> 0 (Safe)
    # Cast 3: 0 -> -50 (Burn 50)
    # Cast 4: -50 -> -100 (Burn 100)
    for i in range(1, 6):
        print(f"\n--- Cast #{i} ---")
        
        pre_hp = player.hp
        pre_conc = player.resources[Tags.CONCENTRATION]
        
        # Perform Cast
        magic_engine.consume_resources(player, spell)
        
        post_hp = player.hp
        post_conc = player.resources[Tags.CONCENTRATION]
        
        burn = pre_hp - post_hp
        
        print(f"Concentration: {pre_conc} -> {post_conc}")
        if burn > 0:
            print(f"HP Burned: {burn}")
            
            # Verification Logic
            expected_deficit = 50 - pre_conc
            if burn == expected_deficit:
                print(f"VERIFIED: Burn matches deficit ({expected_deficit}).")
            else:
                print(f"FAILURE: Burn {burn} != Expected {expected_deficit}")
        else:
            print("No HP Burn (Safe Cast)")
            
        if post_conc <= -100:
            print("\nTarget depth (-100) reached.")
            break

if __name__ == "__main__":
    run_simulation()
