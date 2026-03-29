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
    Swords,
    Sun
} from "lucide-react";
import { SculptorCanvas } from "./sculptor/SculptorCanvas";
import { SculptorPalette } from "./sculptor/SculptorPalette";
import { SculptorTuningDeck } from "./sculptor/SculptorTuningDeck";
import { useStore } from "../../store/useStore";
import { clsx } from "clsx";

// Standard biome colors from architect_data.py
const COLOR_MAP: Record<string, string> = {
    ocean: "#000044", water: "#0066cc", lake: "#004499",
    plains: "#228B22", grass: "#32CD32", meadow: "#7CFC00",
    mountain: "#808080", mountain_shadow: "#424242", high_mountain: "#A9A9A9",
    peak: "#FFFFFF", peak_shadow: "#A9A9A9", forest: "#006400",
    dense_forest: "#004d00", dense_forest_core: "#002b00", swamp: "#2f4f4f",
    desert: "#edc9af", wasteland: "#3e2723", city: "#ffd700",
    shrine: "#ff00ff", docks: "#795548", road: "#555555",
    cobblestone: "#777777", bridge: "#9e9e9e", beach: "#f5deb3",
    dirt_road: "#8b4513", ruins: "#424242", barrows: "#37474f",
    monument: "#00bcd4", tower: "#d32f2f", snow: "#f0f0f0",
    tundra: "#8d99ae", cliffs: "#4a4a4a", glacier: "#afeeee"
};

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

const WIDTH = 125;
const HEIGHT = 125;

