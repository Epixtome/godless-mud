from utilities.colors import Colors

# --- Configuration ---
CHUNK_W = 20
CHUNK_H = 20
SEED = None

# Terrain Types
T_DEEP_WATER = "deep_water"
T_WATER = "water"
T_LAND = "plains"
T_HILLS = "hills"
T_LAKE_DEEP = "lake_deep"
T_MOUNTAIN = "mountain"
T_PEAK = "peak"
T_FOREST = "forest"
T_SWAMP = "swamp"
T_DESERT = "desert"
T_WASTELAND = "wasteland"
T_SNOW = "ice"
T_ROAD = "road"
T_RAIL = "rail"
T_BRIDGE = "bridge"
T_CITY = "road"
T_WALL = "wall"
T_GATE = "gate"
T_SHOP = "shop"
T_PLAZA = "plaza"
T_RUIN = "ruins"
T_CAMP = "plains"
T_VILLAGE_CENTER = "village_center"
T_VILLAGE_HOUSE = "village_house"

# Terrain that generates rooms but blocks movement (Visual Barriers)
BLOCKING_TERRAIN = {T_PEAK, T_WALL, T_DEEP_WATER}
# Terrain that does NOT generate rooms (Void)
VOID_TERRAIN = set() # Generate everything to avoid map holes
NON_TRAVERSABLE = BLOCKING_TERRAIN | VOID_TERRAIN

# Visuals
SYMBOLS = {
    T_DEEP_WATER: f"{Colors.BLUE}@{Colors.RESET}",
    T_WATER: f"{Colors.BLUE}~{Colors.RESET}",
    T_LAKE_DEEP: f"{Colors.BLUE}@{Colors.RESET}",
    T_LAND: f"{Colors.GREEN}.{Colors.RESET}",
    T_HILLS: f"{Colors.GREEN}n{Colors.RESET}",
    T_FOREST: f"{Colors.GREEN}^{Colors.RESET}",
    T_SWAMP: f"{Colors.MAGENTA}%{Colors.RESET}",
    T_MOUNTAIN: f"{Colors.YELLOW}^{Colors.RESET}",
    T_PEAK: f"{Colors.BOLD}{Colors.WHITE}^{Colors.RESET}",
    T_DESERT: f"{Colors.YELLOW}:{Colors.RESET}",
    T_WASTELAND: f"{Colors.RED}:{Colors.RESET}",
    T_SNOW: f"{Colors.CYAN}.{Colors.RESET}",
    T_ROAD: f"{Colors.YELLOW}+{Colors.RESET}",
    T_RAIL: f"{Colors.BOLD}{Colors.WHITE}#{Colors.RESET}",
    T_BRIDGE: f"{Colors.BOLD}{Colors.YELLOW}={Colors.RESET}",
    T_WALL: f"{Colors.BOLD}{Colors.WHITE}#{Colors.RESET}",
    T_GATE: f"{Colors.BOLD}{Colors.YELLOW}+{Colors.RESET}",
    T_SHOP: f"{Colors.GREEN}${Colors.RESET}",
    T_PLAZA: f"{Colors.BOLD}{Colors.WHITE}O{Colors.RESET}",
    T_RUIN: f"{Colors.RED}X{Colors.RESET}",
    T_CITY: f"{Colors.WHITE}O{Colors.RESET}",
    T_VILLAGE_CENTER: f"{Colors.BOLD}{Colors.WHITE}O{Colors.RESET}",
    T_VILLAGE_HOUSE: f"{Colors.WHITE}n{Colors.RESET}",
    T_CAMP: f"{Colors.YELLOW}^{Colors.RESET}"
}

ZONE_NAMES = {
    T_LAND: "The Great Plains",
    T_HILLS: "The Highlands",
    T_FOREST: "The Elder Woods",
    T_SWAMP: "The Black Morass",
    T_MOUNTAIN: "The Stone Peaks",
    T_PEAK: "The High Summits",
    T_DESERT: "The Sunscorched Wastes",
    T_WASTELAND: "The Ashen Wastes",
    T_SNOW: "The Frozen Tundra",
    T_WATER: "The Endless Sea",
    T_DEEP_WATER: "The Abyssal Depths",
    T_RUIN: "Ancient Ruins"
}

