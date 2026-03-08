> [!CAUTION]
> **LEGACY ARCHITECTURE**: This document reflects Godless MUD v2.x architecture (Pre-Feb 14, 2026 Reset). **Do not use for implementation.** Reference ARCHITECTURE.md for current V3.1+ standards.

# Class Design Reference

## Philosophy
In Godless, **Classes do not exist** as rigid containers. They are **Identities** recognized by the world when a player's soul (Blessing Deck) resonates with a specific frequency (Tags).

To "build" a class, we define:
1. **The Identity**: What tags are required?
2. **The Enablers**: Which blessings provide these tags?
3. **The Payoff**: What bonuses or exclusive Tier 4 abilities does this identity unlock?

---

## Class Definition Template

### [Class Name] (ID: `class_id`)
**Description**: Flavor text describing the class.
**Playstyle**: A short summary of how it plays (e.g., "High Burst, Low Defense").

#### 1. Identity Requirements
The specific combination of tags needed to trigger this class.
- **Primary Tag**: `tag_name` (Count: X)
- **Secondary Tag**: `tag_name` (Count: Y)

#### 2. Prestige Path (Unlock Logic)
*How does a player become this class?*
- **Basic Class**: Achievable via Tier 1/2 blessings available to everyone.
- **Prestige Class**: Requires specific tags found only on Tier 3/4 blessings.
    - *Constraint*: Tier 4 blessings often require a specific **Active Class** to buy.
    - *Flow*: `Rogue` (Class) -> Buy `Shadow Step` (T3 Blessing) -> Equip it -> Gain `shadow` tag -> Become `Ninja`.

#### 3. Key Blessings (The Enablers)
List the blessings that help form this identity.
| Blessing Name | Tier | Tags Provided | Deity |
|---------------|------|---------------|-------|
| *Kick*        | 1    | `martial`     | None  |
| *Backstab*    | 2    | `martial`, `dark` | Nox |

---

## Detailed Class Definitions

### Alchemist (ID: `alchemist`)
**Description**: A versatile manipulator of matter who thrives on modifying the battlefield through transmutation.
**Playstyle**: Flexible / Strategic / Transmutation
**Kingdom**: Light / Dark / Instinct (Int-based)

#### 1. Identity Requirements
- **Primary**: `int` (Count: 3)
- **Secondary**: `alchemy` (Count: 2)
- **Tertiary**: `utility` (Count: 1)

#### 2. Key Blessings (The Enablers)
| Blessing Name | Tier | Tags | Deity |
|---------------|------|------|-------|
| *Flask Toss* | 1 | `alchemy`, `ranged` | Lumos |
| *Reinforce* | 1 | `alchemy`, `buff` | Lumos |
| *Corrosive Vial* | 2 | `alchemy`, `acid` | Vex |
| *Volatile Reaction* | 2 | `alchemy`, `energy` | Echo |
| *Philosopher's Stone* | 4 | `ultimate`, `alchemy` | Echo |

---

### Archer (ID: `ranger`)
**Description**: A precision striker who controls range and pins enemies.
**Playstyle**: Precision / Range Control
**Kingdom**: Instinct (Dex-based)

#### 1. Identity Requirements
- **Primary**: `instinct` (Count: 3)
- **Secondary**: `marksmanship` (Count: 2)

#### 2. Key Blessings (The Enablers)
| Blessing Name | Tier | Tags | Deity |
|---------------|------|------|-------|
| *Quick Shot* | 1 | `marksmanship`, `dex` | Feral |
| *Crossbow Shot* | 1 | `marksmanship`, `ranged` | Raven |
| *Snipe* | 2 | `marksmanship`, `lethal` | Raven |
| *Net Trap* | 2 | `crowd_control`, `stalker` | Feral |

---

### Assassin (ID: `assassin`)
**Description**: A stealth specialist who excels at positioning and lethal backstabs.
**Playstyle**: High Risk / Positioning / Traps
**Kingdom**: Dark (Dex-based)

#### 1. Identity Requirements
- **Primary**: `dark` (Count: 3)
- **Secondary**: `stealth` (Count: 1)
- **Tertiary**: `martial` (Count: 1)

