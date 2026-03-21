# Godless: AI Agent Navigation & Knowledge Index

This index serves as the primary entry point for AI Agents working on Godless. It provides a map of the codebase and explains the tracking protocols.

## 🗺️ Codebase Map (Where things are)

| Directory | Purpose | Key Files |
| :--- | :--- | :--- |
| `logic/core/` | Global systems & Facades | `__init__.py`, `combat.py`, `resources.py` |
| `logic/modules/` | Class-specific logic | `[class]/events.py`, `[class]/state.py` |
| `logic/handlers/` | Input & External Interfaces | `input_handler.py`, `command_manager.py` |
| `data/` | Configuration & Persistence | `classes/`, `blessings/`, `zones/` |
| `documentation/` | Living Artifacts & Guides | `SCHEMA.md`, `class_registry.md`, `KIT_COMPOSITION.md` |

| `scripts/dev/` | Developer Tooling | `map_renderer.py`, `combat_sim.py` |

---

## 🧭 Tracking Protocol (How I know what to use)

To maintain context and efficiency, I use a multi-layered tracking approach:

### 1. The Protocol Layer (`GEMINI.md`)
I start every session by reviewing `GEMINI.md`. It defines the "Architecture of Truth" (e.g., Facade standards, line limits, and the "Clean Border" protocol).

### 2. The Registry Layer (`documentation/`)
I use specific files to track the "Live State" of the project's systems:
-   **`GODLESS_SYSTEM_REGISTRY.md`**: The definitive compilation of versions, acronyms, and protocols. I check this to resolve terminology confusion.
-   **`class_registry.md`**: Which class hooks are active. I check this before adding new event listeners.
-   **`SCHEMA.md`**: Structural requirements for data files. I use this to validate and create new JSON content.
-   **`COMMAND_REFERENCE.md`**: Available admin and player commands.
-   **`KIT_COMPOSITION.md`**: The 8-ability tactical kit standard (Setup, Payoff, Defense, etc.). I use this to balance new classes.
-   **`building_suite_workflow.md`**: The master guide for handcrafted world-shaping.

-   **`engine_v5_3_refinement.md`**: Summary of V5.3 structural fixes and handover details.

### 3. The Structural Layer (Facades)
I never search for local utility functions if a system-wide facade exists. I always prioritize:
`from logic.core import combat, resources, messaging`
This ensures I am using the standardized interface and not bypassing game rules.

### 4. The Tooling Layer (`scripts/dev/`)
I use internal scripts to "see" and "test" without manual grep:
-   **`map_renderer.py`**: To understand world layout.
-   **`combat_sim.py`**: To verify damage scaling formulas.
-   **`audit_data.py`**: To check for schema drift.

---

## 🛠️ Operational workflows

If you are performing a common task, follow these standard operation procedures:

1.  **Adding a Class**: See `GEMINI.md` Section 3 (GCA Architecture).
2.  **Updating Data**: Consult `SCHEMA.md` for structure, then use `scripts/dev/audit_data.py`.
3.  **Debugging Combat**: Use `scripts/dev/combat_sim.py` to isolate scaling logic from the network loop.

---
> [!TIP]
> **Proactive Documentation**: If you discover a pattern or a new registry is needed, CREATE IT in `documentation/`. If you change a core system, update the Facade in `logic/core/__init__.py`.