export default function EditorWorkspace() {
    const { setWorkspace, terrainRegistry } = useStore();
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [grid, setGrid] = useState<string[][]>(Array(HEIGHT).fill(null).map(() => Array(WIDTH).fill("ocean")));
    const [biasElev, setBiasElev] = useState<number[][]>(Array(HEIGHT).fill(null).map(() => Array(WIDTH).fill(0.1)));
    const [biasMoist, setBiasMoist] = useState<number[][]>(Array(HEIGHT).fill(null).map(() => Array(WIDTH).fill(0.1)));
    const [biasVolume, setBiasVolume] = useState<number[][]>(Array(HEIGHT).fill(null).map(() => Array(WIDTH).fill(0.0)));
    const [biasBiomes, setBiasBiomes] = useState<(string | null)[][]>(Array(HEIGHT).fill(null).map(() => Array(WIDTH).fill(null)));
    const [biasRoads, setBiasRoads] = useState<number[][]>(Array(HEIGHT).fill(null).map(() => Array(WIDTH).fill(0)));
    const [biasLandmarks, setBiasLandmarks] = useState<(string | null)[][]>(Array(HEIGHT).fill(null).map(() => Array(WIDTH).fill(null)));

    const [elevMap, setElevMap] = useState<number[][] | undefined>();
    const [moistMap, setMoistMap] = useState<number[][] | undefined>();
    const [tideMap, setTideMap] = useState<{ kingdom: string, power: number }[][] | undefined>();
    const [secMap, setSecMap] = useState<number[][] | undefined>();

    const [activeTool, setActiveTool] = useState("peak");
    const [isGenerating, setIsGenerating] = useState(false);
    const [targetPrefix, setTargetPrefix] = useState("");
    const [anchorX, setAnchorX] = useState<number | "">("");
    const [anchorY, setAnchorY] = useState<number | "">("");
    const [anchorZ, setAnchorZ] = useState<number | "">("");
    const [zoom, setZoom] = useState(1);
    const [panOffset, setPanOffset] = useState({ x: 0, y: 0 });
    const [isPanning, setIsPanning] = useState(false);
    const [lastPanPos, setLastPanPos] = useState({ x: 0, y: 0 });
    const [brushRadius, setBrushRadius] = useState(4);
    const [viewMode, setViewMode] = useState<"terrain" | "elev" | "moist" | "tide" | "sec">("terrain");

    const [weights, setWeights] = useState<Record<string, number>>({
        sea_level: 0.5, aridity: 0.5, peak_intensity: 0.5, mtn_clusters: 0.5, mtn_scale: 0.5,
        moisture_level: 0.5, land_density: 0.6, biome_isolation: 0.5, designer_authority: 0.5,
        erosion_scale: 0.2, fertility_rate: 1.0, blossom_speed: 1.0, melting_point: 0.0,
        seed: Math.floor(Math.random() * 999999)
    });

    const [intents, setIntents] = useState<Record<string, number>>({
        cities: 3,
        shrines: 5,
        ruins: 10,
        road_density: 3,
        mountain_density: 5,
        forest_density: 5,
        swamp_density: 2,
        water_density: 5
    });

    const [status, setStatus] = useState("V9.0 INTENT-READY");
    const [telemetry, setTelemetry] = useState("[ NO DATA ]");
    const [hoverPos, setHoverPos] = useState<{ x: number, y: number } | null>(null);

    const calculateInfluence = useCallback(() => {
        const newTide = Array(HEIGHT).fill(null).map(() => Array(WIDTH).fill({ kingdom: "neutral", power: 0 }));
        const newSec = Array(HEIGHT).fill(null).map(() => Array(WIDTH).fill(0));

        const activeShrines: { x: number, y: number, type: string, kingdom: string, potency: number, decay: number }[] = [];

        for (let y = 0; y < HEIGHT; y++) {
            for (let x = 0; x < WIDTH; x++) {
                const lm = biasLandmarks[y][x];
                if (lm === "shrine" || lm === "city") {
                    const kingdom = (x + y) % 2 === 0 ? "light" : "dark"; // DETERMINISTIC TEST MAPPING
                    activeShrines.push({
                        x, y, type: lm, kingdom,
                        potency: lm === "city" ? 40 : 25,
                        decay: lm === "city" ? 0.35 : 0.55
                    });
                }
            }
        }

        for (let y = 0; y < HEIGHT; y++) {
            for (let x = 0; x < WIDTH; x++) {
                let maxP = 0; let dom = "neutral";
                let maxS = 0;

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
        setTideMap(newTide);
        setSecMap(newSec);
    }, [biasLandmarks]);

    const negotiate = useCallback(async () => {
        calculateInfluence();
        try {
            await axios.post("/api/world/negotiate", {
                width: WIDTH, height: HEIGHT, config: weights,
                bias_elev: biasElev, bias_moist: biasMoist, bias_volume: biasVolume,
                bias_biomes: biasBiomes, bias_roads: biasRoads, bias_landmarks: biasLandmarks, grid
            });
            setStatus("NEGOTIATED");
        } catch (e) {
            console.error(e);
            setStatus("SYNC ERROR");
        }
    }, [weights, biasElev, biasMoist, biasVolume, biasBiomes, biasRoads, biasLandmarks, grid]);

    const generateFull = async (forceRandomSeed = false) => {
        if (anchorX === "" || anchorY === "" || anchorZ === "") {
            alert("Spatial Anchors Required! Please specify X, Y, and Z coordinates before manifesting.");
            return;
        }

        setIsGenerating(true);
        setStatus("GENESIS COMMENCING...");

        let activeWeights = { ...weights };
        if (forceRandomSeed) {
            const newSeed = Math.floor(Math.random() * 999999);
            activeWeights.seed = newSeed;
            setWeights(prev => ({ ...prev, seed: newSeed }));
        }

        try {
            const resp = await axios.post("/api/world/generate", {
                width: WIDTH, height: HEIGHT, config: activeWeights,
                intents: intents, // V9.0 INTENTS
                bias_elev: biasElev, bias_moist: biasMoist, bias_volume: biasVolume,
                bias_biomes: biasBiomes, bias_roads: biasRoads, bias_landmarks: biasLandmarks
            });
            setGrid(resp.data.grid);
            setElevMap(resp.data.elev_map);
            setMoistMap(resp.data.moist_map);
            if (resp.data.seed) setWeights(prev => ({ ...prev, seed: resp.data.seed }));
            setStatus("WORLD REALIZED");
        } catch (e) {
            console.error(e);
            setStatus("GENESIS FAILED");
        } finally {
            setIsGenerating(false);
        }
    };

    const handleSave = async () => {
        if (anchorX === "" || anchorY === "" || anchorZ === "") {
            alert("Spatial Anchors Missing! Specify coordinates to sharding.");
            return;
        }

        // [V9.0] SPATIAL SAFETY CHECK
        try {
            const checkResp = await axios.post('/api/world/check-conflicts', {
                offset_x: anchorX,
                offset_y: anchorY,
                width: WIDTH,
                height: HEIGHT
            });

            if (checkResp.data.conflict_count > 0) {
                const affectedZones = checkResp.data.zones.join(', ');
                const confirmed = window.confirm(
                    `SPATIAL CONFLICT DETECTED!\n\n` +
                    `There are ${checkResp.data.conflict_count} existing rooms in this coordinate range (Zones: ${affectedZones}).\n\n` +
                    `Saving will PERMANENTLY OVERWRITE these areas in the Live Engine. Are you sure?`
                );
                if (!confirmed) return;
            }
        } catch (e) {
            console.error("Conflict check failed, proceeding with caution", e);
        }

        setStatus("SHARDING WORLD...");
        try {
            const resp = await axios.post("/api/world/save", {
                grid,
                config: weights,
                intents: intents, // PERSIST INTENTS
                prefix: targetPrefix,
                offset_x: anchorX,
                offset_y: anchorY,
                offset_z: anchorZ
            });
            if (resp.data.status === "success") setStatus("SAVED: " + resp.data.msg);
        } catch (e) {
            console.error(e);
            setStatus("EXPORT FAILED");
        }
    };

    const handlePaint = (gx: number, gy: number) => {
        const R = Math.max(0, brushRadius - 1);
        const newElev = [...biasElev.map(r => [...r])];
        const newMoist = [...biasMoist.map(r => [...r])];
        const newVol = [...biasVolume.map(r => [...r])];
        const newBiomes = [...biasBiomes.map(r => [...r])];
        const newRoads = [...biasRoads.map(r => [...r])];
        const newLandmarks = [...biasLandmarks.map(r => [...r])];
        const newGrid = [...grid.map(r => [...r])];

        let volume = 0.1;
        let changed = false;

        for (let dy = -R; dy <= R; dy++) {
            for (let dx = -R; dx <= R; dx++) {
                const nx = gx + dx;
                const ny = gy + dy;
                if (nx >= 0 && nx < WIDTH && ny >= 0 && ny < HEIGHT) {
                    if (Math.sqrt(dx * dx + dy * dy) <= R) {
                        newVol[ny][nx] = Math.min(5.0, newVol[ny][nx] + volume);
                        changed = true;

                        const isLandmark = ["shrine", "monument", "tower", "ruins", "barrows", "city"].includes(activeTool);

                        if (activeTool === "water" || activeTool === "ocean") {
                            newElev[ny][nx] = Math.max(-1.0, newElev[ny][nx] - (volume * 2));
                            newBiomes[ny][nx] = activeTool;
                            newGrid[ny][nx] = activeTool;
                        } else if (activeTool === "peak" || activeTool === "mountain") {
                            newElev[ny][nx] = Math.min(1.0, newElev[ny][nx] + (volume * 2));
                            newBiomes[ny][nx] = activeTool;
                            newGrid[ny][nx] = activeTool;
                        } else if (activeTool === "rise") {
                            newElev[ny][nx] = Math.min(1.0, newElev[ny][nx] + volume);
                        } else if (activeTool === "sink") {
                            newElev[ny][nx] = Math.max(-1.0, newElev[ny][nx] - volume);
                        } else if (activeTool === "moist") {
                            newMoist[ny][nx] = Math.min(1.0, newMoist[ny][nx] + volume);
                        } else if (activeTool === "dry") {
                            newMoist[ny][nx] = Math.max(-1.0, newMoist[ny][nx] - volume);
                        } else if (activeTool === "road") {
                            newRoads[ny][nx] = 1;
                            newGrid[ny][nx] = "road";
                        } else if (isLandmark) {
                            newLandmarks[ny][nx] = activeTool;
                            newGrid[ny][nx] = activeTool;
                        } else if (activeTool === "erase") {
                            newVol[ny][nx] = 0.0;
                            newElev[ny][nx] = 0.0;
                            newMoist[ny][nx] = 0.0;
                            newBiomes[ny][nx] = null;
                            newRoads[ny][nx] = 0;
                            newLandmarks[ny][nx] = null;
                            newGrid[ny][nx] = "ocean";
                        } else {
                            newBiomes[ny][nx] = activeTool;
                            newGrid[ny][nx] = activeTool;
                        }
                    }
                }
            }
        }

        if (changed) {
            setBiasElev(newElev); setBiasMoist(newMoist); setBiasVolume(newVol);
            setBiasBiomes(newBiomes); setBiasRoads(newRoads); setBiasLandmarks(newLandmarks);
            setGrid(newGrid);
        }
    };

    const handleImportStencil = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = async (event) => {
            const base64 = event.target?.result as string;
            setStatus("INGESTING IMAGE STENCIL...");
            try {
                const resp = await axios.post("/api/world/import-stencil", { image_base64: base64, width: WIDTH, height: HEIGHT });
                if (resp.data.status === "success") {
                    setGrid(resp.data.grid); setBiasElev(resp.data.bias_elev);
                    setBiasMoist(resp.data.bias_moist); setBiasBiomes(resp.data.bias_biomes);
                    setBiasVolume(resp.data.bias_volume); setStatus("STENCIL LOADED: " + file.name);
                }
            } catch (err) { setStatus("STENCIL ERROR"); }
        };
        reader.readAsDataURL(file);
    };

    const handleHover = (gx: number, gy: number) => {
        if (gx >= 0 && gx < WIDTH && gy >= 0 && gy < HEIGHT) {
            const terr = grid[gy][gx];
            const e = elevMap ? elevMap[gy][gx] : biasElev[gy][gx];
            const m = moistMap ? moistMap[gy][gx] : biasMoist[gy][gx];
            const vol = biasVolume[gy][gx];
            const ax = anchorX === "" ? 0 : anchorX;
            const ay = anchorY === "" ? 0 : anchorY;
            const az = anchorZ === "" ? 0 : anchorZ;
            const tide = tideMap ? tideMap[gy][gx] : { kingdom: "neutral", power: 0 };
            const sec = secMap ? secMap[gy][gx] : 0;
            const msg = `POS: ${gx + ax}, ${gy + ay}, ${az}\nBIO: ${terr.toUpperCase()}\nE: ${e.toFixed(2)} M: ${m.toFixed(2)}\nTIDE: ${tide.kingdom.toUpperCase()} (${tide.power.toFixed(0)})\nSEC: ${sec.toFixed(1)}`;
            setTelemetry(msg);
        }
    };

    const handleWheel = (event: React.WheelEvent) => {
        if (event.ctrlKey) return;
        const scaleAmount = 0.15;
        const newZoom = event.deltaY < 0 ? zoom * (1 + scaleAmount) : zoom / (1 + scaleAmount);
        setZoom(Math.max(1, Math.min(5, newZoom)));
    };

    const handleMouseDown = (e: React.MouseEvent) => {
        if (e.button === 2) {
            e.preventDefault(); setIsPanning(true);
            setLastPanPos({ x: e.clientX, y: e.clientY });
        }
    };

    useEffect(() => {
        const handleGlobalMouseMove = (e: MouseEvent) => {
            if (isPanning) {
                const dx = e.clientX - lastPanPos.x;
                const dy = e.clientY - lastPanPos.y;
                setPanOffset(prev => ({ x: prev.x + dx / zoom, y: prev.y + dy / zoom }));
                setLastPanPos({ x: e.clientX, y: e.clientY });
            }
        };
        const handleGlobalMouseUp = () => setIsPanning(false);
        if (isPanning) {
            window.addEventListener("mousemove", handleGlobalMouseMove);
            window.addEventListener("mouseup", handleGlobalMouseUp);
        }
        return () => {
            window.removeEventListener("mousemove", handleGlobalMouseMove);
            window.removeEventListener("mouseup", handleGlobalMouseUp);
        };
    }, [isPanning, lastPanPos, zoom]);

    return (
        <div className="absolute inset-0 bg-black flex text-white overflow-hidden z-[100]">
            <SculptorPalette
                activeTool={activeTool} setActiveTool={setActiveTool}
                brushRadius={brushRadius} setBrushRadius={setBrushRadius}
                categories={BIOME_CATEGORIES}
            />

            <div className="flex-1 flex flex-col bg-[#050505]">
                <header className="h-16 border-b border-white/5 bg-zinc-950 flex items-center justify-between px-8 shadow-2xl z-10">
                    <div className="flex items-center gap-8">
                        <div className="flex items-center gap-3">
                            <div className="h-2 w-2 rounded-full bg-[#00bcd4] animate-pulse" />
                            <span className="text-[#00bcd4] text-xl font-black italic uppercase tracking-tighter">
                                World<span className="text-white">Sculptor</span>
                            </span>
                        </div>

                        <div className="flex items-center gap-1 bg-white/5 rounded-full p-1 border border-white/5">
                            <button
                                onClick={() => setViewMode("terrain")}
                                className={clsx("p-2 rounded-full transition-all", viewMode === "terrain" ? "bg-[#00bcd4] text-black shadow-lg" : "text-zinc-500 hover:text-white")}
                            >
                                <Layers size={14} />
                            </button>
                            <button
                                onClick={() => setViewMode("elev")}
                                className={clsx("p-2 rounded-full transition-all", viewMode === "elev" ? "bg-[#00bcd4] text-black shadow-lg" : "text-zinc-500 hover:text-white")}
                            >
                                <Zap size={14} />
                            </button>
                            <button
                                onClick={() => setViewMode("moist")}
                                className={clsx("p-2 rounded-full transition-all", viewMode === "moist" ? "bg-[#00bcd4] text-black shadow-lg" : "text-zinc-500 hover:text-white")}
                            >
                                <RefreshCw size={14} />
                            </button>
                            <div className="w-[1px] h-4 bg-white/10 mx-1" />
                            <button
                                onClick={() => setViewMode("tide")}
                                title="Divine Tide (Influence)"
                                className={clsx("p-2 rounded-full transition-all", viewMode === "tide" ? "bg-purple-500 text-white shadow-lg" : "text-zinc-500 hover:text-white")}
                            >
                                <Sun size={14} />
                            </button>
                            <button
                                onClick={() => setViewMode("sec")}
                                title="Security Rating (Frontier)"
                                className={clsx("p-2 rounded-full transition-all", viewMode === "sec" ? "bg-green-500 text-white shadow-lg" : "text-zinc-500 hover:text-white")}
                            >
                                <Shield size={14} />
                            </button>
                        </div>
                    </div>

                    <div className="flex items-center gap-4">
                        <div className="flex flex-col">
                            <label className="text-[8px] font-black text-zinc-600 uppercase tracking-widest mb-1 italic">World Name</label>
                            <input
                                type="text"
                                value={targetPrefix}
                                onChange={(e) => setTargetPrefix(e.target.value)}
                                placeholder="e.g. aetheria"
                                className="bg-black/40 border border-white/10 rounded-lg px-4 py-2 text-[10px] font-bold text-cyan-400 focus:outline-none focus:border-cyan-500/50 w-32 placeholder:text-zinc-800"
                            />
                        </div>

                        <div className="flex items-center gap-2 bg-black/40 border border-white/10 rounded-lg px-4 py-2 hover:border-cyan-500/30 transition-all">
                            <div className="flex flex-col border-r border-white/10 pr-3">
                                <label className="text-[7px] font-black text-zinc-600 uppercase mb-0.5 tracking-tighter">X-Anchor</label>
                                <input type="number" value={anchorX} onChange={(e) => setAnchorX(e.target.value === "" ? "" : parseInt(e.target.value))} placeholder="???" className="bg-transparent text-[10px] font-mono font-bold text-cyan-400 w-12 outline-none placeholder:text-zinc-800" />
                            </div>
                            <div className="flex flex-col border-r border-white/10 pr-3">
                                <label className="text-[7px] font-black text-zinc-600 uppercase mb-0.5 tracking-tighter">Y-Anchor</label>
                                <input type="number" value={anchorY} onChange={(e) => setAnchorY(e.target.value === "" ? "" : parseInt(e.target.value))} placeholder="???" className="bg-transparent text-[10px] font-mono font-bold text-cyan-400 w-12 outline-none placeholder:text-zinc-800" />
                            </div>
                            <div className="flex flex-col">
                                <label className="text-[7px] font-black text-zinc-600 uppercase mb-0.5 tracking-tighter">Z-Layer</label>
                                <input type="number" value={anchorZ} onChange={(e) => setAnchorZ(e.target.value === "" ? "" : parseInt(e.target.value))} placeholder="0" className="bg-transparent text-[10px] font-mono font-bold text-cyan-400 w-8 outline-none placeholder:text-zinc-800" />
                            </div>
                        </div>

                        <div className="flex items-center gap-2 bg-black/40 p-1 rounded-xl border border-white/5 mx-2">
                            <button
                                onClick={() => generateFull(false)}
                                disabled={isGenerating}
                                className="px-6 py-2 bg-[#00bcd4]/10 hover:bg-[#00bcd4]/20 text-[#00bcd4] text-[10px] font-black uppercase rounded-lg border border-[#00bcd4]/20 transition-all flex items-center gap-3 disabled:opacity-50"
                            >
                                <RefreshCw size={14} className={isGenerating ? "animate-spin" : ""} />
                                {isGenerating ? "Manifesting..." : "Realize"}
                            </button>
                            <button
                                onClick={() => generateFull(true)}
                                disabled={isGenerating}
                                title="Randomize Seed and Materialize World instantaneously"
                                className="px-6 py-2 bg-[#00bcd4] hover:bg-[#00acc1] text-black text-[10px] font-black uppercase rounded-lg shadow-[0_0_30px_rgba(0,188,212,0.3)] transition-all flex items-center gap-3 disabled:opacity-50"
                            >
                                <Zap size={14} fill="currentColor" />
                                Chaotic Realize
                            </button>
                        </div>

                        <div className="flex items-center gap-1.5 ml-4">
                            <button
                                className="p-2.5 bg-white/5 text-zinc-500 hover:text-white rounded-lg border border-white/5 transition-all"
                                title="Upload Stencil"
                                onClick={() => fileInputRef.current?.click()}
                            >
                                <Shield size={16} />
                            </button>
                            <button
                                className="p-2.5 bg-white/5 text-zinc-500 hover:text-white rounded-lg border border-white/5 transition-all"
                                title="Save Map State"
                                onClick={handleSave}
                            >
                                <DatabaseIcon size={16} />
                            </button>
                            <div className="w-[1px] h-6 bg-white/10 mx-2" />
                            <button
                                onClick={() => setWorkspace('studio')}
                                className="px-4 py-2 bg-zinc-800 text-zinc-400 hover:text-white text-[9px] font-black uppercase rounded-lg border border-white/5 transition-all flex items-center gap-2"
                            >
                                <MapIcon size={14} />
                                Studio
                            </button>
                            <button
                                onClick={() => setWorkspace('game')}
                                className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-white/5 transition-all text-[10px] font-black uppercase tracking-widest"
                            >
                                <Zap size={14} />
                                Game
                            </button>
                        </div>
                        <input type="file" ref={fileInputRef} className="hidden" accept="image/*" onChange={handleImportStencil} />
                    </div>
                </header>

                <main className="flex-1 overflow-hidden flex items-center justify-center bg-[#0a0a0a] relative group">
                    <div
                        className="relative shadow-[0_0_100px_rgba(0,0,0,0.9)] cursor-crosshair transition-transform duration-75 origin-center"
                        style={{ transform: `scale(${zoom}) translate(${panOffset.x}px, ${panOffset.y}px)` }}
                        onWheel={handleWheel}
                        onMouseDown={handleMouseDown}
                        onContextMenu={(e) => e.preventDefault()}
                    >
                        <SculptorCanvas
                            grid={grid} onPaint={handlePaint} onPaintEnd={negotiate}
                            onHover={handleHover}
                            onRightClick={() => { }} onSurvey={() => { }}
                            brushRadius={brushRadius} tileSize={6} zoom={zoom} viewMode={viewMode}
                            elevMap={elevMap} moistMap={moistMap}
                            tideMap={tideMap} secMap={secMap}
                            colorMap={Object.keys(COLOR_MAP).reduce((acc, tid) => {
                                acc[tid] = terrainRegistry?.terrains?.[tid]?.hex || COLOR_MAP[tid];
                                return acc;
                            }, {} as Record<string, string>)}
                            biasBiomes={biasBiomes} biasRoads={biasRoads} biasVolume={biasVolume}
                        />
                    </div>

                    <div className="absolute top-10 left-10 pointer-events-none space-y-4">
                        <div className="bg-black/80 backdrop-blur-3xl border border-white/5 p-6 rounded-[2rem] shadow-2xl min-w-[200px]">
                            <h4 className="text-[#00bcd4] text-[10px] font-black uppercase tracking-[0.3em] mb-3 flex items-center gap-2 italic">
                                <DatabaseIcon size={12} /> Live Telemetry
                            </h4>
                            <div className="font-mono text-[9px] text-zinc-400 space-y-1">
                                {telemetry.split('\n').map((l, i) => <div key={i}>{l}</div>)}
                            </div>
                        </div>
                    </div>
                </main>

                <footer className="h-10 border-t border-white/5 bg-zinc-950 flex items-center justify-between px-6 text-[9px] font-black text-zinc-600 tracking-widest uppercase italic">
                    <div className="flex items-center gap-6">
                        <span className="text-[#00bcd4] flex items-center gap-2">
                            <div className="h-1.5 w-1.5 rounded-full bg-[#00bcd4] animate-pulse" />
                            {status}
                        </span>
                        <span>DIMENSIONS: {WIDTH}x{HEIGHT}</span>
                    </div>
                    <span>ENGINE: OMNIPRESENT_SCULPTOR_V8.9</span>
                </footer>
            </div>

            <SculptorTuningDeck
                weights={weights} onWeightChange={(k, v) => setWeights(p => ({ ...p, [k]: v }))}
                intents={intents} onIntentChange={(k, v) => setIntents(p => ({ ...p, [k]: v }))}
                telemetry={telemetry}
            />
        </div>
    );
}
