import os
import sys
import logging
import re
import copy
import random
from collections import Counter

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from logic.core import loader as world_loader
from logic.core import event_engine, combat, effects
from logic.engines import class_engine, combat_processor
from logic.commands import module_loader
from logic.engines.blessings.auditor import Auditor
from utilities.colors import Colors

# Late-bind models to avoid circular import hell in standalone scripts
import models

# Initialize logging for sim
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger("SimEngine")

def strip_ansi(text):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

class MockConnection:
    def __init__(self):
        self.output = []
    
    def write(self, text):
        self.output.append(text)
    
    def flush(self):
        pass

class SimEngine:
    def __init__(self):
        self.game = self._init_mock_game()
        self.battle_log = []
        self._register_modules()
    
    def _init_mock_game(self):
        class MockGame:
            def __init__(self):
                self.world = world_loader.load_world(self)
                self.players = {}
                self.tick_count = 0
                
        return MockGame()

    def _register_modules(self):
        """Must register all modules for event listeners to work."""
        module_loader.register_all_modules()

    def get_all_items(self):
        return sorted([{"id": id, "name": item.name} for id, item in self.game.world.items.items()], key=lambda x: x['name'])

    def create_room(self, terrain="forest", weather="clear", flags=None):
        room = models.Room(room_id="sim.0.0.0", name="Simulation Chamber")
        room.terrain = terrain
        room.zone_id = "sim"
        room.x = room.y = room.z = 0
        room.flags = flags or []
        # Weather is represented as a room status effect in V6.0
        room.status_effects = {weather: 99999}
        return room

    def setup_player(self, name, kit_id, room, weapon_id=None, armor_id=None):
        conn = MockConnection()
        player = models.Player(self.game, conn, name, room)
        player.current_tags = {}
        
        success, msg = class_engine.apply_kit(player, kit_id)
        if not success:
            raise ValueError(f"Failed to apply kit {kit_id}: {msg}")
        
        # Gear Overrides
        if weapon_id:
            w_proto = self.game.world.items.get(weapon_id)
            if w_proto: player.equipped_weapon = copy.deepcopy(w_proto)
        if armor_id:
            a_proto = self.game.world.items.get(armor_id)
            if a_proto: player.equipped_armor = copy.deepcopy(a_proto)
            
        return player

    def setup_mob(self, mob_id, room):
        proto = self.game.world.monsters.get(mob_id)
        if not proto:
            raise ValueError(f"Mob prototype {mob_id} not found.")
        
        mob = models.Monster(
            proto.name, proto.description, proto.hp, proto.damage,
            tags=proto.tags.copy(), max_hp=proto.max_hp, prototype_id=mob_id,
            game=self.game
        )
        mob.room = room
        mob.resources = proto.resources.copy() if hasattr(proto, 'resources') else {'stamina': 100, 'balance': 100}
        mob.fighting = None
        mob.attackers = []
        mob.skills = proto.skills.copy()
        return mob

    def run_series(self, req, iterations=10):
        series_results = []
        all_logs = []
        skill_usage = Counter()
        
        for i in range(iterations):
            room = self.create_room(req.terrain, req.weather)
            if req.p1_type == "player":
                c1 = self.setup_player("Attacker", req.p1_id, room, req.p1_weapon, req.p1_armor)
            else:
                c1 = self.setup_mob(req.p1_id, room)
                
            if req.p2_type == "player":
                c2 = self.setup_player("Defender", req.p2_id, room, req.p2_weapon, req.p2_armor)
            else:
                c2 = self.setup_mob(req.p2_id, room)
                
            result, duel_log = self.run_duel(c1, c2, room, it_index=i+1)
            series_results.append(result)
            all_logs.extend(duel_log)
            skill_usage.update(result.get('skills_used', Counter()))

        # Aggregate Stats
        wins = Counter([str(r.get('winner', 'None')) for r in series_results])
        avg_rounds = sum(float(r.get('rounds', 0)) for r in series_results) / iterations
        valid_ttks = [float(r.get('rounds', 0)) for r in series_results if r.get('winner') not in ["Draw (Time Limit)", None]]
        avg_ttk = sum(valid_ttks) / len(valid_ttks) if valid_ttks else 0
        avg_c1_dmg = sum(float(r.get('c1_dmg_dealt', 0)) for r in series_results) / iterations
        avg_c2_dmg = sum(float(r.get('c2_dmg_dealt', 0)) for r in series_results) / iterations
        
        summary = {
            "iterations": iterations,
            "win_rate": {k: round(v/iterations * 100, 1) for k, v in wins.items()},
            "avg_rounds": round(avg_rounds, 1),
            "avg_ttk": round(avg_ttk, 1),
            "avg_dmg": {"Attacker": round(avg_c1_dmg, 1), "Defender": round(avg_c2_dmg, 1)},
            "skill_frequency": {k: v for k, v in skill_usage.most_common(10)},
            "last_winner": series_results[-1]['winner'],
            "last_rounds": series_results[-1]['rounds'],
            "last_c1_hp": series_results[-1]['c1_final_hp'],
            "last_c2_hp": series_results[-1]['c2_final_hp']
        }
        
        return summary, all_logs

    def run_duel(self, c1, c2, room, max_rounds=50, it_index=1):
        """
        Runs a duel between two combatants.
        c1 and c2 can be Player or Monster.
        """
        self.battle_log = []
        c1.room = room
        c2.room = room
        room.players = [c1] if hasattr(c1, 'is_player') and c1.is_player else []
        if hasattr(c2, 'is_player') and c2.is_player: room.players.append(c2)
        
        room.monsters = [c1] if not (hasattr(c1, 'is_player') and c1.is_player) else []
        if not (hasattr(c2, 'is_player') and c2.is_player): room.monsters.append(c2)

        # Initiate combat
        combat.start_combat(c1, c2)
        combat.start_combat(c2, c1)

        result = {
            "winner": None, "rounds": 0, "c1_dmg_dealt": 0, "c2_dmg_dealt": 0,
            "c1_final_hp": 0, "c2_final_hp": 0, "skills_used": Counter()
        }

        for r in range(1, max_rounds + 1):
            self.game.tick_count = r
            
            # Randomize initiative each round to prevent "First-Strike" stun locking
            turn_order = [(c1, c2, "Attacker"), (c2, c1, "Defender")]
            random.shuffle(turn_order)

            for attacker, target, role in turn_order:
                if attacker.hp <= 0 or target.hp <= 0:
                    break
                
                h_target_before = target.hp
                
                # Choose and execute action
                skill = self._choose_action(attacker, target)
                if skill: result["skills_used"][skill.name] += 1
                
                combat_processor._process_turn(attacker, room, self.game, set(), visibility_cache={(attacker, target): True})
                
                # Track damage for statistics
                dmg = h_target_before - target.hp
                if role == "Attacker":
                    result["c1_dmg_dealt"] += dmg
                else:
                    result["c2_dmg_dealt"] += dmg

                if target.hp <= 0:
                    result.update({"winner": role, "rounds": r})
                    break
            
            if result["winner"]:
                break
                
            self._flush_outputs([c1, c2])

        self._flush_outputs([c1, c2]) # Flush any remaining output after combat ends
        result.update({"c1_final_hp": c1.hp, "c2_final_hp": c2.hp})
        if not result["winner"]:
            result["winner"] = "Draw (Time Limit)"
            result["rounds"] = max_rounds

        return result, self.battle_log

    def _choose_action(self, combatant, target):
        """Mock AI to select a blessing based on tactical logic."""
        if not hasattr(combatant, 'is_player') or not combatant.is_player:
            # Mobs use their own AI in combat_processor, but we can pre-select if we want.
            return None 

        blessings = {b_id: self.game.world.blessings.get(b_id) for b_id in combatant.equipped_blessings if b_id in self.game.world.blessings}
        
        # --- Assassin Tactical Logic ---
        if "assassin" in [getattr(combatant, 'active_class', '').lower(), combatant.name.lower()]:
            # Priority 1: Backstab if concealed
            if "concealed" in getattr(combatant, 'status_effects', {}):
                bs = blessings.get('backstab')
                if bs:
                    can, _ = Auditor.can_invoke(bs, combatant)
                    if can:
                        combatant.pending_skill = {'skill': bs, 'args': target.name}
                        return bs
            
            # Priority 2: Hide to get concealed
            hide = blessings.get('hide')
            if hide and "concealed" not in getattr(combatant, 'status_effects', {}):
                can, _ = Auditor.can_invoke(hide, combatant)
                if can:
                    combatant.pending_skill = {'skill': hide, 'args': combatant.name} # Self target
                    return hide

        # --- General High-Power Logic ---
        available = []
        for b in blessings.values():
            can, _ = Auditor.can_invoke(b, combatant)
            if can: available.append(b)
        
        if not available: return None
        
        # Sort by base_power (Priority to heavy hitters)
        available.sort(key=lambda x: getattr(x, 'base_power', 0), reverse=True)
        
        chosen = available[0]
        combatant.pending_skill = {'skill': chosen, 'args': target.name}
        return chosen

    def _flush_outputs(self, entities):
        for e in entities:
            if hasattr(e, 'connection') and hasattr(e.connection, 'output'):
                for line in e.connection.output:
                    # Clean ANSI for logging if needed, or keep for UI
                    self.battle_log.append(strip_ansi(line))
                e.connection.output = []

if __name__ == "__main__":
    # Test run
    sim = SimEngine()
    room = sim.create_room(terrain="forest")
    p1 = sim.setup_player("Kip", "barbarian", room)
    p2 = sim.setup_player("Dummy", "knight", room)
    
    result, log = sim.run_duel(p1, p2, room)
    print(f"Winner: {result['winner']} in {result['rounds']} rounds.")
    # for line in log: print(line)