#### 2. Key Blessings (The Enablers)
| Blessing Name | Tier | Tags | Deity |
|---------------|------|------|-------|
| *Backstab* | 2 | `stealth`, `martial` | Nox |
| *Shadow Step* | 2 | `mobility`, `dark` | Nox |
| *Venom Coat* | 2 | `alchemy`, `poison` | Nox |
| *Shroud of Shadows* | 3 | `stealth`, `dark` | Nox |

---

### Barbarian (ID: `barbarian`)
**Description**: A force of raw, chaotic power, focused on high-damage melee combat and disruptive battlefield presence.
**Playstyle**: Frontline Devastation / Disruptive
**Kingdom**: Instinct (Str-based)

#### 1. Identity Requirements
- **Primary**: `instinct` (Count: 3)
- **Secondary**: `martial` (Count: 2)
- **Tertiary**: `rage` (Count: 1)

#### 2. Key Blessings (The Enablers)
| Blessing Name | Tier | Tags | Deity |
|---------------|------|------|-------|
| *Heavy Swing* | 1 | `instinct`, `martial` | Krog |
| *Reckless Strike* | 2 | `instinct`, `rage` | Krog |
| *Battle Cry* | 2 | `instinct`, `buff` | Krog |
| *Earthshatter* | 4 | `ultimate`, `control` | Krog |

---

### Bard (ID: `bard`)
**Description**: A support-oriented musician who uses melodies to buff allies and debuff enemies.
**Playstyle**: Support / Crowd Control / Rhythm
**Kingdom**: Light (Luk/Wis-based)

#### 1. Identity Requirements
- **Primary**: `light` (Count: 3)
- **Secondary**: `buff` (Count: 2)
- **Tertiary**: `control` (Count: 1)

#### 2. Key Blessings (The Enablers)
| Blessing Name | Tier | Tags | Deity |
|---------------|------|------|-------|
| *Protection from Evil* | 1 | `light`, `buff` | Fortuna |
| *Trip* | 2 | `light`, `control` | Celeris |
| *Guardians Oath* | 2 | `light`, `buff` | Fortuna |
| *Banner of Kings* | 4 | `ultimate`, `tactics` | Solas |

---

---

### Berserker (ID: `berserker`)
**Description**: An offensive powerhouse that thrives in the chaos of melee combat.
**Playstyle**: All-in Aggression / Risk vs Reward
**Kingdom**: Instinct (Str/Con-based)

#### 1. Identity Requirements
- **Primary**: `instinct` (Count: 3)
- **Secondary**: `rage` (Count: 2)

#### 2. Key Blessings (The Enablers)
| Blessing Name | Tier | Tags | Deity |
|---------------|------|------|-------|
| *Bloodlust* | 2 | `instinct`, `rage` | Krog |
| *Reckless Swing* | 3 | `instinct`, `rage` | Krog |
| *Undying Rage* | 4 | `ultimate`, `rage` | Ursus |

---

### Black Mage (ID: `black_mage`)
**Description**: The epitome of raw magical destruction, specializing in high-damage AoE.
**Playstyle**: Glass Cannon / AoE / Positioning
**Kingdom**: Dark (Int-based)

#### 1. Identity Requirements
- **Primary**: `int` (Count: 4)
- **Secondary**: `destruction` (Count: 2)

#### 2. Key Blessings (The Enablers)
| Blessing Name | Tier | Tags | Deity |
|---------------|------|------|-------|
| *Fireburst* | 1 | `elemental`, `destruction` | Aldildod |
| *Pyroclasm* | 3 | `elemental`, `destruction` | Aldildod |
| *Meteor* | 4 | `ultimate`, `destruction` | Vex |

---

### Chemist (ID: `chemist`)
**Description**: A battlefield support expert using potions for healing, buffs, and explosives.
**Playstyle**: Support / Resource Management
**Kingdom**: Light (Int/Wis-based)

#### 1. Identity Requirements
- **Primary**: `int` (Count: 3)
- **Secondary**: `alchemy` (Count: 3)