DESCRIPTIONS = {
    T_WATER: ["The dark water ripples silently.", "Murky water extends in all directions."],
    T_DEEP_WATER: ["The water here is dangerously deep.", "Large waves crash against each other."],
    T_LAKE_DEEP: ["The water is incredibly deep and cold.", "You cannot see the bottom.", "The water is still and ominous."],
    T_LAND: ["Tall grass waves in the wind.", "The plains stretch out to the horizon."],
    T_HILLS: ["Rolling hills stretch out before you.", "The terrain is uneven and rocky."],
    T_FOREST: ["Tall trees block out most of the light.", "The air smells of pine and damp earth."],
    T_SWAMP: ["The ground squelches beneath your feet.", "Insects buzz in the humid air."],
    T_MOUNTAIN: ["Jagged peaks pierce the sky.", "The air is thin and cold here."],
    T_PEAK: ["You stand atop the world.", "The wind howls violently at this altitude.", "Snow clings to the jagged rock."],
    T_DESERT: ["Endless dunes of golden sand.", "The heat is oppressive."],
    T_WASTELAND: ["The ground is cracked and hot.", "Ash falls from the sky.", "Rivers of magma flow nearby."],
    T_SNOW: ["A blanket of white snow covers everything.", "The cold bites at your exposed skin."],
    T_CITY: ["The bustle of the city surrounds you.", "Paved streets line the orderly buildings."],
    T_ROAD: ["A well-traveled dirt road.", "Wagon ruts cut deep into the path."],
    T_BRIDGE: ["A sturdy wooden bridge spans the water.", "The bridge creaks slightly in the wind."],
    T_RAIL: ["Iron tracks stretch into the distance.", "The gravel ballast crunches underfoot."],
    T_VILLAGE_CENTER: ["A quaint village square with a stone well.", "Villagers gather here."],
    T_VILLAGE_HOUSE: ["A cozy cottage with a thatched roof.", "Smoke rises from the chimney."],
    T_RUIN: ["Crumbling stone walls are all that remain.", "Nature is reclaiming this ancient structure."],
    T_CAMP: ["A small campfire smolders in the center.", "Travelers rest here for the night."],
    T_WALL: ["A massive stone wall blocks the way.", "Fortified ramparts loom above you."],
    T_GATE: ["A heavy iron gate stands open.", "The gateway to the city is bustling."],
    T_SHOP: ["A busy shop filled with wares.", "Merchants shout their prices."],
    T_PLAZA: ["The grand central plaza of the capital.", "A massive fountain flows in the center."]
}

BIOME_MOBS = {
    T_FOREST: [("wolf", 0.08), ("bear", 0.04), ("bandit", 0.05)],
    T_SWAMP: [("slime", 0.08), ("leech", 0.08), ("witch", 0.02)],
    T_DESERT: [("scorpion", 0.08), ("sand_worm", 0.03)],
    T_WASTELAND: [("shadow_stalker", 0.08), ("skeleton", 0.08), ("fire_elemental", 0.05)],
    T_SNOW: [("yeti", 0.03), ("ice_wolf", 0.08)],
    T_LAND: [("wild_boar", 0.08), ("goblin", 0.05)],
    T_RUIN: [("skeleton", 0.15), ("ghost", 0.05)],
    T_ROAD: [("bandit", 0.02), ("traveler", 0.02)]
}

BIOME_ITEMS = {
    T_FOREST: [("wild_berry", 0.10), ("wood", 0.10)],
    T_SWAMP: [("swamp_root", 0.10), ("elderberry", 0.05)],
    T_DESERT: [("cactus_fruit", 0.10)],
    T_WASTELAND: [("rusty_coin", 0.10), ("void_essence", 0.05)],
    T_SNOW: [("ice_shard", 0.05)],
    T_LAND: [("wild_berry", 0.05)],
    T_RUIN: [("rusty_coin", 0.15), ("cloth", 0.10)],
    T_ROAD: [("rusty_coin", 0.05)]
}
