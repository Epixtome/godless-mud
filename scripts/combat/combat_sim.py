import sys
import os
import random

# Add project root to path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from logic.calibration import MaxValues, HeatCoefficients

class SimEntity:
    def __init__(self, name, kit):
        self.name = name
        self.kit = kit
        self.hp = MaxValues.HP
        self.max_hp = MaxValues.HP
        self.heat = 0
        self.stability = 100
        self.max_stability = 100
        self.cooldown_ticks = 0
        
        # Stats for Report
        self.wins = 0
        self.overheat_count = 0
        
        # Disengage Logic
        self.disengaged = False
        self.disengage_timer = 0
        self.disengage_cooldown = 0
        
        # Kit Config (Approximation of Gear + Blessings)
        if kit == "Knight":
            self.defense = 12      # Heavy Plate + Shield (Adjusted for 50 round scaling)
            self.damage = 16       # Iron Sword + Kit Bonus (Adjusted)
            self.max_heat = 250    # Knight Heat Cap (Buffed)
            self.heat_cost = 15    # Heavy Action Cost
            self.stability_cost = 10
            self.tags = ["plains", "castle"]
        else: # Wanderer
            self.defense = 6       # Leather (Adjusted)
            self.damage = 18       # Standard Weapon (Adjusted)
            self.max_hp = 150      # Wanderer HP Nerf
            self.max_heat = 100    # Standard Heat Cap
            self.heat_cost = 5     # Light Action Cost
            self.stability_cost = 5
            self.tags = ["forest", "road"]

    def reset(self):
        self.hp = self.max_hp
        self.heat = 0
        self.stability = self.max_stability
        self.cooldown_ticks = 0
        self.disengaged = False
        self.disengage_timer = 0
        self.disengage_cooldown = 0

    def act(self, target, terrain):
        # 0. Handle Disengagement State
        if self.disengaged:
            self.hp = min(self.max_hp, self.hp + 5) # HP Regen while disengaged
            self.disengage_timer -= 1
            if self.disengage_timer <= 0:
                self.disengaged = False
                self.disengage_cooldown = 15 # Cooldown before next disengage
            return

        # 1. Check Cooldown (Overheat)
        if self.cooldown_ticks > 0:
            self.cooldown_ticks -= 1
            # Cooling down faster when resting/stunned
            self.heat = max(0, self.heat - 10)
            return

        # 1.5 Check Disengage Trigger (HP < 30%)
        if self.hp < (self.max_hp * 0.30) and self.disengage_cooldown <= 0:
            self.disengaged = True
            self.disengage_timer = 3
            return

        # If target is disengaged, we chase (generate heat but no damage)
        if target.disengaged:
            self.heat += 5 # Chasing cost
            return

          # 2. Generate Heat (With Stability Mitigation)
        actual_heat_cost = self.heat_cost
        if self.stability > 50:
            reduction = int((self.stability - 50) / 20)
            if reduction > 0:
                actual_heat_cost = max(1, actual_heat_cost - reduction)
        
        self.heat += actual_heat_cost
       
               
        # 3. Check Overheat Threshold
        if self.heat >= self.max_heat:
            self.cooldown_ticks = int(HeatCoefficients.OVERHEAT_DURATION)
            self.overheat_count += 1
            return # Turn ends immediately, action fails

        # 4. Consume Stability (Exertion)
        self.stability = max(0, self.stability - self.stability_cost)

        # 5. Calculate Damage
        # Edge Mechanic (Accuracy)
        hit_chance = 0.9
        if terrain in self.tags:
            hit_chance = 1.0 # +10% Accuracy
            
        if random.random() > hit_chance:
            return # Miss

        multiplier = 1.0
        # Off-Balance Mechanic
        if target.stability <= 0:
            multiplier = 1.5 
            
        raw_dmg = int(self.damage * multiplier)
        final_dmg = max(1, raw_dmg - target.defense)
        
        # Apply Damage Cap
        final_dmg = min(MaxValues.DAMAGE, final_dmg)
        
        target.hp -= final_dmg
        
        # 6. Impact Stability Drain on Target (Physics)
        target.stability = max(0, target.stability - 5)

def run():
    knight = SimEntity("Knight", "Knight")
    wanderer = SimEntity("Wanderer", "Wanderer")
    
    total_turns = 0
    runs = 1000
    terrains = ["plains", "forest", "road", "castle", "swamp"]
    
    print(f"Starting Monte Carlo Simulation ({runs} runs)...")
    
    for _ in range(runs):
        knight.reset()
        wanderer.reset()
        turns = 0
        terrain = random.choice(terrains)
        
        while knight.hp > 0 and wanderer.hp > 0:
            turns += 1
            
            # Trade Actions
            knight.act(wanderer, terrain)
            if wanderer.hp <= 0: break
            
            wanderer.act(knight, terrain)
            if knight.hp <= 0: break
            
            # End of Turn Regen (Passive)
            if knight.cooldown_ticks == 0:
                decay = 1 if knight.disengaged else 2 # Slowed decay if disengaged
                knight.heat = max(0, knight.heat - decay)
                knight.stability = min(knight.max_stability, knight.stability + 2)
                
            if wanderer.cooldown_ticks == 0:
                decay = 1 if wanderer.disengaged else 2
                wanderer.heat = max(0, wanderer.heat - decay)
                wanderer.stability = min(wanderer.max_stability, wanderer.stability + 2)
            
            # Cooldown Tick for Disengage
            if knight.disengage_cooldown > 0: knight.disengage_cooldown -= 1
            if wanderer.disengage_cooldown > 0: wanderer.disengage_cooldown -= 1
                
        total_turns += turns
        if knight.hp > 0:
            knight.wins += 1
        else:
            wanderer.wins += 1

    print(f"\n--- Simulation Report ---")
    print(f"Win/Loss Ratio: Knight {knight.wins} - {wanderer.wins} Wanderer")
    print(f"Knight Win Rate: {knight.wins/runs:.1%}")
    print(f"Avg Turns to Kill: {total_turns/runs:.1f}")
    print(f"Knight Overheats: {knight.overheat_count} (Avg {knight.overheat_count/runs:.1f}/fight)")
    print(f"Wanderer Overheats: {wanderer.overheat_count} (Avg {wanderer.overheat_count/runs:.1f}/fight)")

if __name__ == "__main__":
    run()