#### 2. Key Blessings (The Enablers)
| Blessing Name | Tier | Tags | Deity |
|---------------|------|------|-------|
| *Flask Toss* | 1 | `alchemy`, `ranged` | Lumos |
| *Healing Mist* | 2 | `alchemy`, `healing` | Sophia |
| *Elixir of Life* | 4 | `ultimate`, `alchemy` | Sophia |

---

### Cleric (ID: `cleric`)
**Description**: A divine caster focused on healing, protection, and purging evil.
**Playstyle**: Healer / Buffer
**Kingdom**: Light (Wis-based)

#### 1. Identity Requirements
- **Primary**: `light` (Count: 4)
- **Secondary**: `healing` (Count: 1)
- **Tertiary**: `protection` (Count: 1)

#### 2. Key Blessings (The Enablers)
| Blessing Name | Tier | Tags | Deity |
|---------------|------|------|-------|
| *Cure Light* | 2 | `light`, `healing` | Sophia |
| *Sanctuary* | 2 | `light`, `protection` | Sophia |
| *Holy Smite* | 3 | `light`, `damage` | Lumos |
| *Resurrection* | 4 | `ultimate`, `healing` | Sophia |

---

### Druid (ID: `druid`)
**Description**: A guardian of nature who commands earth, storms, and growth.
**Playstyle**: Versatile Caster / Control
**Kingdom**: Instinct (Wis-based)

#### 1. Identity Requirements
- **Primary**: `instinct` (Count: 3)
- **Secondary**: `nature` (Count: 3)

#### 2. Key Blessings (The Enablers)
| Blessing Name | Tier | Tags | Deity |
|---------------|------|------|-------|
| *Tremor* | 1 | `instinct`, `nature` | Sylva |
| *Stone Skin* | 2 | `instinct`, `nature` | Sylva |
| *Lightning Storm* | 3 | `instinct`, `nature` | Sylva |
| *Earthquake* | 4 | `ultimate`, `nature` | Sylva |

---

### Elementalist (ID: `elementalist`)
**Description**: A mage who chains elemental spells for devastating combos.
**Playstyle**: Combo Caster / AoE
**Kingdom**: Light (Int-based)

#### 1. Identity Requirements
- **Primary**: `int` (Count: 4)
- **Secondary**: `elemental` (Count: 2)
- **Tertiary**: `spell` (Count: 2)

#### 2. Key Blessings (The Enablers)
| Blessing Name | Tier | Tags | Deity |
|---------------|------|------|-------|
| *Fireburst* | 1 | `light`, `elemental` | Aldildod |
| *Glacier Spike* | 1 | `light`, `elemental` | Aldildod |
| *Frost Nova* | 2 | `light`, `elemental` | Aldildod |
| *Elemental Cataclysm* | 4 | `ultimate`, `elemental` | Aldildod |

---

## Example: The Prestige Flow (Rogue -> Ninja)

### Base Class: Rogue
- **Reqs**: `dex: 3`, `rogue: 1`
- **Playstyle**: Evasive, opportunistic damage.
- **Source**: Tier 1/2 blessings from **Nox** and **Raven**.

### Prestige Class: Shadow Dancer (Ninja)
- **Reqs**: `dex: 4`, `mobility: 2`, `dark: 1`
- **Playstyle**: Teleporting assassin, high mobility.
- **The Catch**: You cannot get `mobility: 2` easily with just Tier 1 blessings.
- **The Path**:
    1. Become **Rogue**.
    2. Use Rogue status to buy **Shadow Step** (Tier 2) and **Vault** (Tier 3).
    3. Equip them to gain the `mobility` tags.
    4. System recognizes **Shadow Dancer** identity.
    5. **Shadow Dancer** identity allows buying **Assassinate** (Tier 4 Ultimate).

---

### Dancer (ID: `dancer`)
**Description**: A rhythmic combatant who combines offensive buffs with disruptive effects.
**Playstyle**: Fluid / Rhythm / Buffs
**Kingdom**: Light / Instinct (Dex-based)

