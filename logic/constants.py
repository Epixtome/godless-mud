class Tags:
    # --- UTS 2.0 VOCABULARY (The 22 Words) ---
    # Sources
    MARTIAL = "martial"
    MAGIC = "magic"
    INSTINCT = "instinct"
    HOLY = "holy"
    DARK = "dark"

    # Actions
    STRIKE = "strike"
    AOE = "aoe"
    PROJECTION = "projection"
    RESTORATION = "restoration"
    PROTECTION = "protection"
    DISRUPTION = "disruption"
    UTILITY = "utility"

    # Flavors
    FIRE = "fire"
    ICE = "ice"
    LIGHTNING = "lightning"
    TOXIC = "toxic"
    SLASHING = "slashing"
    BLUNT = "blunt"
    PIERCING = "piercing"
    LETHAL = "lethal"
    WEIGHT = "weight"
    SPEED = "speed"

    # --- RESOURCES ---
    CONCENTRATION = "concentration"
    HEAT = "heat"
    CHI = "chi"
    HP = "hp"

    # --- LEGACY / SYSTEM TAGS ---
    # These exist in the codebase but are not part of the strict UTS vocabulary.
    ARCANE = "arcane"
    HEALING = "healing"
    BUFF = "buff"
    STANCE = "stance"
    MAGIC_DEF = "magic_def"
    PASSIVE = "passive"
    LIGHT = "light"
    DEX = "dex"
    AGILITY = "agility"
    MOVEMENT = "movement"
    HEAVY = "heavy"
    CONCUSSIVE = "concussive"
    SWIFT = "swift"
    ELEMENTAL = "elemental"
    SORCERY = "sorcery"

    # --- VALIDATION SET ---
    VALID_UTS_TAGS = {
        MARTIAL, MAGIC, INSTINCT, HOLY, DARK,
        STRIKE, AOE, PROJECTION, RESTORATION, PROTECTION, DISRUPTION, UTILITY,
        FIRE, ICE, LIGHTNING, TOXIC, SLASHING, BLUNT, PIERCING, LETHAL, WEIGHT, SPEED
    }
