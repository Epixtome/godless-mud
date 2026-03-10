# Refactor Audit: Death Protocol Decoupling

> **Status:** COMPLETED
> **Objective:** Remove circular dependencies between Entities and Combat Lifecycle without breaking the game.
> **Risk Level:** High (Core Logic)

## 1. The "Wiring" Map (Current Dependencies)
We have identified that the "Death Signal" currently travels through these specific hardcoded paths. These are the "cables" we intend to cut.

**Who calls `handle_death` right now?**
1.  `models/entities/player.py`: Uses an **inline import** inside `take_damage`.
2.  `models/entities/monster.py`: Uses an **inline import** inside `take_damage`.
3.  `logic/engines/combat_processor.py`: Contains legacy wrappers `handle_mob_death` and `handle_player_death`.

## 2. The "Ghost" Code Risks
If we switch to the Event Bus, the following code becomes "Dead" (unused but dangerous if left behind):
- The inline imports in `player.py` and `monster.py`.
- The legacy wrappers in `combat_processor.py`.# Refactor Audit: Death Protocol Decoupling

> **Status:** AUDIT PHASE
> **Objective:** Remove circular dependencies between Entities and Combat Lifecycle without breaking the game.
> **Risk Level:** High (Core Logic)

## 1. The "Wiring" Map (Current Dependencies)
We have identified that the "Death Signal" currently travels through these specific hardcoded paths. These are the "cables" we intend to cut.

**Who calls `handle_death` right now?**
1.  `models/entities/player.py`: Uses an **inline import** inside `take_damage`.
2.  `models/entities/monster.py`: Uses an **inline import** inside `take_damage`.
3.  `logic/engines/combat_processor.py`: Contains legacy wrappers `handle_mob_death` and `handle_player_death`.
4.  `logic/engines/combat_actions.py`: Direct call inside `execute_attack`.

## 2. The "Ghost" Code Risks
If we switch to the Event Bus, the following code becomes "Dead" (unused but dangerous if left behind):
- The inline imports in `player.py` and `monster.py`.
- The legacy wrappers in `combat_processor.py`.

## 3. The Safe Transition Plan
We will use the **"Strangler Fig" Pattern**: Add the new system alongside the old one, verify it works, then remove the old one.

1.  **[CURRENT STEP] Audit:** Add logging to `combat_lifecycle.py` to shout whenever `handle_death` is called directly. This proves *who* is still using the old wiring.
2.  **Parallel Wire:** Create the Event Listener, but keep the old function active.
3.  **Migrate One:** Change `Monster` to use the Event.
4.  **Verify:** Kill a monster. If the `[AUDIT]` log stops appearing, the new wire is working.
5.  **Migrate All:** Change `Player`.
6.  **Cleanup:** Delete the inline imports and legacy wrappers only when the logs are silent.

## 4. Verification Checklist
- [ ] Audit Logging installed.
- [ ] `Monster.py` migrated to Event Bus.
- [ ] `Player.py` migrated to Event Bus.
- [x] `combat_processor.py` legacy wrappers removed.
- [x] `combat_lifecycle.py` direct access deprecated.

## 3. The Safe Transition Plan
We will use the **"Strangler Fig" Pattern**: Add the new system alongside the old one, verify it works, then remove the old one.

1.  **[CURRENT STEP] Audit:** Add logging to `combat_lifecycle.py` to shout whenever `handle_death` is called directly. This proves *who* is still using the old wiring.
2.  **Parallel Wire:** Create the Event Listener, but keep the old function active.
3.  **Migrate One:** Change `Monster` to use the Event.
4.  **Verify:** Kill a monster. If the `[AUDIT]` log stops appearing, the new wire is working.
5.  **Migrate All:** Change `Player`.
6.  **Cleanup:** Delete the inline imports and legacy wrappers only when the logs are silent.

## 4. Verification Checklist
- [ ] Audit Logging installed.
- [ ] `Monster.py` migrated to Event Bus.
- [ ] `Player.py` migrated to Event Bus.
- [ ] `combat_processor.py` legacy wrappers removed.
- [ ] `combat_lifecycle.py` direct access deprecated.
