# Changelog - 2026-03-04

## Logic Modules: Beastmaster
### `logic/modules/beastmaster/actions.py`
- **Fix (`pets` command)**: Resolved an issue where the first pet in the library was always marked as `[ACTIVE]`. The command now correctly identifies the active pet by checking the current room for a mob owned by the player with a matching name.
- **Feature (`pets` command)**: Added display of pet tags (e.g., `[tough, tank]`) to the list output.
- **Optimization (`call` command)**: Refactored the pet dismissal logic. It now checks the player's current room for the active pet before scanning the entire world, reducing overhead for the most common use case.