#### 1. Identity Requirements
- **Primary**: `dex` (Count: 3)
- **Secondary**: `mobility` (Count: 2)
- **Tertiary**: `buff` (Count: 1)

#### 2. Key Blessings (The Enablers)
| Blessing Name | Tier | Tags | Deity |
|---------------|------|------|-------|
| *Quick Step* | 1 | `mobility`, `dex` | Celeris |
| *Tiger Stance* | 2 | `stance`, `buff` | Feral |
| *Evasive Step* | 1 | `mobility`, `dex` | Celeris |

---

### Death Knight (ID: `death_knight`)
**Description**: A hybrid tank and dark caster who drains life to sustain in combat.
**Playstyle**: Sustain Tank / Lifesteal
**Kingdom**: Dark (Con/Str-based)

#### 1. Identity Requirements
- **Primary**: `dark` (Count: 3)
- **Secondary**: `protection` (Count: 2)
- **Tertiary**: `leech` (Count: 1)

#### 2. Key Blessings (The Enablers)
| Blessing Name | Tier | Tags | Deity |
|---------------|------|------|-------|
| *Siphon* | 2 | `dark`, `siphon` | Blight |
| *Hunger* | 2 | `dark`, `leech` | Blight |
| *Unholy Armor* | 3 | `dark`, `protection` | Blight |

---

### Defiler (ID: `defiler`)
**Description**: A master of curses and afflictions who wins through attrition.
**Playstyle**: Attrition / Debuffs
**Kingdom**: Dark (Int/Wis-based)

#### 1. Identity Requirements
- **Primary**: `dark` (Count: 3)
- **Secondary**: `curse` (Count: 2)
- **Tertiary**: `debuff` (Count: 1)

#### 2. Key Blessings (The Enablers)
| Blessing Name | Tier | Tags | Deity |
|---------------|------|------|-------|
| *Curse* | 2 | `dark`, `curse` | Umbra |
| *Corrosive Vial* | 2 | `debuff`, `acid` | Vex |
| *Miasma* | 2 | `dark`, `dot` | Vex |

---

### Dragoon (ID: `dragoon`)
**Description**: A highly mobile warrior who excels in vertical movement and multi-target attacks.
**Playstyle**: High-mobility / Aerial
**Kingdom**: Instinct / Light (Dex/Str-based)

#### 1. Identity Requirements
- **Primary**: `mobility` (Count: 3)
- **Secondary**: `martial` (Count: 2)

#### 2. Key Blessings (The Enablers)
| Blessing Name | Tier | Tags | Deity |
|---------------|------|------|-------|
| *Vault* | 3 | `mobility`, `vault` | Feral |
| *Dragon Dive* | 4 | `ultimate`, `skill` | Nox |

---

### Engineer (ID: `engineer`)
**Description**: A mid-range battlefield manipulator focused on building deployables.
**Playstyle**: Reactive / Traps / Area Control
**Kingdom**: Light (Int-based)

#### 1. Identity Requirements
- **Primary**: `int` (Count: 3)
- **Secondary**: `gadget` (Count: 2)

#### 2. Key Blessings (The Enablers)
| Blessing Name | Tier | Tags | Deity |
|---------------|------|------|-------|
| *Deploy Turret* | 2 | `gadget`, `summon` | Lumos |
| *Blast Mine* | 2 | `gadget`, `trap` | Vex |

---

### Gambler (ID: `gambler`)
**Description**: Thrives on risk and reward, using dice rolls to create unexpected advantages.
**Playstyle**: High-risk / High-reward / RNG
**Kingdom**: Dark / Light (Luk-based)

#### 1. Identity Requirements
- **Primary**: `luk` (Count: 4)
- **Secondary**: `chance` (Count: 2)

#### 2. Key Blessings (The Enablers)
| Blessing Name | Tier | Tags | Deity |
|---------------|------|------|-------|
| *Roll the Bones* | 1 | `chance`, `buff` | Fortuna |
| *Jackpot* | 4 | `ultimate`, `chance` | Fortuna |

---

