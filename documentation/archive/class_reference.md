> [!CAUTION]
> **LEGACY ARCHITECTURE**: This document reflects Godless MUD v2.x architecture (Pre-Feb 14, 2026 Reset). **Do not use for implementation.** Reference ARCHITECTURE.md for current V3.1+ standards.

# CLASS REFERENCE

### Philosophy
Classes are **Identities** recognized when a player's Blessing Deck resonates with specific Tags.

### 1. Class Definitions

#### **Warrior** (Base)
*   **Role**: Frontline Fighter
*   **Requirements**: `[martial]: 3`, `[weapon]: 2`
*   **Key Blessings**: Kick, Bash, Parry, Sunder, Pommel Strike.

#### **Mage** (Base)
*   **Role**: Arcane Caster
*   **Requirements**: `[spell]: 3`, `[int]: 3`
*   **Key Blessings**: Fireball, Magic Missile, Mana Shield, Arcane Blink.

#### **Rogue** (Base)
*   **Role**: Skirmisher
*   **Requirements**: `[dex]: 3`, `[stealth]: 1`
*   **Key Blessings**: Backstab, Hide, Gouge, Quick Step.

#### **Cleric** (Base)
*   **Role**: Healer
*   **Requirements**: `[light]: 3`, `[healing]: 2`
*   **Key Blessings**: Cure Light, Bless, Purify, Sanctuary.

#### **Ranger** (Base)
*   **Role**: Hunter / Tracker
*   **Requirements**: `[instinct]: 3`, `[marksmanship]: 2`
*   **Key Blessings**: Track, Snipe, Volley, Camouflage.

---

### 2. Advanced Classes (Kingdom Specific)

#### **Paladin** (Light)
*   **Role**: Holy Tank
*   **Requirements**: `[light]: 3`, `[protection]: 2`
*   **Key Blessings**: Divine Smite, Holy Shield, Lay on Hands (T2).

#### **Knight** (Light)
*   **Role**: Mounted Combatant
*   **Requirements**: `[light]: 2`, `[mount]: 1`, `[martial]: 2`
*   **Key Blessings**: Mount, Charge, Trample, Joust.

#### **Bard** (Light/Instinct)
*   **Role**: Buffer / Support
*   **Requirements**: `[song]: 2`, `[support]: 2`
*   **Key Blessings**: Song of Courage, Lullaby, Anthem of War.

#### **Assassin** (Dark)
*   **Role**: Burst DPS
*   **Requirements**: `[dark]: 3`, `[lethal]: 2`
*   **Key Blessings**: Assassinate, Poison Weapon, Garrote.

#### **Necromancer** (Dark)
*   **Role**: Summoner
*   **Requirements**: `[dark]: 3`, `[summon]: 2`
*   **Key Blessings**: Raise Dead, Bone Spear, Life Tap.

#### **Warlock** (Dark)
*   **Role**: Debuffer / Drain
*   **Requirements**: `[dark]: 3`, `[curse]: 2`
*   **Key Blessings**: Curse, Hex, Drain Life, Fear.

#### **Witch** (Dark)
*   **Role**: Thorns / Control
*   **Requirements**: `[dark]: 3`, `[malediction]: 1`
*   **Key Blessings**: Malediction, Hex, Curse.

#### **Barbarian** (Instinct)
*   **Role**: Momentum / Control
*   **Requirements**: `[instinct]: 3`, `[momentum]: 2`
*   **Key Blessings**: Whirlwind, Drag, Second Attack, Stomp.

#### **Druid** (Instinct)
*   **Role**: Nature Caster
*   **Requirements**: `[instinct]: 3`, `[nature]: 2`
*   **Key Blessings**: Entangle, Regrowth, Lightning Call, Shapeshift.

#### **Monk** (Instinct)
*   **Role**: Unarmed Fighter
*   **Requirements**: `[martial]: 3`, `[unarmed]: 2`
*   **Key Blessings**: Tiger Palm, Blackout Kick, Tiger Stance, Meditate.

---

### 3. Prestige Classes (Specialized)

#### **Samurai**
*   **Concept**: Precision striker using "Iaido".
*   **Requirements**: `[blade]: 3`, `[focus]: 2`
*   **Key Blessings**: Iaido (Sheathe), Draw Slash, Third Eye, Meditate.

#### **Ninja**
*   **Concept**: Mobility and stealth skirmisher.
*   **Requirements**: `[ninjutsu]: 2`, `[mobility]: 2`
*   **Key Blessings**: Shuriken Toss, Shadow Step, Smoke Bomb, Vanish.

#### **Dragoon**
*   **Concept**: Aerial assaults.
*   **Requirements**: `[mobility]: 3`, `[polearm]: 1`
*   **Key Blessings**: Jump, Dragon Dive, High Jump.

#### **Alchemist**
*   **Concept**: Item-based caster.
*   **Requirements**: `[alchemy]: 3`, `[utility]: 1`
*   **Key Blessings**: Flask Toss, Transmute, Brew Potion.

#### **Engineer**
*   **Concept**: Construct builder.
*   **Requirements**: `[gadget]: 2`, `[int]: 3`
*   **Key Blessings**: Deploy Turret, Repair, Blast Mine.

#### **Gambler**
*   **Concept**: RNG manipulation.
*   **Requirements**: `[luck]: 3`, `[chance]: 2`
*   **Key Blessings**: Coin Toss, Roll Dice, Jackpot.

#### **Red Mage**
*   **Concept**: Hybrid Caster.
*   **Requirements**: `[light]: 2`, `[dark]: 2`
*   **Key Blessings**: Dualcast, Verfire, Verstone.

#### **Blue Mage**
*   **Concept**: Monster Skill Learner.
*   **Requirements**: `[mimic]: 2`, `[int]: 3`
*   **Key Blessings**: Observe, Absorb, Monster Skill (Learned).