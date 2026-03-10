# Add project root to path
# Assuming we run from the project root.
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from logic.core import event_engine, resources
from logic.core import combat
from logic.engines import class_engine
from models import Player, GameEntity
from logic.core.world import World
from logic.core import loader as world_loader
from utilities.colors import Colors
from logic.engines.resonance_engine import ResonanceAuditor

class MockGame:
    def __init__(self):
        self.world = world_loader.load_world(self)
        # Dynamically pick the first room available as start room for simulation
        if self.world.rooms:
            self.world.start_room = next(iter(self.world.rooms.values()))
        else:
            self.world.start_room = None
        self.tick_count = 0
        self.players = {}

def simulate_h2h(kit1="monk", kit2="monk", rounds=5):
    """Simulates a series of auto-attacks between two classes."""
    game = MockGame()
    
    # Register events (Critical for class logic)
    from logic.commands import module_loader
    module_loader.register_all_modules()
    
    # Setup Player 1
    class MockConnection:
        def write(self, *args, **kwargs): pass
        def flush(self, *args, **kwargs): pass
        
    p1 = Player(game, MockConnection(), "Attacker", game.world.start_room)
    success, msg = class_engine.apply_kit(p1, kit1)
    if not success:
        print(f"Error applying kit {kit1}: {msg}")
        return
    
    # Setup Player 2 (Target)
    p2 = Player(game, MockConnection(), "Defender", game.world.start_room)
    success, msg = class_engine.apply_kit(p2, kit2)
    if not success:
        print(f"Error applying kit {kit2}: {msg}")
        return
    
    print(f"\n{Colors.CYAN}--- Combat Simulation: {kit1.upper()} vs {kit2.upper()} ---{Colors.RESET}")
    print(f"{p1.name}: Class={p1.active_class}, Weapon={p1.equipped_weapon.name if p1.equipped_weapon else 'Unarmed'}, Tags={p1.current_tags}")
    print(f"{p2.name}: Class={p2.active_class}, Weapon={p2.equipped_weapon.name if p2.equipped_weapon else 'Unarmed'}, Tags={p2.current_tags}")
    print("-" * 40)
    
    total_p1_dmg = 0
    total_p2_dmg = 0
    
    for i in range(1, rounds + 1):
        # Round starts
        game.tick_count = i
        
        # P1 Attacks P2 (Using facade calculate_player_damage equivalent)
        p1_dmg = combat.calculate_base_damage(p1, p2)
        total_p1_dmg += p1_dmg
        print(f"Round {i}: {p1.name} hits {p2.name} for {Colors.RED}{p1_dmg}{Colors.RESET} damage.")
        
        # P2 Attacks P1
        p2_dmg = combat.calculate_base_damage(p2, p1)
        total_p2_dmg += p2_dmg
        print(f"Round {i}: {p2.name} hits {p1.name} for {Colors.RED}{p2_dmg}{Colors.RESET} damage.")
        
    print("-" * 40)
    print(f"RESULTS (Total Damage Output):")
    print(f"  {p1.name}: {total_p1_dmg}")
    print(f"  {p2.name}: {total_p2_dmg}")

if __name__ == "__main__":
    # Standard classes to test
    class_to_test = "monk"
    against = "monk"
    
    if len(sys.argv) > 1:
        class_to_test = sys.argv[1]
    if len(sys.argv) > 2:
        against = sys.argv[2]
        
    # We need to register modules for events to work
    from logic.commands import module_loader
    module_loader.register_all_modules()
    
    simulate_h2h(class_to_test, against)
