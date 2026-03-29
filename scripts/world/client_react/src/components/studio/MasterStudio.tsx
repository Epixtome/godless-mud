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
    Compass,
    Activity,
    Box
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

/**
 * [V11.8] Godless Master Studio: The Unified Monolith
 * A singular viewport for Sculpting (Genesis) & Observation (Mirror).
 */
export default function MasterStudio({ initialMode = 'sculpt' }: MasterStudioProps) {
    const { isAdmin, setWorkspace, terrainRegistry, fetchTerrainRegistry } = useStore();
    const [activeTab, setActiveTab] = useState<'mirror' | 'genesis'>(initialMode === 'observe' ? 'mirror' : 'genesis');
    const [viewMode, setViewMode] = useState<"terrain" | "elev" | "moist" | "tide" | "sec">("terrain");
    const [zoom, setZoom] = useState(25);
    const [telemetry, setTelemetry] = useState("[ LINK ESTABLISHED ]");
    const [currentZ, setCurrentZ] = useState(0);

    // --- Genesis (Sculpt) State ---
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
    const [anchorX, setAnchorX] = useState<number>(0);
    const [anchorY, setAnchorY] = useState<number>(0);
    const [isGenerating, setIsGenerating] = useState(false);

    // --- Mirror (Observe) State ---
    const [zones, setZones] = useState<string[]>([]);
    const [activeZone, setActiveZone] = useState<string | null>(null);
    const [rooms, setRooms] = useState<any[]>([]);
    const [players, setPlayers] = useState<any[]>([]);
    const [showPlayerList, setShowPlayerList] = useState(false);
    const [centerRequest, setCenterRequest] = useState<{ x: number, y: number } | null>(null);

    // --- Effect: Load Initial State ---
    useEffect(() => {
        fetchTerrainRegistry();
        loadZoneList();
        refreshLiveWorld();
    }, [fetchTerrainRegistry]);

    const loadZoneList = async () => {
        try {
            const resp = await axios.get('/api/zones');
            setZones(resp.data.zones || []);
        } catch (e) { console.error("Mirror sync failed", e); }
    };

    const refreshLiveWorld = async () => {
        try {
            const mapResp = await axios.get('/api/map-data');
            setRooms(mapResp.data.rooms || []);
            const pResp = await axios.get('/api/players');
            setPlayers(pResp.data.players || []);
        } catch (e) { console.error("Mirror sync failed", e); }
    };

    const generateFull = async (forceRandomSeed = false) => {
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
            setTelemetry(`GENESIS COMPLETE: Seed ${resp.data.seed}`);
        } catch (e) { setTelemetry("GENESIS FAILED"); }
        finally { setIsGenerating(false); }
    };

    const handlePaint = (gx: number, gy: number) => {
        // Painting relative to genesis anchor
        const localX = gx - anchorX;
        const localY = gy - anchorY;
        if (localX < 0 || localX >= WIDTH || localY < 0 || localY >= HEIGHT) return;

        setGrid(prev => {
            const next = [...prev];
            const R = brushRadius - 1;
            for (let dy = -R; dy <= R; dy++) {
                for (let dx = -R; dx <= R; dx++) {
                    const ny = localY + dy, nx = localX + dx;
                    if (ny >= 0 && ny < HEIGHT && nx >= 0 && nx < WIDTH && Math.sqrt(dx * dx + dy * dy) <= R) {
                        if (activeTool === "rise") biasElev[ny][nx] = Math.min(1.0, biasElev[ny][nx] + 0.1);
                        else if (activeTool === "sink") biasElev[ny][nx] = Math.max(0.0, biasElev[ny][nx] - 0.1);
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
    };

    const handleSaveRealization = async () => {
        try {
            await axios.post("/api/world/save", {
                grid, prefix: activeZone || "custom",
                config: { ...weights, anchor_x: anchorX, anchor_y: anchorY, anchor_z: currentZ }
            });
            setTelemetry("SHARD PERSISTED TO ENGINE");
        } catch (e) { setTelemetry("PERSISTENCE FAILED"); }
    };

    return (
        <div className="absolute inset-0 bg-slate-[#050505] flex text-white overflow-hidden pt-10 font-sans select-none">
            
            {/* LEFT TOOLBAR: Global Controls */}
            {/* LEFT TOOLBAR: Global Intelligence & Portal */}
            <aside className="w-18 border-r border-white/5 bg-slate-950/40 backdrop-blur-3xl flex flex-col items-center py-8 gap-8 z-50 shadow-2xl">
                <div className="flex flex-col items-center gap-1 mb-2">
                   <div className={clsx("h-1 w-8 rounded-full mb-1 shadow-lg shadow-cyan-500/50", activeTab === 'genesis' ? "bg-cyan-500" : "bg-purple-500")} />
                </div>

                <div className="flex flex-col gap-4">
                   <button 
                     onClick={() => setWorkspace('nexus')}
                     className="p-3.5 bg-white/5 rounded-2xl text-slate-400 hover:text-white transition-all shadow-inner border border-white/5 group"
                     title="Spiritual Nexus"
                   >
                     <Zap size={22} className="group-hover:scale-110 group-hover:text-cyan-400 transition-transform" />
                   </button>
                   <button 
                     onClick={() => setCenterRequest({ x: anchorX, y: anchorY })}
                     className="p-3.5 bg-white/5 rounded-2xl text-slate-500 hover:text-white transition-all border border-white/5 group"
                     title="Focus Anchor"
                   >
                     <Compass size={22} className="group-hover:rotate-45 transition-transform" />
                   </button>
                </div>

                <div className="w-8 h-px bg-white/10" />

                <button 
                  onClick={() => setShowPlayerList(!showPlayerList)}
                  className={clsx("p-4 rounded-2xl transition-all border group shadow-lg", showPlayerList ? "bg-purple-500 border-purple-400 text-white shadow-purple-500/20" : "text-slate-500 bg-white/2 border-white/5 hover:bg-white/5")}
                  title="Player Monitor"
                >
                  <Users size={22} className="group-hover:scale-110 transition-transform" />
                </button>
                
                <div className="mt-auto flex flex-col items-center gap-8 opacity-40 hover:opacity-100 transition-opacity">
                   <div className="vertical-text text-[7px] font-black uppercase tracking-[0.4em] text-slate-500 italic rotate-180">Master Control</div>
                   <button className="text-slate-600 hover:text-white transition-colors" title="Engine Settings"><Settings size={18} /></button>
                </div>
            </aside>

            {/* MAIN WORKSPACE: The Unified Viewport */}
            <section className="flex-1 flex flex-col relative bg-black overflow-hidden">
                
                {/* Unified Sub-Header */}
                <div className="h-14 border-b border-white/5 bg-zinc-950/80 backdrop-blur-md flex items-center justify-between px-8 z-40 shrink-0 shadow-lg">
                    <div className="flex items-center gap-6">
                        <div className="flex items-center gap-3">
                           <Activity size={18} className="text-purple-500 animate-pulse" />
                           <h1 className="text-xl font-black uppercase tracking-tighter italic whitespace-nowrap">
                              Master<span className="text-purple-500">Studio</span>
                              <span className="ml-3 px-2 py-0.5 bg-purple-500/10 border border-purple-500/20 rounded text-[7px] text-purple-400 align-middle not-italic tracking-[0.2em] font-black">V11.20</span>
                           </h1>
                        </div>
                        <div className="h-4 w-px bg-white/10" />
                        <div className="flex items-center gap-1 bg-black/40 rounded-full p-0.5 border border-white/5">
                            {["terrain", "elev", "moist", "tide", "sec"].map(v => (
                                <button
                                    key={v}
                                    onClick={() => setViewMode(v as any)}
                                    className={clsx("px-3 py-1.5 rounded-full text-[8px] font-black uppercase transition-all tracking-widest", viewMode === v ? "bg-white text-black shadow-lg" : "text-zinc-500 hover:text-white")}
                                >
                                    {v}
                                </button>
                            ))}
                        </div>
                    </div>

                    <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2 bg-black/60 border border-white/10 rounded-lg px-3 py-1.5 h-8">
                            <span className="text-[8px] font-black text-slate-600 uppercase">Anchor</span>
                            <input type="number" value={anchorX} onChange={e => setAnchorX(parseInt(e.target.value) || 0)} className="bg-transparent text-[10px] font-mono text-cyan-400 w-10 text-center outline-none" placeholder="X" />
                            <input type="number" value={anchorY} onChange={e => setAnchorY(parseInt(e.target.value) || 0)} className="bg-transparent text-[10px] font-mono text-cyan-400 w-10 text-center outline-none" placeholder="Y" />
                        </div>
                        <button 
                          onClick={() => generateFull(false)} 
                          disabled={isGenerating}
                          className="h-8 px-4 bg-purple-600 hover:bg-purple-500 text-white text-[9px] font-black uppercase rounded shadow-lg flex items-center gap-2 transition-all active:scale-95"
                        >
                            <RefreshCw size={12} className={isGenerating ? "animate-spin" : ""} /> Realize Shard
                        </button>
                        <button 
                          onClick={handleSaveRealization}
                          className="h-8 w-8 bg-zinc-800 hover:bg-zinc-700 text-zinc-400 hover:text-white rounded border border-white/5 flex items-center justify-center transition-all"
                        >
                            <DatabaseIcon size={14} />
                        </button>
                    </div>
                </div>

                {/* THE UNIFIED CANVAS */}
                <div className="flex-1 relative bg-slate-950">
                    <UniversalCanvas
                        mode={activeTab === 'genesis' ? 'sculpt' : 'observe'}
                        grid={grid}
                        rooms={rooms.filter(r => r.z === currentZ)}
                        elevMap={elevMap}
                        moistMap={moistMap}
                        viewMode={viewMode}
                        brushRadius={brushRadius}
                        zoom={zoom}
                        onPaint={handlePaint}
                        onPaintEnd={() => refreshLiveWorld()}
                        onHover={(x, y) => {
                            const terr = rooms.find(r => r.x === x && r.y === y && r.z === currentZ)?.terrain || grid[y-anchorY]?.[x-anchorX] || 'VOID';
                            setTelemetry(`COORD: ${x}, ${y}, ${currentZ} | RECOGNITION: ${terr.toUpperCase()}`);
                        }}
                        onRightClick={(x, y) => setCenterRequest({ x, y })}
                        centerPos={centerRequest}
                        anchorX={anchorX}
                        anchorY={anchorY}
                    />

                    {/* Vellum Telemetry Overlay: High-Fidelity Glassmorphism */}
                    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="absolute bottom-10 left-10 p-6 bg-slate-950/80 backdrop-blur-3xl border border-white/10 rounded-3xl shadow-[0_30px_60px_rgba(0,0,0,0.8)] min-w-[280px] pointer-events-none group">
                        <div className="flex items-center justify-between mb-4 pb-2 border-b border-white/5">
                           <div className="flex items-center gap-2 text-cyan-500">
                             <Activity size={14} className="animate-pulse" />
                             <span className="text-[10px] font-black uppercase tracking-[0.4em] italic leading-none">Telemetry Deck</span>
                           </div>
                           <div className="h-1.5 w-1.5 rounded-full bg-cyan-500 shadow-[0_0_8px_#06b6d4] animate-ping" />
                        </div>
                        <div className="font-mono text-[10px] text-zinc-400 leading-relaxed uppercase space-y-2">
                            <div className="flex justify-between border-b border-white/5 pb-1"><span className="text-slate-600">Spatial Anchor</span> <span className="text-cyan-400">{anchorX}, {anchorY}</span></div>
                            <div className="flex justify-between opacity-80"><span className="text-slate-600">Coordinate</span> <span className="text-white">{telemetry.split('|')[0].replace('COORD: ', '')}</span></div>
                            <div className="text-[11px] font-black text-white italic mt-4 tracking-tighter border-t border-white/5 pt-2">
                               {telemetry.split('|')[1]?.replace('RECOGNITION: ', '') || '[ LINKING ]'}
                            </div>
                        </div>
                    </motion.div>
                </div>
            </section>

            {/* RIGHT TOOLBAR: The High-Fidelity Dual-Panel */}
            <aside className="w-96 border-l border-white/5 bg-black/40 backdrop-blur-3xl flex flex-col shrink-0">
                {/* Tab Switcher */}
                <div className="flex border-b border-white/5 bg-zinc-950/40">
                  <button 
                    onClick={() => setActiveTab('mirror')}
                    className={clsx("flex-1 py-5 text-[10px] font-black uppercase tracking-[0.2em] transition-all", activeTab === 'mirror' ? "text-purple-400 border-b-2 border-purple-500 bg-white/5" : "text-slate-500 hover:text-white")}
                  >Mirror Monitor</button>
                  <button 
                    onClick={() => setActiveTab('genesis')}
                    className={clsx("flex-1 py-5 text-[10px] font-black uppercase tracking-[0.2em] transition-all", activeTab === 'genesis' ? "text-cyan-400 border-b-2 border-cyan-500 bg-white/5" : "text-slate-500 hover:text-white")}
                  >Genesis Engine</button>
                </div>

                <div className="flex-1 overflow-y-auto custom-scrollbar p-8">
                   <AnimatePresence mode="wait">
                      {activeTab === 'mirror' && (
                        <motion.div key="mirror" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="space-y-8">
                           <section>
                              <h5 className="text-[9px] font-black text-purple-500 uppercase tracking-widest mb-4 italic">Active Shards</h5>
                              <div className="space-y-2">
                                 {zones.map(z => (
                                    <button 
                                       key={z} 
                                       onClick={() => { setActiveZone(z); refreshLiveWorld(); }}
                                       className={clsx("w-full p-4 rounded-xl bg-white/2 border border-white/5 text-left flex items-center justify-between group hover:border-purple-500/50 transition-all", activeZone === z ? "border-purple-500/50 bg-purple-500/5" : "")}
                                    >
                                       <span className="text-[10px] font-bold text-slate-300 uppercase tracking-tighter">{z.replace(/_/g, ' ')}</span>
                                       <ChevronRight size={12} className="text-slate-600 group-hover:text-purple-400" />
                                    </button>
                                 ))}
                              </div>
                           </section>
                        </motion.div>
                      )}

                      {activeTab === 'genesis' && (
                        <motion.div key="genesis" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="space-y-10 pb-20">
                           {/* Brush Config */}
                           <section>
                              <h5 className="text-[9px] font-black text-cyan-500 uppercase tracking-widest mb-4 italic">Materialization Brush</h5>
                              <div className="space-y-6 mb-8">
                                <div className="space-y-2">
                                    <div className="flex justify-between text-[8px] font-black uppercase tracking-tighter">
                                        <span className="text-zinc-500">Radius</span>
                                        <span className="text-cyan-500">{brushRadius}px</span>
                                    </div>
                                    <input type="range" min="1" max="10" step="1" value={brushRadius} onChange={e => setBrushRadius(parseInt(e.target.value))} className="w-full" />
                                </div>
                              </div>

                              <div className="grid grid-cols-2 gap-2">
                                 {Object.entries(BIOME_CATEGORIES).map(([cat, biomes]) => (
                                    <div key={cat} className="col-span-2 mt-4 first:mt-0">
                                       <span className="text-[8px] font-black text-zinc-700 uppercase mb-2 block tracking-widest">{cat}</span>
                                       <div className="grid grid-cols-2 gap-1.5">
                                          {biomes.map(b => (
                                             <button 
                                               key={b} onClick={() => setActiveTool(b)}
                                               className={clsx("px-3 py-2.5 rounded-lg border text-[9px] font-black uppercase transition-all truncate", activeTool === b ? "bg-cyan-600 border-cyan-400 text-white shadow-lg shadow-cyan-500/20" : "bg-white/2 border-white/5 text-slate-500 hover:text-white")}
                                             >
                                                {b}
                                             </button>
                                          ))}
                                       </div>
                                    </div>
                                 ))}
                              </div>
                           </section>

                           <section className="pt-8 border-t border-white/5">
                              <h5 className="text-[9px] font-black text-cyan-500 uppercase tracking-widest mb-6 italic">Genesis Parameters</h5>
                              <div className="space-y-6">
                                 {Object.entries(weights).map(([k, v]) => (
                                    <div key={k} className="space-y-2">
                                       <div className="flex justify-between text-[8px] font-black uppercase tracking-tighter">
                                          <span className="text-zinc-500">{k.replace(/_/g, ' ')}</span>
                                          <span className="text-cyan-500">{k === 'seed' ? v : v.toFixed(2)}</span>
                                       </div>
                                       {k === 'seed' ? (
                                          <input type="number" value={v} onChange={e => setWeights({...weights, seed: parseInt(e.target.value) || 0})} className="w-full bg-black/40 border border-white/10 rounded-lg p-3 text-[10px] font-mono text-cyan-400 outline-none" />
                                       ) : (
                                          <input type="range" min="0" max="1" step="0.01" value={v} onChange={e => setWeights({...weights, [k]: parseFloat(e.target.value)})} className="w-full" />
                                       )}
                                    </div>
                                 ))}
                              </div>
                           </section>
                        </motion.div>
                      )}
                   </AnimatePresence>
                </div>
            </aside>

            {/* Global Soul Tracker (Left Sidebar Context) */}
            <AnimatePresence>
                {showPlayerList && (
                    <motion.div initial={{ x: 400 }} animate={{ x: 0 }} exit={{ x: 400 }} className="fixed right-0 top-16 bottom-0 w-80 bg-zinc-950/95 backdrop-blur-3xl border-l border-white/10 p-8 z-[200] shadow-2xl">
                        <div className="flex justify-between items-center mb-8">
                           <div>
                              <span className="text-purple-500 text-[10px] font-black uppercase tracking-[0.3em] italic">Soul Monitor</span>
                              <h4 className="text-2xl font-black italic uppercase">Active Divine</h4>
                           </div>
                           <button onClick={() => setShowPlayerList(false)} className="text-slate-500 hover:text-white"><X size={20} /></button>
                        </div>
                        <div className="space-y-3 h-[75vh] overflow-y-auto custom-scrollbar pr-2">
                           {players.map(p => (
                              <button key={p.name} onClick={() => setCenterRequest({ x: p.x, y: p.y })} className="w-full p-4 rounded-2xl bg-white/2 border border-white/5 hover:border-purple-500 text-left transition-all group">
                                 <div className="text-sm font-black italic text-white group-hover:text-purple-400 capitalize">{p.name}</div>
                                 <div className="text-[10px] font-mono text-zinc-600 mt-1 uppercase">Coordinate: {p.x}, {p.y}</div>
                              </button>
                           ))}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}
