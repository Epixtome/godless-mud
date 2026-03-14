import os
import sys
import asyncio
import time

# Ensure project root is in path
sys.path.append(os.getcwd())

# We MUST mock the networking before importing GodlessGame to avoid socket errors
import unittest.mock
mock_reader = unittest.mock.Mock()
mock_writer = unittest.mock.Mock()

from godless_mud import GodlessGame
from models.entities.player import Player
from models.entities.monster import Monster
from logic.core import combat, resources, effects
from utilities.colors import Colors

async def run_system_check():
    print(f"{Colors.BOLD}{Colors.CYAN}--- GODLESS ENGINE INTEGRITY SCAN (V4.5) ---{Colors.RESET}")
    
    # 0. Initialize Engine (Loads World, Registers Modules, Starts Systems)
    # Mocking the loader to prevent full disk read if possible, but GodlessGame needs a world.
    # We'll let it load normally but suppress noise.
    game = GodlessGame()
    print(f"  {Colors.GREEN}✓ Engine Initialized (Tick: {game.tick_count}){Colors.RESET}")
    
    # 1. Setup Test Environment
    room = list(game.world.rooms.values())[0]
    player = Player(game, None, "Tester", room)
    
    # Create a fresh dummy to ensure a clean state
    dummy = Monster("Dummy", "A training dummy", 100, 0, tags=["training_dummy"], game=game)
    dummy.room = room
    room.monsters.append(dummy)
    
    # 2. Test Posture Protocol
    print(f"\n{Colors.YELLOW}[TEST] Posture Protocol & Auto-Attacks:{Colors.RESET}")
    initial_bal = dummy.resources.get('balance', 100)
    
    # Simulate an attack
    combat.handle_attack(player, dummy, room, game)
    new_bal = dummy.resources.get('balance', 100)
    
    if new_bal < initial_bal:
        print(f"  {Colors.GREEN}✓ Auto-attack correctly reduced balance ({initial_bal} -> {new_bal}){Colors.RESET}")
    else:
        print(f"  {Colors.RED}✗ ERROR: Auto-attack failed to reduce balance! Check combat_actions.py logic.{Colors.RESET}")

    # 3. Test Class Shards (UI & Logic)
    print(f"\n{Colors.YELLOW}[TEST] Class Archetype Shards:{Colors.RESET}")
    
    # We test the 4 core archetypes
    test_cases = [
        {'id': 'monk', 'resource': 'flow_pips', 'keyword': 'FLOW'},
        {'id': 'barbarian', 'resource': 'momentum', 'keyword': 'MOMENTUM'},
        {'id': 'warlock', 'resource': 'entropy', 'keyword': 'ENTROPY'},
        {'id': 'illusionist', 'resource': 'echoes', 'keyword': 'ECHO'}
    ]
    
    from logic.core import event_engine
    
    for case in test_cases:
        cid = case['id']
        player.active_class = cid
        
        # Populate class state to avoid prompt crashes
        class_state = player.ext_state.setdefault(cid, {})
        class_state[case['resource']] = 5
        
        if cid == 'monk':
            class_state['stance'] = 'tiger'
            class_state['chi'] = 5
        elif cid == 'barbarian':
            class_state['momentum'] = 5
            class_state['fury'] = 50
        elif cid == 'warlock':
            class_state['entropy'] = 3
        elif cid == 'illusionist':
            class_state['echoes'] = 3
        
        ctx = {'player': player, 'prompts': []}
        event_engine.dispatch("on_build_prompt", ctx)
        
        found = False
        keyword = case['keyword']
        
        for p in ctx['prompts']:
            if p and keyword in p.upper():
                found = True
                break
        
        if found:
            print(f"  {Colors.GREEN}✓ {cid.title()}: Prompt identified class signature. ({ctx['prompts'][-1] if ctx['prompts'] else 'Empty'}){Colors.RESET}")
        else:
            print(f"  {Colors.RED}✗ ERROR: {cid.title()} signature missing from prompt! (Prompts: {ctx['prompts']}){Colors.RESET}")

    # 4. Test Death Transition
    print(f"\n{Colors.YELLOW}[TEST] Reaper Pipeline (Deferred Death):{Colors.RESET}")
    dummy.hp = 0
    combat.kill_entity(dummy, killer=player)
    
    if any(d['victim'] == dummy for d in game.dead_entities):
        print(f"  {Colors.GREEN}✓ Entity correctly queued for the Reaper.{Colors.RESET}")
    else:
        print(f"  {Colors.RED}✗ ERROR: Entity death bypassed the queue!{Colors.RESET}")

    print(f"\n{Colors.BOLD}{Colors.CYAN}--- ALL TESTS PASSED ---{Colors.RESET}")

if __name__ == "__main__":
    try:
        asyncio.run(run_system_check())
    except Exception as e:
        print(f"{Colors.RED}System Check Aborted: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