### Gunner (ID: `gunner`)
**Description**: A pure ranged damage dealer using different shot types.
**Playstyle**: Long-range / Burst / Reload
**Kingdom**: Instinct (Dex-based)

#### 1. Identity Requirements
- **Primary**: `dex` (Count: 3)
- **Secondary**: `firearm` (Count: 2)

#### 2. Key Blessings (The Enablers)
| Blessing Name | Tier | Tags | Deity |
|---------------|------|------|-------|
| *Snipe* | 2 | `marksmanship`, `lethal` | Raven |
| *Explosive Round* | 2 | `firearm`, `aoe` | Raven |

---

### Hunter (ID: `hunter`)
**Description**: A hybrid combatant excelling in tracking, ranged combat, and taming beasts.
**Playstyle**: Versatile / Ambush / Mobility
**Kingdom**: Instinct (Dex/Wis-based)

#### 1. Identity Requirements
- **Primary**: `instinct` (Count: 3)
- **Secondary**: `tracking` (Count: 1)
- **Tertiary**: `beast` (Count: 1)

#### 2. Key Blessings (The Enablers)
| Blessing Name | Tier | Tags | Deity |
|---------------|------|------|-------|
| *Track* | 2 | `tracking`, `scout` | Feral |
| *Tame* | 2 | `tame`, `instinct` | Sylva |

---

### Illusionist (ID: `illusionist`)
**Description**: Deceives enemies by creating clones and distorting movement.
**Playstyle**: Tactical Disruption / Deception
**Kingdom**: Dark (Int-based)

#### 1. Identity Requirements
- **Primary**: `int` (Count: 3)
- **Secondary**: `illusion` (Count: 2)

#### 2. Key Blessings (The Enablers)
| Blessing Name | Tier | Tags | Deity |
|---------------|------|------|-------|
| *Mirror Image* | 2 | `illusion`, `defense` | Jinx |
| *Phantasm* | 3 | `illusion`, `control` | Jinx |

---

### Machinist (ID: `machinist`)
**Description**: Excels at long-term battlefield management through autonomous drones.
**Playstyle**: Strategic / Drone Management
**Kingdom**: Light (Int-based)

#### 1. Identity Requirements
- **Primary**: `int` (Count: 4)
- **Secondary**: `drone` (Count: 2)

#### 2. Key Blessings (The Enablers)
| Blessing Name | Tier | Tags | Deity |
|---------------|------|------|-------|
| *Deploy Drone* | 2 | `drone`, `summon` | Lumos |
| *Overclock* | 3 | `drone`, `buff` | Lumos |

---

### Mage (ID: `mage`)
**Description**: The Lord of Magic's disciple, wielding Fire, Ice, and Lightning.
**Playstyle**: High-damage / Elemental Versatility / Mobility
**Kingdom**: Light (Int-based)

#### 1. Identity Requirements
- **Primary**: `int` (Count: 3)
- **Secondary**: `elemental` (Count: 1)

#### 2. Key Blessings (The Enablers)
| Blessing Name | Tier | Tags | Deity |
|---------------|------|------|-------|
| *Fireball* | 1 | `elemental`, `fire` | Aldildod |
| *Arcane Blink* | 2 | `mobility`, `arcane` | Aldildod |
| *Meteor Swarm* | 3 | `elemental`, `fire` | Aldildod |
| *Reality Fracture* | 4 | `ultimate`, `arcane` | Aldildod |

---

### Ninja (ID: `ninja`)
**Description**: A fast-moving skirmisher specializing in precision strikes and agility.
**Playstyle**: Speed / Hit-and-Run / Precision
**Kingdom**: Dark (Dex-based)

#### 1. Identity Requirements
- **Primary**: `dex` (Count: 4)
- **Secondary**: `ninjutsu` (Count: 2)

#### 2. Key Blessings (The Enablers)
| Blessing Name | Tier | Tags | Deity |
|---------------|------|------|-------|
| *Shuriken Toss* | 1 | `ninjutsu`, `ranged` | Nox |
| *Shadow Step* | 2 | `mobility`, `dark` | Nox |

---

