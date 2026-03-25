# Godless: Class Kit Composition Standard (V6.2)

> **Status:** ACTIVE PROTOCOL
> **Objective:** Ensure all 50+ classes maintain PvP readability, tactical depth, and balanced utility.

All class kits in Godless adhere to the **8-Ability Standard**. This composition prevents "ability bloat" and ensures that combat remains a readable "Tactical Fencing" match rather than a spam-fest.

## 1. THE 8-ABILITY DECK STRUCTURE
Each class kit must contain exactly 8 blessings, distributed across the following tactical categories:

| Category | Count | Keywords | Purpose |
| :--- | :--- | :--- | :--- |
| **Setup** | 2 | `Builder`, `Opener` | Apply primary class states (e.g., *prone*, *off-balance*) and generate resources. |
| **Payoff** | 2 | `AOE`, `Finisher` | Consume or exploit states for massive damage or secondary effects. |
| **Defense** | 2 | `Reaction`, `Parry`, `Brace` | Self-preservation, counters, or damage mitigation. |
| **Mobility** | 1 | `Dash`, `Blink`, `Escape` | Repositioning, breaking control states (e.g., *pinned*), or LOS control. |
| **Utility** | 1 | `Ultimate`, `Identity` | Class-defining signature tool (e.g., *War Cry*, *Camouflage*, *Summon*). |

## 2. ABILITY TYPE KEYWORDS
When designing custom abilities, align them with these functional roles:

*   **Builder**: A low-cost or resource-generating ability used as an opener. (Example: `Triple Kick`)
*   **Setup**: An ability designed to apply a specific state (e.g., *prone*) to enable a Payoff. (Example: `Leg Sweep`)
*   **AOE (Payoff)**: A state-dependent area-of-effect attack. (Example: `Whirlwind`)
*   **Finisher (Payoff)**: A high-damage single-target strike that scales with existing target states. (Example: `Iron Palm`)
*   **Reaction (Defense)**: An ability that triggers in response to damage or provides a short-duration parry/buff. (Example: `Seven Fists`)
*   **Mobility**: A tool to change position or remove movement-impairing effects. (Example: `Cloud Step`)
*   **Ultimate (Utility)**: A high-impact, class-defining ability often requiring 100% resource. (Example: `Bloodrage`)

## 3. DESIGN PHILOSOPHY: THE 2-AXIS RULE
Each class is balanced around **2 Primary Axes** (e.g., *Tempo* and *Endurance*).
*   **Axial Balance**: The 8 abilities should reflect these axes (e.g., the Paladin's Setup/Payoff focus on *Endurance/Lethality*).
*   **State Specialty**: Each class should specialize in interacting with only **2-3 specific states** (e.g., Monk focuses on *prone* and *off-balance*).

## 4. INTEGRATING CUSTOM ABILITIES
To add user-designed abilities while maintaining the standard:
1.  **Slot Replacement**: Replace one of the 8 slots in `data/kits.json` while maintaining the category counts (e.g., replace a `Defense` tool with a new `Defense` tool).
2.  **The "Plus One" Extra**: While the engine technically permits >8 blessings in `equipped_blessings`, it is recommended to keep the active kit at 8 for balancing.
3.  **JSON Registration**: Add the new ability to the appropriate blessing shard in `data/blessings/[class].json` and ensure it has the correct `identity_tags` (e.g., `["setup", "builder"]`).

---
> [!IMPORTANT]
> All new abilities MUST be audited via `scripts/dev/audit_data.py` to ensure schema compliance.
