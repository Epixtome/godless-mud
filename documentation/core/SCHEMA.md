# Godless Data Schema Registry

This document serves as the "Source of Truth" for all data structures within the Godless MUD. 

## 1. Classes (`data/classes/*.json`)
Defined in kingdom-sharded files (e.g., `light.json`).
- **Key**: String (Class ID, e.g., `paladin`)
- **Structure**:
    - `id`: string (Machine ID)
    - `name`: string (Display Name)
    - `description`: string
    - `kingdom`: string (Alignment)
    - `recipe`: object (Resonance requirements, e.g., `{"holy": 5}`)
    - `engine_passive`: object
        - `name`: string
        - `description`: string

## 2. Blessings (`data/blessings/[class].json`)
- **Key**: String (Blessing ID, e.g., `double_strike`)
- **Structure**:
    - `id`: string (Identical to key)
    - `name`: string (Display Name)
    - `tier`: integer (1-4)
    - `cost`: integer (Resource cost to acquire or use)
    - `description`: string (User-facing text)
    - `identity_tags`: list[string] (Metadata for scaling and resonance)
    - `axis`: string (Tactical category: Position, Tempo, Vision, Endurance, Elemental, Utility)
    - `action`: string (Reference to Python function in `blessing_actions.py`)
    - `requirements`: object (Required class, stamina, chi, etc.)
    - `scaling`: object (Single object or list of objects for math)
        - `scaling_tag`: string (Stat/Resonance being used)
        - `multiplier`: float
        - `base_value`: integer (optional)

## 3. Zones (`data/zones/*.json`)
- **Structure**:
    - `rooms`: object (Key: Room ID, Value: Room Object)
- **Room Object**:
    - `id`: string (format: `zone.x.y.z`)
    - `name`: string
    - `description`: string
    - `terrain`: string (e.g., `plains`, `forest`)
    - `x`: integer
    - `y`: integer
    - `z`: integer
    - `elevation`: integer (-5 to +5)
    - `exits`: object (Key: Direction, Value: Target Room ID)

## 4. Telemetry (`logs/telemetry.jsonl`)
- **Structure**:
    - `time`: string (HH:MM:SS.mmm)
    - `entity`: string (Player/NPC name)
    - `room_id`: string
    - `type`: string (Event Type: `SKILL_EXECUTE`, `RESOURCE_DELTA`, `COMBAT_DETAIL`, `STATUS_CHANGE`, `BUG_REPORT`, `VITALS`)
    - `data`: object (Payload specific to the event type)

## 5. Shrines (`data/shrines.json`)
- **Key**: String (Shrine ID, e.g., `light_cap`)
- **Structure**:
    - `id`: string (Identical to key)
    - `name`: string (Display Name)
    - `description`: string (Lore and tactical info)
    - `deity_id`: string (The Deity who grants the kit)
    - `kingdom`: string (The "Home" or default kingdom)
    - `captured_by`: string (The kingdom currently holding the shrine)
    - `coords`: list[int] (x, y, z)
    - `potency`: integer (Base influence strength)
    - `decay`: float (Drop-off per tile distance)
    - `is_capital`: boolean (Invulnerability and high-sec flag)
    - `favor_cost_mult`: float (The Ritual Swap discount if owner matches visitor)

---
> [!IMPORTANT]
> All new data additions MUST follow these structures to ensure compatibility with the Telemetry Aggregator and Map Renderer.
