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

## 2. Blessings (`data/blessings/[Kingdom]/[Deity]/tier_[N].json`)
- **Key**: String (Blessing ID, e.g., `dragon_strike`)
- **Structure**:
    - `id`: string
    - `name`: string
    - `description`: string
    - `deity_id`: string
    - `tier`: integer (1-4)
    - `identity_tags`: list[string] (Metadata tags for resonance/logic)
    - `requirements`: object (Resource costs or state checks)
    - `scaling`: list[object] (Damage/Effect calculation entries)
        - `scaling_tag`: string (Stat/Resonance being used)
        - `multiplier`: float
        - `base_value`: integer

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

---
> [!IMPORTANT]
> All new data additions MUST follow these structures to ensure compatibility with the Telemetry Aggregator and Map Renderer.
