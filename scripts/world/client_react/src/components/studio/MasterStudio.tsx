"use client";

import React, { useState, useEffect, useCallback, useRef } from "react";
import axios from "axios";
import {
    Map as MapIcon,
    Database as DatabaseIcon,
    RefreshCw,
    Layers,
    Zap,
    Info,
    Settings,
    Shield,
    Sun,
    Users,
    ChevronRight,
    X,
    Search,
    Compass
} from "lucide-react";
import { clsx } from "clsx";
import { motion, AnimatePresence } from "framer-motion";
import { useStore } from "../../store/useStore";
import { UniversalCanvas } from "./UniversalCanvas";

// --- Constants ---
const WIDTH = 125;
const HEIGHT = 125;

const BIOME_CATEGORIES = {
    Water: ["ocean", "water", "lake", "swamp"],
    Land: ["plains", "grass", "meadow", "desert", "wasteland", "beach"],
    Cold: ["snow", "tundra", "glacier"],
    Peak: ["mountain", "high_mountain", "peak"],
    Life: ["forest", "dense_forest", "hills"],
    Cultus: ["shrine", "monument", "tower", "ruins", "barrows"],
    Polis: ["city", "road", "bridge"],
    Intent: ["dry", "moist", "rise", "sink", "erase"]
};

interface MasterStudioProps {
    initialMode?: 'sculpt' | 'observe';
}