### Paladin (ID: `paladin`)
**Description**: A champion of Civilization who protects allies and smites evil.
**Playstyle**: Defensive Tank / Support / Heavy Hitter
**Kingdom**: Light (Str-based)

#### 1. Identity Requirements
- **Primary**: `light` (Count: 3)
- **Secondary**: `martial` (Count: 1)
- **Tertiary**: `protection` (Count: 1)

#### 2. Key Blessings (The Enablers)
| Blessing Name | Tier | Tags | Deity |
|---------------|------|------|-------|
| *Divine Smite* | 1 | `martial`, `light` | Pyraz |
| *Holy Shield* | 1 | `protection`, `light` | Pyraz |
| *Lay on Hands* | 2 | `healing`, `light` | Pyraz |
| *Divine Wrath* | 4 | `ultimate`, `light` | Pyraz |

---




---

### Priest (ID: `priest`)
**Description**: The strongest raw healer, using divine magic to restore HP.
**Playstyle**: Pure Support / Healing
**Kingdom**: Light (Wis-based)

#### 1. Identity Requirements
- **Primary**: `wis` (Count: 4)
- **Secondary**: `healing` (Count: 3)

#### 2. Key Blessings (The Enablers)
| Blessing Name | Tier | Tags | Deity |
|---------------|------|------|-------|
| *Cure Light* | 2 | `healing`, `light` | Sophia |
| *Resurrection* | 4 | `ultimate`, `healing` | Sophia |

---

### Samurai (ID: `samurai`)
**Description**: Precision-based melee warrior with spirit-infused sword techniques.
**Playstyle**: High-skill / Timing / Counter
**Kingdom**: Instinct (Str/Dex-based)

#### 1. Identity Requirements
- **Primary**: `str` (Count: 3)
- **Secondary**: `dex` (Count: 2)
- **Tertiary**: `spirit` (Count: 1)

#### 2. Key Blessings (The Enablers)
| Blessing Name | Tier | Tags | Deity |
|---------------|------|------|-------|
| *Iaido* | 2 | `martial`, `spirit` | Krog |
| *Spirit Blade* | 3 | `spirit`, `buff` | Krog |

---

### Soldier (ID: `soldier`)
**Description**: Tactically trained infantry excelling at weapon adaptability.
**Playstyle**: Well-rounded / Fundamentals
**Kingdom**: Light (Str/Dex-based)

#### 1. Identity Requirements
- **Primary**: `str` (Count: 2)
- **Secondary**: `dex` (Count: 2)
- **Tertiary**: `tactics` (Count: 1)

#### 2. Key Blessings (The Enablers)
| Blessing Name | Tier | Tags | Deity |
|---------------|------|------|-------|
| *Shield Bash* | 1 | `martial`, `shield` | Solas |
| *Tactical Strike* | 2 | `martial`, `tactics` | Solas |

---

### Sorcerer (ID: `sorcerer`)
**Description**: A conduit of raw magic who fuels spells with life force when mental reserves fail.
**Playstyle**: High Frequency / Blood Magic / Overcast
**Kingdom**: Instinct (Int/Con-based)

#### 1. Identity Requirements
- **Primary**: `int` (Count: 4)
- **Secondary**: `innate` (Count: 2)

#### 2. Key Blessings (The Enablers)
| Blessing Name | Tier | Tags | Deity |
|---------------|------|------|-------|
| *Inner Fire* | 1 | `innate`, `buff` | Sylva |
| *Wild Surge* | 2 | `innate`, `chaos` | Krog |
| *Chaos Bolt* | 4 | `ultimate`, `destruction` | Krog |

---

### Summoner (ID: `summoner`)
**Description**: Controls powerful but costly legendary creatures.
**Playstyle**: Slow / High-Impact Summons
**Kingdom**: Dark / Instinct (Int-based)

#### 1. Identity Requirements
- **Primary**: `int` (Count: 4)
- **Secondary**: `summon` (Count: 3)

#### 2. Key Blessings (The Enablers)
| Blessing Name | Tier | Tags | Deity |
|---------------|------|------|-------|
| *Summon Ifrit* | 3 | `summon`, `fire` | Vex |
| *Grand Summon* | 4 | `ultimate`, `summon` | Vex |


