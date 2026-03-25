# Godless: Developer Script Reference

This document catalogs the autonomous scripts available in `scripts/dev/` and other subdirectories. Use these for testing, validation, and world building.

## 🛠️ Development & Auditing (`scripts/dev/`)

| Script | Purpose | Usage Example |
| :--- | :--- | :--- |
| `map_renderer.py` | Renders the world map and player clusters for debugging. | `python scripts/dev/map_renderer.py` |
| `combat_sim.py` | Simulates scaling math for blessings without running the server. | `python scripts/dev/combat_sim.py --class monk` |
| `audit_data.py` | Scans `data/` for schema violations or missing keys. | `python scripts/dev/audit_data.py` |
| `system_check.py` | Runs a health check on core systems (Combat, Quest, Events). | `python scripts/dev/system_check.py` |
| `scaffold_class.py` | Generates the directory structure and base files for a new class. | `python scripts/dev/scaffold_class.py [name]` |
| `smart_tagger.py` | Batch updates items or blessings with new tags. | `python scripts/dev/smart_tagger.py --add martial` |
| `telemetry_aggregator.py` | Parses `logs/telemetry.jsonl` into readable summaries. | `python scripts/dev/telemetry_aggregator.py --last 10m` |

## 🌍 World & Content (`scripts/world/`)

| Script | Purpose |
| :--- | :--- |
| `aethelgard_gen.py` | Generates new room shards based on topographical rules. |
| `validator.py` | Checks for broken exits or disconnected coordinates in zone files. |

## 🥋 Combat & Class (`scripts/combat/`)

| Script | Purpose |
| :--- | :--- |
| `tune_scaling.py` | Adjusts multipliers in blessing JSONs to match target DPS curves. |

---

## 🧭 How to use these in your workflow
1.  **Before committing logic**: Run `scripts/dev/system_check.py` to ensure no circular dependencies were introduced.
2.  **When adding data**: Run `scripts/dev/audit_data.py` to catch spelling errors in keys.
3.  **To visualize changes**: Use `scripts/dev/map_renderer.py` to see how new rooms or terrain look in the engine.
