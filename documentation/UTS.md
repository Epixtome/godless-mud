# GODLESS: Class Kit System (V4.5)

> **Status:** ACTIVE PROTOCOL
> **Replaces:** Unified Tag Synergy (UTS)
> **Source of Truth:** `data/kits.json`

## 1. Core Philosophy
Godless uses a **Kit-Based Class System**. Instead of dynamically calculating a class based on equipped tags, players explicitly adopt a **Class Kit** from a Deity.

*   **The Kit is the Class:** A Kit defines the *exact* loadout (Blessings and Gear) for an archetype.
*   **Rigid Identity:** You cannot mix-and-match blessings from different classes. If you are a Monk, you use the Monk Kit.
*   **Deity Granted:** You switch classes by visiting a Deity and using the `become` command (e.g., `become knight`).

---

## 2. The Kit Definition (`kits.json`)
Classes are defined in `data/kits.json`. This file is the absolute source of truth for what a class *is*.

### Schema
```json
"class_id": {
  "name": "Display Name",
  "description": "Flavor text.",
  "gear": [
    "item_id_1",
    "item_id_2"
  ],
  "blessings": [
    "blessing_id_1",
    "blessing_id_2",
    "blessing_id_3"
  ]
}
```

## 3. The "Become" Protocol
When a player runs `become <class>` at a shrine:
1.  **Validation:** The system checks if the Deity grants that class.
2.  **Cost:** The player pays Favor (usually 250).
3.  **Kit Application:**
    *   `player.active_class` is updated.
    *   `player.active_kit` is populated with the data from `kits.json`.
    *   **Auto-Equip:** The system automatically strips old gear/blessings and equips the items/skills defined in the Kit.

## 4. The Auditor's Role
The `Auditor` (`logic/engines/blessings/auditor.py`) enforces the Kit boundaries.
*   **Identity Check:** `check_identity` verifies that any blessing the player attempts to use is present in their `active_kit`.
*   **Result:** If you try to cast *Fireball* while in the *Warrior* kit, the Auditor rejects it, even if you technically "know" the spell from a previous life.