export default function MasterStudio({ initialMode = 'sculpt' }: MasterStudioProps) {
    const { setWorkspace, terrainRegistry, fetchTerrainRegistry } = useStore();
    const fileInputRef = useRef<HTMLInputElement>(null);

    // --- SHARED STATE ---
    const [mode, setMode] = useState<'sculpt' | 'observe'>(initialMode);
    const [viewMode, setViewMode] = useState<"terrain" | "elev" | "moist" | "tide" | "sec">("terrain");
    const [zoom, setZoom] = useState(mode === 'sculpt' ? 10 : 25);
    const [status, setStatus] = useState("V11.0 UNIFIED");
    const [telemetry, setTelemetry] = useState("[ NO DATA ]");
    const [currentZ, setCurrentZ] = useState(0);

    // --- SCULPT STATE ---
    const [grid, setGrid] = useState<string[][]>(Array(HEIGHT).fill(null).map(() => Array(WIDTH).fill("ocean")));
    const [biasElev, setBiasElev] = useState<number[][]>(Array(HEIGHT).fill(null).map(() => Array(WIDTH).fill(0.1)));
    const [biasMoist, setBiasMoist] = useState<number[][]>(Array(HEIGHT).fill(null).map(() => Array(WIDTH).fill(0.1)));
    const [biasVolume, setBiasVolume] = useState<number[][]>(Array(HEIGHT).fill(null).map(() => Array(WIDTH).fill(0.0)));
    const [biasBiomes, setBiasBiomes] = useState<(string | null)[][]>(Array(HEIGHT).fill(null).map(() => Array(WIDTH).fill(null)));
    const [biasRoads, setBiasRoads] = useState<number[][]>(Array(HEIGHT).fill(null).map(() => Array(WIDTH).fill(0)));
    const [biasLandmarks, setBiasLandmarks] = useState<(string | null)[][]>(Array(HEIGHT).fill(null).map(() => Array(WIDTH).fill(null)));
    const [activeTool, setActiveTool] = useState("peak");
    const [brushRadius, setBrushRadius] = useState(4);
    const [weights, setWeights] = useState<Record<string, number>>({
        sea_level: 0.5, aridity: 0.5, peak_intensity: 0.5, mtn_clusters: 0.5, mtn_scale: 0.5,
        moisture_level: 0.5, land_density: 0.6, biome_isolation: 0.5, designer_authority: 0.5,
        seed: Math.floor(Math.random() * 999999)
    });
    const [intents, setIntents] = useState<Record<string, number>>({
        cities: 3, shrines: 5, ruins: 10, road_density: 3, mountain_density: 5, forest_density: 5, swamp_density: 2, water_density: 5
    });
    const [elevMap, setElevMap] = useState<number[][] | undefined>();
    const [moistMap, setMoistMap] = useState<number[][] | undefined>();
    const [targetPrefix, setTargetPrefix] = useState("");
    const [anchorX, setAnchorX] = useState<number | "">("");
    const [anchorY, setAnchorY] = useState<number | "">("");
    const [anchorZ, setAnchorZ] = useState<number | "">("");
    const [isGenerating, setIsGenerating] = useState(false);

    // --- OBSERVE STATE ---
    const [zones, setZones] = useState<string[]>([]);
    const [activeZone, setActiveZone] = useState<string | null>(null);
    const [rooms, setRooms] = useState<any[]>([]);
    const [players, setPlayers] = useState<any[]>([]);
    const [showPlayerList, setShowPlayerList] = useState(false);
    const [selectedRoom, setSelectedRoom] = useState<any | null>(null);
    const [centerRequest, setCenterRequest] = useState<{ x: number, y: number } | null>(null);

    // --- INFLUENCE STATE ---
    const [tideMap, setTideMap] = useState<{ kingdom: string, power: number }[][] | undefined>();
    const [secMap, setSecMap] = useState<number[][] | undefined>();

    // --- INITIALIZATION ---
    useEffect(() => {
        fetchTerrainRegistry();
        if (mode === 'observe') {
            loadZoneList();
            refreshLiveWorld();
        }
    }, [mode, fetchTerrainRegistry]);

    const loadZoneList = async () => {
        try {
            const resp = await axios.get('/api/zones');
            setZones(resp.data.zones);
        } catch (e) { console.error("Zones failed", e); }
    };

    const refreshLiveWorld = async () => {
        try {
            const mapResp = await axios.get('/api/map-data');
            setRooms(mapResp.data.rooms || []);
            const pResp = await axios.get('/api/players');
            setPlayers(pResp.data.players || []);
        } catch (e) { console.error("Live sync failed", e); }
    };

    const calculateInfluence = useCallback(() => {
        const newTide = Array(HEIGHT).fill(null).map(() => Array(WIDTH).fill({ kingdom: "neutral", power: 0 }));
        const newSec = Array(HEIGHT).fill(null).map(() => Array(WIDTH).fill(0));
        const activeShrines: any[] = [];

        // Contextual: Use grid landmarks or live rooms depending on mode
        if (mode === 'sculpt') {
            for (let y = 0; y < HEIGHT; y++) {
                for (let x = 0; x < WIDTH; x++) {
                    const lm = biasLandmarks[y][x];
                    if (lm === "shrine" || lm === "city") {
                        activeShrines.push({ x, y, type: lm, kingdom: (x + y) % 2 === 0 ? "light" : "dark", potency: lm === "city" ? 40 : 25, decay: lm === "city" ? 0.35 : 0.55 });
                    }
                }
            }
        }

        for (let y = 0; y < HEIGHT; y++) {
            for (let x = 0; x < WIDTH; x++) {
                let maxP = 0; let dom = "neutral"; let maxS = 0;
                activeShrines.forEach(s => {
                    const d = Math.sqrt((s.x - x) ** 2 + (s.y - y) ** 2);
                    const p = Math.max(0, s.potency - (d * s.decay));
                    if (p > maxP) { maxP = p; dom = s.kingdom; }
                    const s_val = s.type === "city" ? Math.max(0, 1.0 - (d / 30)) : Math.max(0, 0.7 - (d / 15));
                    if (s_val > maxS) maxS = s_val;
                });
                newTide[y][x] = { kingdom: dom, power: maxP };
                newSec[y][x] = maxS;
            }
        }
        setTideMap(newTide); setSecMap(newSec);
    }, [mode, biasLandmarks]);

    // --- ACTIONS ---
    const generateFull = async (forceRandomSeed = false) => {
        if (!anchorX && anchorX !== 0 || !anchorY && anchorY !== 0) {
            alert("Spatial Anchor Required! Please set X and Y coordinates to materialize the shard.");
            return;
        }
        setIsGenerating(true);
        const finalWeights = { ...weights };
        if (forceRandomSeed) finalWeights.seed = Math.floor(Math.random() * 999999);

        try {
            const resp = await axios.post("/api/world/generate", {
                width: WIDTH, height: HEIGHT, config: finalWeights, intents,
                bias_elev: biasElev, bias_moist: biasMoist, bias_biomes: biasBiomes,
                bias_roads: biasRoads, bias_landmarks: biasLandmarks, bias_volume: biasVolume
            });
            setGrid(resp.data.grid);
            setElevMap(resp.data.elev_map);
            setMoistMap(resp.data.moist_map);
            setStatus(`MANIFESTED S:${resp.data.seed}`);
            calculateInfluence();
        } catch (e) { setStatus("GENERATION FAILED"); }
        finally { setIsGenerating(false); }
    };

    const handlePaint = (gx: number, gy: number) => {
        if (mode === 'sculpt') {
            if ((gx < 0 || gx >= WIDTH || gy < 0 || gy >= HEIGHT)) return;
            const R = brushRadius - 1;
            setGrid(prev => {
                const next = [...prev];
                for (let dy = -R; dy <= R; dy++) {
                    for (let dx = -R; dx <= R; dx++) {
                        const ny = gy + dy, nx = gx + dx;
                        if (ny >= 0 && ny < HEIGHT && nx >= 0 && nx < WIDTH && Math.sqrt(dx * dx + dy * dy) <= R) {
                            if (activeTool === "rise") biasElev[ny][nx] = Math.min(1.0, biasElev[ny][nx] + 0.1);
                            else if (activeTool === "sink") biasElev[ny][nx] = Math.max(0.0, biasElev[ny][nx] - 0.1);
                            else if (activeTool === "moist") biasMoist[ny][nx] = Math.min(1.0, biasMoist[ny][nx] + 0.1);
                            else if (activeTool === "dry") biasMoist[ny][nx] = Math.max(0.0, biasMoist[ny][nx] - 0.1);
                            else if (activeTool === "erase") { biasBiomes[ny][nx] = null; biasLandmarks[ny][nx] = null; }
                            else if (BIOME_CATEGORIES.Polis.includes(activeTool) || BIOME_CATEGORIES.Cultus.includes(activeTool)) {
                                biasLandmarks[ny][nx] = activeTool;
                            } else {
                                biasBiomes[ny][nx] = activeTool;
                                biasVolume[ny][nx] = Math.min(1.0, biasVolume[ny][nx] + 0.2);
                            }
                        }
                    }
                }
                return next;
            });
        }
    };

    const handleSaveRealization = async () => {
        if ((anchorX === "" || anchorY === "")) {
            alert("Spatial Anchor Required for Persistance!");
            return;
        }
        try {
            await axios.post("/api/world/save", {
                grid, prefix: targetPrefix,
                config: { ...weights, anchor_x: anchorX, anchor_y: anchorY, anchor_z: anchorZ || 0 }
            });
            alert("Shard Persisted to Engine.");
        } catch (e) { alert("Persistence Failed."); }
    };

    return (
        <div className="absolute inset-0 bg-slate-950 flex text-white overflow-hidden z-[100] animate-in fade-in duration-700">
            {/* Left Sidebar: Contextual Tools */}
            <aside className="w-20 border-r border-white/5 bg-slate-900/40 backdrop-blur-3xl flex flex-col items-center py-8 gap-8 z-30 shadow-2xl">
                <div className="flex flex-col items-center gap-1">
                    <div className={clsx("h-1 w-8 rounded-full mb-1", mode === 'sculpt' ? "bg-cyan-500 shadow-[0_0_10px_#00bcd4]" : "bg-purple-500 shadow-[0_0_10px_#a855f7]")} />
                </div>

                <div className="flex flex-col gap-4">
                    <button onClick={() => setWorkspace('game')} className="p-3 bg-white/5 rounded-xl text-slate-400 hover:text-white transition-all shadow-inner" title="Quick Jump: Game Client"><Zap size={20} /></button>
                </div>

                <div className="h-px w-10 bg-white/5" />

                <button
                    onClick={() => {
                        const nM = mode === 'sculpt' ? 'observe' : 'sculpt';
                        setMode(nM);
                        setWorkspace(nM === 'sculpt' ? 'editor' : 'studio');
                    }}
                    title="Toggle Workflow: Sculpt vs Observe"
                    className={clsx(
                        "p-4 rounded-2xl transition-all border group",
                        mode === 'sculpt' ? "bg-cyan-500/10 text-cyan-400 border-cyan-500/20" : "bg-purple-500/10 text-purple-400 border-purple-500/20"
                    )}
                >
                    {mode === 'sculpt' ? <Settings size={22} className="group-hover:rotate-45 transition-transform" /> : <MapIcon size={22} />}
                </button>

                <button
                    onClick={() => setShowPlayerList(!showPlayerList)}
                    title="Player Tracker"
                    className={clsx("p-4 rounded-2xl transition-all", showPlayerList ? "bg-purple-500 text-white shadow-lg" : "text-slate-500 hover:bg-white/5")}
                >
                    <Users size={22} />
                </button>

                <button
                    onClick={() => setCenterRequest({ x: WIDTH / 2, y: HEIGHT / 2 })}
                    title="Reset Camera Viewport"
                    className="p-4 rounded-2xl text-slate-500 hover:text-white transition-all hover:bg-white/5"
                >
                    <Compass size={22} />
                </button>

                <div className="mt-auto mb-4">
                    <span className="text-[7px] font-black uppercase tracking-[0.3em] vertical-text opacity-30 italic">{mode} MODE</span>
                </div>
            </aside>

            {/* Main Workspace */}
            <div className="flex-1 flex flex-col bg-[#050505]">
                {/* Unified Header */}
                <header className="h-16 border-b border-white/5 bg-zinc-950/80 backdrop-blur-2xl flex items-center justify-between px-8 shadow-2xl z-20">
                    <div className="flex items-center gap-8">
                        <div className="flex items-center gap-3">
                            <div className={clsx("h-2 w-2 rounded-full animate-pulse", mode === 'sculpt' ? "bg-cyan-500" : "bg-purple-500")} />
                            <span className="text-white text-xl font-black italic uppercase tracking-tighter">
                                Master<span className={mode === 'sculpt' ? "text-cyan-500" : "text-purple-500"}>Studio</span>
                            </span>
                        </div>

                        {/* View Modes */}
                        <div className="flex items-center gap-1 bg-white/5 rounded-full p-1 border border-white/5">
                            {[
                                { id: "terrain", icon: <Layers size={14} />, title: "Topology" },
                                { id: "elev", icon: <Zap size={14} />, title: "Verticality" },
                                { id: "moist", icon: <RefreshCw size={14} />, title: "Climate" },
                                { id: "tide", icon: <Sun size={14} />, title: "Divine Tide" },
                                { id: "sec", icon: <Shield size={14} />, title: "Security Matrix" }
                            ].map(v => (
                                <button
                                    key={v.id}
                                    onClick={() => setViewMode(v.id as any)}
                                    title={v.title}
                                    className={clsx("p-2 rounded-full transition-all", viewMode === v.id ? "bg-white text-black shadow-lg" : "text-zinc-500 hover:text-white")}
                                >
                                    {v.icon}
                                </button>
                            ))}
                        </div>
                    </div>

                    <div className="flex items-center gap-6">
                        {/* Contextual Header Tools */}
                        {mode === 'sculpt' && (
                            <div className="flex items-center gap-3">
                                <div className="flex items-center gap-2 bg-black/40 border border-white/10 rounded-lg px-4 py-2">
                                    <input type="number" value={anchorX} onChange={e => setAnchorX(e.target.value === "" ? "" : parseInt(e.target.value))} placeholder="X" className="bg-transparent text-[10px] font-mono text-cyan-400 w-10 outline-none" />
                                    <input type="number" value={anchorY} onChange={e => setAnchorY(e.target.value === "" ? "" : parseInt(e.target.value))} placeholder="Y" className="bg-transparent text-[10px] font-mono text-cyan-400 w-10 outline-none" />
                                </div>
                                <button onClick={() => generateFull(false)} disabled={isGenerating} className="px-6 py-2 bg-cyan-500 hover:bg-cyan-400 text-black text-[10px] font-black uppercase rounded-lg shadow-xl flex items-center gap-2">
                                    <RefreshCw size={14} className={isGenerating ? "animate-spin" : ""} /> Realize
                                </button>
                                <button onClick={() => generateFull(true)} className="p-2 bg-purple-500/20 text-purple-400 border border-purple-500/20 rounded-lg hover:bg-purple-500/30 transition-all">
                                    <Zap size={16} fill="currentColor" />
                                </button>
                            </div>
                        )}

                        {mode === 'observe' && (
                            <div className="flex items-center gap-4">
                                <button onClick={loadZoneList} className="text-zinc-500 hover:text-white"><RefreshCw size={16} /></button>
                                <div className="px-5 py-2 bg-slate-900 border border-white/5 rounded-lg text-[10px] font-black text-slate-500 flex items-center gap-2 tracking-[0.2em] uppercase">
                                    {activeZone ? activeZone : "LIVE ENGINE STREAM"}
                                </div>
                            </div>
                        )}

                        <div className="h-4 w-px bg-white/10" />
                        <button onClick={handleSaveRealization} className="p-2.5 bg-zinc-800 text-zinc-400 hover:text-white rounded-lg border border-white/5 transition-all">
                            <DatabaseIcon size={16} />
                        </button>
                    </div>
                </header>

                {/* Primary Canvas Area */}
                <main className="flex-1 relative overflow-hidden flex">
                    <div className="flex-1 relative bg-[#0a0a0a]">
                        <UniversalCanvas
                            mode={mode}
                            grid={grid}
                            rooms={rooms.filter(r => r.z === currentZ)}
                            elevMap={elevMap}
                            moistMap={moistMap}
                            tideMap={tideMap}
                            secMap={secMap}
                            viewMode={viewMode}
                            brushRadius={brushRadius}
                            zoom={zoom}
                            onPaint={handlePaint}
                            onPaintEnd={() => mode === 'sculpt' ? null : refreshLiveWorld()}
                            onHover={(x, y) => {
                                const terr = mode === 'sculpt' ? grid[y]?.[x] : rooms.find(r => r.x === x && r.y === y && r.z === currentZ)?.terrain;
                                setTelemetry(`POS: ${x},${y},${currentZ}\nMODE: ${mode.toUpperCase()}\nBIO: ${terr || 'VOID'}`);
                            }}
                            onRightClick={(x, y) => setSelectedRoom({ x, y, z: currentZ })}
                            centerPos={centerRequest}
                        />

                        {/* Telemetry Floating Card */}
                        <div className="absolute top-10 left-10 pointer-events-none p-6 bg-black/80 backdrop-blur-3xl border border-white/5 rounded-3xl shadow-2xl min-w-[200px]">
                            <h4 className="text-cyan-500 text-[9px] font-black uppercase tracking-[0.3em] mb-3 italic flex items-center gap-2">
                                <Info size={12} /> Master Telemetry
                            </h4>
                            <div className="font-mono text-[9px] text-zinc-400 space-y-1 whitespace-pre">
                                {telemetry}
                            </div>
                        </div>
                    </div>

                    {/* Right Toolbar Panel */}
                    <AnimatePresence mode="wait">
                        {mode === 'sculpt' && (
                            <motion.aside key="sculpt" initial={{ x: 400 }} animate={{ x: 0 }} exit={{ x: 400 }} className="w-96 border-l border-white/5 bg-slate-950/50 backdrop-blur-3xl p-8 flex flex-col gap-8 scrollbar-hide overflow-y-auto">
                                <header>
                                    <h3 className="text-[10px] font-black text-cyan-500 uppercase tracking-[0.3em] mb-2 italic">Creator Palette</h3>
                                    <div className="text-3xl font-black italic tracking-tighter uppercase whitespace-nowrap">Universal Brush</div>
                                </header>

                                <div className="flex-1 px-1 custom-scrollbar">
                                    <div className="grid grid-cols-2 gap-2 pb-8">
                                        {Object.entries(BIOME_CATEGORIES).map(([cat, biomes]) => (
                                            <div key={cat} className="col-span-2 mt-4 first:mt-0">
                                                <label className="text-[8px] font-black text-zinc-600 uppercase tracking-[0.2em] mb-2 block">{cat}</label>
                                                <div className="grid grid-cols-2 gap-2">
                                                    {biomes.map(b => (
                                                        <button
                                                            key={b} onClick={() => setActiveTool(b)}
                                                            className={clsx("px-4 py-3 rounded-xl border text-[9px] font-black uppercase transition-all truncate", activeTool === b ? "bg-cyan-500 border-cyan-400 text-black shadow-lg" : "bg-white/5 border-white/5 text-zinc-500 hover:text-white")}
                                                        >
                                                            {b}
                                                        </button>
                                                    ))}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </motion.aside>
                        )}

                        {mode === 'observe' && (
                            <motion.aside key="observe" initial={{ x: 400 }} animate={{ x: 0 }} exit={{ x: 400 }} className="w-96 border-l border-white/5 bg-slate-900/50 backdrop-blur-3xl p-8 flex flex-col gap-8">
                                <header>
                                    <h3 className="text-[10px] font-black text-purple-500 uppercase tracking-[0.3em] mb-2 italic">Shard Monitor</h3>
                                    <div className="text-3xl font-black italic tracking-tighter uppercase">Active Grids</div>
                                </header>
                                <div className="flex-1 overflow-y-auto custom-scrollbar flex flex-col gap-3">
                                    {zones.map(z => (
                                        <button key={z} onClick={() => setActiveZone(z)} className={clsx("w-full p-5 rounded-3xl bg-white/5 border border-white/5 text-left transition-all", activeZone === z ? "border-purple-500/50 bg-purple-500/5" : "hover:bg-white/10")}>
                                            <span className="text-xs font-bold text-white uppercase italic">{z.replace(/_/g, ' ')}</span>
                                        </button>
                                    ))}
                                </div>
                            </motion.aside>
                        )}
                    </AnimatePresence>
                </main>
            </div>

            {/* Player List Overlay */}
            <AnimatePresence>
                {showPlayerList && (
                    <motion.aside initial={{ x: 400 }} animate={{ x: 0 }} exit={{ x: 400 }} className="fixed right-0 top-16 bottom-0 w-80 bg-black/90 backdrop-blur-3xl border-l border-white/10 p-8 z-[200] shadow-[-50px_0_100px_rgba(0,0,0,0.8)]">
                        <div className="mb-8 flex justify-between items-center">
                            <div>
                                <span className="text-purple-500 text-[10px] font-black uppercase tracking-[0.3em] italic">Soul Tracker</span>
                                <h3 className="text-2xl font-black italic uppercase">Mortals</h3>
                            </div>
                            <button onClick={() => setShowPlayerList(false)} className="p-2 text-slate-500 hover:text-white"><X size={20} /></button>
                        </div>
                        <div className="flex flex-col gap-3 overflow-y-auto custom-scrollbar pr-2 h-[80vh]">
                            {players.map(p => (
                                <button key={p.name} onClick={() => setCenterRequest({ x: p.x, y: p.y })} className="p-4 rounded-2xl bg-white/5 border border-white/5 hover:border-purple-500 text-left transition-all group">
                                    <div className="text-sm font-black italic text-white group-hover:text-purple-400 capitalize">{p.name}</div>
                                    <div className="text-[10px] font-mono text-slate-500">POS: {p.x}, {p.y}</div>
                                </button>
                            ))}
                        </div>
                    </motion.aside>
                )}
            </AnimatePresence>
        </div>
    );
}
