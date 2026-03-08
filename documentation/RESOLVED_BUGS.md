# Resolved Bugs Archive

| Date | User | Description | Resolution |
|------|------|-------------|------------|
| 2026-03-06 | kip | Blind south exit at 109,124 | Map regenerated with corrected 125x125 grid logic. |
| 2026-03-06 | kip | Elevation visibility issues on mountains | Implemented "Top-Down" scanning in Vision Engine. |
| 2026-03-06 | kip | Recall point in ocean (0,0,-5) | Updated `godless_mud.py` to use dynamic center (62,62,0). |
| 2026-03-06 | kip | LoS East/West mountain visibility | Refactored `vision_engine.py` with improved raycasting. |
| 2026-03-06 | kip | Help system duplicate entries | Merged blessing and status effect help logic in `help_system_commands.py`. |
| 2026-03-06 | kip | Sacrifice corpse favor | Integrated `distribute_favor` from combat engine into the sacrifice command. |
| 2026-03-06 | kip | Dragon Strike scaling | Exponential scaling implemented: 10 Flow = 10x DMG. |
| 2026-03-06 | kip | Missing POI tree in Sylvanis | Added "Ancient Gnarled Oak" to deterministic POI logic. |
| 2026-03-06 | kip | Everything named "Null_Void" | Corrected zone boundary logic in `master_architect.py`. |