# Class Design Reference

## Philosophy
In Godless, **Classes do not exist** as rigid containers. They are **Identities** recognized by the world when a player's soul (Blessing Deck) resonates with a specific frequency (Tags).

To "build" a class, we define:
1. **The Identity**: What tags are required?
2. **The Enablers**: Which blessings provide these tags?
3. **The Payoff**: What bonuses or exclusive Tier 4 abilities does this identity unlock?

---

## Class Definition Template

### [Class Name] (ID: `class_id`)
**Description**: Flavor text describing the class.
**Playstyle**: A short summary of how it plays (e.g., "High Burst, Low Defense").

#### 1. Identity Requirements
The specific combination of tags needed to trigger this class.
- **Primary Tag**: `tag_name` (Count: X)
- **Secondary Tag**: `tag_name` (Count: Y)

#### 2. Prestige Path (Unlock Logic)
*How does a player become this class?*
- **Basic Class**: Achievable via Tier 1/2 blessings available to everyone.
- **Prestige Class**: Requires specific tags found only on Tier 3/4 blessings.
    - *Constraint*: Tier 4 blessings often require a specific **Active Class** to buy.
    - *Flow*: `Rogue` (Class) -> Buy `Shadow Step` (T3 Blessing) -> Equip it -> Gain `shadow` tag -> Become `Ninja`.

#### 3. Key Blessings (The Enablers)
List the blessings that help form this identity.
| Blessing Name | Tier | Tags Provided | Deity |
|---------------|------|---------------|-------|
| *Kick*        | 1    | `martial`     | None  |
| *Backstab*    | 2    | `martial`, `dark` | Nox |

---

## Example: The Prestige Flow (Rogue -> Ninja)

### Base Class: Rogue
- **Reqs**: `dex: 3`, `rogue: 1`
- **Playstyle**: Evasive, opportunistic damage.
- **Source**: Tier 1/2 blessings from **Nox** and **Raven**.

### Prestige Class: Shadow Dancer (Ninja)
- **Reqs**: `dex: 4`, `mobility: 2`, `dark: 1`
- **Playstyle**: Teleporting assassin, high mobility.
- **The Catch**: You cannot get `mobility: 2` easily with just Tier 1 blessings.
- **The Path**:
    1. Become **Rogue**.
    2. Use Rogue status to buy **Shadow Step** (Tier 2) and **Vault** (Tier 3).
    3. Equip them to gain the `mobility` tags.
    4. System recognizes **Shadow Dancer** identity.
    5. **Shadow Dancer** identity allows buying **Assassinate** (Tier 4 Ultimate).

---

## Current Classes (Summary)

### Kingdom: Light
| Class | Playstyle | Key Tags |
|-------|-----------|----------|
| **Paladin** | Tank / Healer | `light`, `protection`, `martial` |
| **Cleric** | Healer / Caster | `light`, `healing` |
| **Knight** | Mounted / Tank | `mount`, `martial` |

### Kingdom: Dark
| Class | Playstyle | Key Tags |
|-------|-----------|----------|
| **Assassin** | Burst DPS | `dark`, `stealth` |
| **Warlock** | DoT / Drain | `dark`, `spell` |
| **Necromancer** | Summoner | `dark`, `summon` |

### Kingdom: Instinct
| Class | Playstyle | Key Tags |
|-------|-----------|----------|
| **Barbarian** | High HP / DPS | `instinct`, `rage` |
| **Ranger** | Ranged DPS | `instinct`, `marksmanship` |
| **Druid** | Caster / Control | `instinct`, `nature` |

### Prestige / Advanced
| Class | Parent | Playstyle |
|-------|--------|-----------|
| **Shadow Dancer** | Rogue | Mobility / Stealth |
| **Dragoon** | Warrior | Jump Attacks / Mobility |
| **Red Mage** | Mage | Hybrid Light/Dark Magic |

---

*Use this document to plan new classes before adding them to `data/classes.json`.*