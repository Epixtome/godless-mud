"use client";

import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { StudioCanvas } from "@/components/StudioCanvas";
import { Palette } from "@/components/Palette";
import { TuningDeck } from "@/components/TuningDeck";
import { 
  Square, 
  MousePointer2, 
  Save, 
  FolderOpen, 
  RefreshCw, 
  Layers, 
  Info,
  ChevronRight,
  ChevronLeft,
  X,
  Copy,
  Image as ImageIcon,
  Upload
} from "lucide-react";

// Standard biome colors from architect_data.py
const COLOR_MAP: Record<string, string> = {
  ocean: "#000044",
  water: "#0066cc",
  lake: "#004499",
  plains: "#228B22",
  grass: "#32CD32",
  meadow: "#7CFC00",
  mountain: "#808080",
  mountain_shadow: "#424242",
  high_mountain: "#A9A9A9",
  peak: "#FFFFFF",
  peak_shadow: "#A9A9A9",
  forest: "#006400",
  dense_forest: "#004d00",
  dense_forest_core: "#002b00",
  swamp: "#2f4f4f",
  desert: "#edc9af",
  wasteland: "#3e2723",
  city: "#ffd700",
  shrine: "#ff00ff",
  docks: "#795548",
  road: "#555555",
  cobblestone: "#777777",
  bridge: "#9e9e9e",
  beach: "#f5deb3",
  dirt_road: "#8b4513",
  ruins: "#424242",
  barrows: "#37474f",
  monument: "#00bcd4",
  tower: "#d32f2f",
  snow: "#f0f0f0",
  tundra: "#8d99ae",
  cliffs: "#4a4a4a",
  glacier: "#afeeee",
  market_ward: "#ffd700",
  residential_ward: "#80deea"
};

const BIOME_CATEGORIES = {
  Water: ["ocean", "water", "lake", "swamp"],
  Land: ["plains", "grass", "meadow", "desert", "wasteland", "beach"],
  Cold: ["snow", "tundra", "glacier"],
  Peak: ["mountain", "high_mountain", "peak"],
  Life: ["forest", "dense_forest", "hills"],
  Cultus: ["shrine", "monument", "tower", "ruins", "barrows"],
  Polis: ["city", "road", "bridge"],
  Conditions: ["dry", "moist", "rise", "sink"],
  Meta: ["cliffs", "inlet", "none"]
};

const WIDTH = 125;
const HEIGHT = 125;

export default function GodlessStudioV30() {
  const fileInputRef = React.useRef<HTMLInputElement>(null);
  const [grid, setGrid] = useState<string[][]>(
    Array(HEIGHT).fill(null).map(() => Array(WIDTH).fill("ocean"))
  );
  const [biasElev, setBiasElev] = useState<number[][]>(
    Array(HEIGHT).fill(null).map(() => Array(WIDTH).fill(0.0))
  );
  const [biasMoist, setBiasMoist] = useState<number[][]>(
    Array(HEIGHT).fill(null).map(() => Array(WIDTH).fill(0.0))
  );
  const [biasVolume, setBiasVolume] = useState<number[][]>(
    Array(HEIGHT).fill(null).map(() => Array(WIDTH).fill(0.0))
  );
  const [biasBiomes, setBiasBiomes] = useState<(string|null)[][]>(
    Array(HEIGHT).fill(null).map(() => Array(WIDTH).fill(null))
  );
  const [biasRoads, setBiasRoads] = useState<number[][]>(
    Array(HEIGHT).fill(null).map(() => Array(WIDTH).fill(0))
  );
  const [biasLandmarks, setBiasLandmarks] = useState<(string|null)[][]>(
    Array(HEIGHT).fill(null).map(() => Array(WIDTH).fill(null))
  );
  
  const [elevMap, setElevMap] = useState<number[][] | undefined>();
  const [moistMap, setMoistMap] = useState<number[][] | undefined>();

  const [activeTool, setActiveTool] = useState("peak");
  const [isGenerating, setIsGenerating] = useState(false);
  const [zoom, setZoom] = useState(1);
  const [panOffset, setPanOffset] = useState({ x: 0, y: 0 });
  const [isPanning, setIsPanning] = useState(false);
  const [lastPanPos, setLastPanPos] = useState({ x: 0, y: 0 });
  const [brushRadius, setBrushRadius] = useState(4);
  const [viewMode, setViewMode] = useState<"terrain" | "elev" | "moist">("terrain");
  const [weights, setWeights] = useState<Record<string, number>>({
    sea_level: 0.5,
    aridity: 0.5,
    peak_intensity: 0.5,
    mtn_clusters: 0.5,
    mtn_scale: 0.5,
    moisture_level: 0.5,
    land_density: 0.6,
    biome_isolation: 0.5,
    designer_authority: 0.5,
    erosion_scale: 0.2,
    fertility_rate: 1.0,
    blossom_speed: 1.0,
    melting_point: 0.0,
    seed: 42
  });

  const [status, setStatus] = useState("V30.0 READY");
  const [telemetry, setTelemetry] = useState("[ NO DATA ]");
  const [hoverPos, setHoverPos] = useState<{x: number, y: number} | null>(null);

  const negotiate = useCallback(async (
    currentWeights = weights,
    currElev = biasElev,
    currMoist = biasMoist,
    currVol = biasVolume,
    currBiomes = biasBiomes,
    currRoads = biasRoads,
    currLandmarks = biasLandmarks,
    currGrid = grid
  ) => {
    // [V32.0] PURE PAINT: We only sync to keep the server updated, we don't reset the grid.
    console.log("SYNC: Updating Server State...");
    try {
      await axios.post("http://localhost:8000/negotiate", {
        width: WIDTH,
        height: HEIGHT,
        config: currentWeights,
        bias_elev: currElev,
        bias_moist: currMoist,
        bias_volume: currVol,
        bias_biomes: currBiomes,
        bias_roads: currRoads,
        bias_landmarks: currLandmarks,
        grid: currGrid
      });
      setStatus("V32.0 READY");
    } catch (e) {
      console.error(e);
      setStatus("SYNC FAILED");
    }
  }, [weights, biasElev, biasMoist, biasVolume, biasBiomes, biasRoads, biasLandmarks, grid]);

  const handleImportStencil = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = async (event) => {
      const base64 = event.target?.result as string;
      setStatus("INGESTING IMAGE STENCIL...");
      try {
        const resp = await axios.post("http://localhost:8000/import_stencil", {
          image_base64: base64,
          width: WIDTH,
          height: HEIGHT
        });
        
        if (resp.data.status === "success") {
          setGrid(resp.data.grid);
          setBiasElev(resp.data.bias_elev);
          setBiasMoist(resp.data.bias_moist);
          setBiasBiomes(resp.data.bias_biomes);
          setBiasVolume(resp.data.bias_volume);
          setStatus("STENCIL LOADED: " + file.name);
        }
      } catch (err) {
        console.error(err);
        setStatus("STENCIL ERROR");
      }
    };
    reader.readAsDataURL(file);
  };

  const handlePaint = (gx: number, gy: number) => {
    // [V41.0] SINGLE PIXEL PRECISION: Radius 1 = 0.0 (Singular Point)
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
          if (Math.sqrt(dx*dx + dy*dy) <= R) {
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
      setBiasElev(newElev);
      setBiasMoist(newMoist);
      setBiasVolume(newVol);
      setBiasBiomes(newBiomes);
      setBiasRoads(newRoads);
      setBiasLandmarks(newLandmarks);
      setGrid(newGrid);
    }
  };

  const generateFull = async (overrideWeights?: any) => {
    const activeWeights = overrideWeights || weights;
    setIsGenerating(true);
    setStatus("GENERATING FULL WORLD...");
    try {
      const resp = await axios.post("http://localhost:8000/generate", {
        width: WIDTH,
        height: HEIGHT,
        config: activeWeights,
        bias_elev: biasElev,
        bias_moist: biasMoist,
        bias_volume: biasVolume,
        bias_biomes: biasBiomes,
        bias_roads: biasRoads,
        bias_landmarks: biasLandmarks
      });
      setGrid(resp.data.grid);
      setElevMap(resp.data.elev_map);
      setMoistMap(resp.data.moist_map);
      if (resp.data.seed) {
        setWeights(prev => ({...prev, seed: resp.data.seed}));
      }
      setStatus("FULL GENERATION COMPLETE");
    } catch (e) {
      console.error(e);
      setStatus("FULL GENERATION FAILED");
    } finally {
      setIsGenerating(false);
    }
  };
    
  const handleSave = async () => {
    setStatus("EXPORTING ZONE...");
    try {
      const resp = await axios.post("http://localhost:8000/save", {
        grid: grid,
        config: weights
      });
      if (resp.data.status === "success") {
        setStatus("SAVED: " + resp.data.msg);
      }
    } catch (e) {
      console.error(e);
      setStatus("EXPORT FAILED");
    }
  };

  const handleHover = (gx: number, gy: number) => {
    if (gx >= 0 && gx < WIDTH && gy >= 0 && gy < HEIGHT) {
      const terr = grid[gy][gx];
      const e = elevMap ? elevMap[gy][gx] : biasElev[gy][gx];
      const m = moistMap ? moistMap[gy][gx] : biasMoist[gy][gx];
      const vol = biasVolume[gy][gx];
      const road = biasRoads[gy][gx] ? " [ROAD]" : "";
      const landmark = biasLandmarks[gy][gx] ? ` [${biasLandmarks[gy][gx]?.toUpperCase()}]` : "";
      
      const msg = `POS: ${gx+9000}, ${gy+9000}\nBIO: ${terr.toUpperCase()}${road}${landmark}\nE: ${e.toFixed(2)} M: ${m.toFixed(2)}\nAUTH: ${(vol * 20).toFixed(0)}%`;
      setTelemetry(msg);
    }
  };

  const handleRightClick = (gx: number, gy: number) => {
    if (gx >= 0 && gx < WIDTH && gy >= 0 && gy < HEIGHT) {
      const terr = grid[gy][gx];
      const abs_str = `(${gx+9000}, ${gy+9000}) | ${terr.toUpperCase()}`;
      navigator.clipboard.writeText(abs_str);
      setActiveTool(terr);
      setStatus(`COPIED & SET: ${abs_str}`);
    }
  };

  const handleSurvey = (start: {x: number, y: number}, end: {x: number, y: number}) => {
    const x1 = Math.min(start.x, end.x) + 9000;
    const y1 = Math.min(start.y, end.y) + 9000;
    const x2 = Math.max(start.x, end.x) + 9000;
    const y2 = Math.max(start.y, end.y) + 9000;
    const range_str = `RANGE: (${x1}, ${y1}) to (${x2}, ${y2})`;
    navigator.clipboard.writeText(range_str);
    setStatus(`COPIED RANGE: ${x1},${y1}..${x2},${y2}`);
  };

  const handlePaintEnd = () => {
    negotiate(weights, biasElev, biasMoist, biasVolume, biasBiomes, biasRoads, biasLandmarks, grid);
  };

  const handleWheel = (event: React.WheelEvent<HTMLDivElement>) => {
    if (event.ctrlKey) return; 
    const scaleAmount = 0.15;
    const newZoom = event.deltaY < 0 ? zoom * (1 + scaleAmount) : zoom / (1 + scaleAmount);
    setZoom(Math.max(1, Math.min(5, newZoom))); 
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    // Right click to pan
    if (e.button === 2) {
      e.preventDefault();
      setIsPanning(true);
      setLastPanPos({ x: e.clientX, y: e.clientY });
    }
  };

  const handleMouseReset = () => {
    setZoom(1);
    setPanOffset({ x: 0, y: 0 });
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

  useEffect(() => {
    // Check API Status
    axios.get("http://localhost:8000/status")
      .then(() => setStatus("V32.0 ONLINE"))
      .catch(() => setStatus("OFFLINE"));
  }, []);

  useEffect(() => {
    if (hoverPos) {
      handleHover(hoverPos.x, hoverPos.y);
    } else {
      setTelemetry("[ NO DATA ]");
    }
  }, [hoverPos, grid, elevMap, moistMap, biasElev, biasMoist, biasVolume, biasRoads, biasLandmarks]);

  return (
    <div className="flex h-screen w-screen bg-black text-white font-sans overflow-hidden">
      {/* LEFT: PALETTE */}
      <Palette 
        activeTool={activeTool} 
        setActiveTool={setActiveTool} 
        brushRadius={brushRadius}
        setBrushRadius={setBrushRadius}
        categories={BIOME_CATEGORIES}
      />

      {/* CENTER: VIEWPORT */}
      <div className="flex-1 flex flex-col bg-[#050505]">
        {/* TOOLBAR */}
        <header className="h-14 border-b border-zinc-900 bg-zinc-950 flex items-center justify-between px-6 shadow-md z-10">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
              <span className="text-[#00bcd4] text-xl font-black lowercase tracking-tighter">Godless World Sculptor</span>
              <span className="bg-[#00bcd4]/10 text-[#00bcd4] text-[9px] font-bold px-1.5 py-0.5 rounded border border-[#00bcd4]/20">INTENT-DRIVEN</span>
            </div>
            
            <div className="h-4 w-px bg-zinc-800" />
            
            <div className="flex items-center gap-1">
              <button 
                onClick={() => setViewMode("terrain")}
                className={`p-1.5 rounded transition-all ${viewMode === "terrain" ? "bg-[#00bcd4] text-white" : "text-zinc-500 hover:text-white"}`}
                title="Terrain View"
              >
                <Layers size={14} />
              </button>
              <button 
                onClick={() => setViewMode("elev")}
                className={`p-1.5 rounded transition-all ${viewMode === "elev" ? "bg-[#00bcd4] text-white" : "text-zinc-500 hover:text-white"}`}
                title="Elevation Heatmap"
              >
                <RefreshCw size={14} />
              </button>
              <button 
                onClick={() => setViewMode("moist")}
                className={`p-1.5 rounded transition-all ${viewMode === "moist" ? "bg-[#00bcd4] text-white" : "text-zinc-500 hover:text-white"}`}
                title="Moisture Heatmap"
              >
                <RefreshCw size={14} className="rotate-45" />
              </button>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 bg-zinc-900/50 border border-zinc-800 rounded px-2 py-1">
              <span className="text-[9px] font-bold text-zinc-500 uppercase">Seed</span>
              <input 
                type="number"
                value={weights.seed}
                onChange={(e) => setWeights(prev => ({...prev, seed: parseInt(e.target.value)}))}
                className="bg-transparent text-[#00bcd4] text-xs font-mono font-bold w-16 focus:outline-none"
              />
              <button 
                onClick={() => {
                  const newSeed = Math.floor(Math.random() * 999999);
                  setWeights(prev => ({...prev, seed: newSeed}));
                  generateFull({...weights, seed: newSeed});
                }}
                className="p-1 hover:text-[#00bcd4] transition-colors"
                title="Randomize Seed"
              >
                <RefreshCw size={12} className={weights.seed === 0 ? "animate-spin" : ""} />
              </button>
            </div>

            <button 
              onClick={handleMouseReset}
              className="p-1.5 text-zinc-500 hover:text-[#00bcd4] transition-all"
              title="Reset Zoom & Pan"
            >
              <MousePointer2 size={14} />
            </button>
            <button 
              onClick={() => generateFull()}
              disabled={isGenerating}
              className="px-4 py-1.5 bg-[#00bcd4] hover:bg-[#00acc1] text-black text-[10px] font-black uppercase rounded shadow-lg shadow-[#00bcd4]/20 transition-all flex items-center gap-2"
            >
              <RefreshCw size={12} className={isGenerating ? "animate-spin" : ""} />
              {isGenerating ? "Realizing..." : "Realize World"}
            </button>
            <button 
              className="p-1.5 text-zinc-500 hover:text-white transition-all"
              onClick={() => fileInputRef.current?.click()}
              title="Import Image Stencil"
            >
              <Upload size={14} />
            </button>
            <input 
              type="file" 
              ref={fileInputRef} 
              className="hidden" 
              accept="image/*"
              onChange={handleImportStencil}
            />
            <button 
              className="p-1.5 text-zinc-500 hover:text-white transition-all"
              onClick={handleSave}
              title="Export Zone JSON"
            >
              <Save size={14} />
            </button>
            <button className="p-1.5 text-zinc-500 hover:text-white transition-all"><FolderOpen size={14} /></button>
          </div>
        </header>

        {/* MAP VIEWPORT */}
        <main className="flex-1 overflow-hidden flex items-center justify-center bg-[#0a0a0a] relative group">
          <div className="absolute top-6 left-6 z-20 flex flex-col gap-2 pointer-events-none">
             <div className="bg-black/80 backdrop-blur-md border border-zinc-800 p-3 rounded-lg text-[10px] font-mono text-zinc-400 shadow-2xl space-y-2">
                <div className="flex items-center gap-2 border-b border-zinc-800 pb-1.5 mb-1.5">
                  <div className="h-2 w-2 rounded-full bg-[#00bcd4] animate-pulse" />
                  <span className="text-[#00bcd4] font-black tracking-widest uppercase">Probe Telemetry</span>
                </div>
                {telemetry.split('\n').map((line, i) => (
                  <div key={i}>{line}</div>
                ))}
             </div>
          </div>

          <div 
            className="relative shadow-[0_0_60px_rgba(0,0,0,0.8)] cursor-crosshair transition-transform duration-75 origin-center"
            style={{ 
              transform: `scale(${zoom}) translate(${panOffset.x}px, ${panOffset.y}px)`,
              cursor: isPanning ? 'grabbing' : (activeTool === 'shrine' || activeTool === 'city' ? 'pointer' : 'crosshair')
            }}
            onWheel={handleWheel}
            onMouseDown={handleMouseDown}
            onContextMenu={(e) => e.preventDefault()}
          >
            <StudioCanvas 
              grid={grid} 
              onPaint={handlePaint} 
              onPaintEnd={handlePaintEnd}
              onHover={(x, y) => setHoverPos({ x, y })}
              onRightClick={handleRightClick}
              onSurvey={handleSurvey}
              brushRadius={brushRadius}
              tileSize={6}
              zoom={zoom}
              viewMode={viewMode}
              elevMap={elevMap}
              moistMap={moistMap}
              colorMap={COLOR_MAP}
              biasBiomes={biasBiomes}
              biasRoads={biasRoads}
              biasVolume={biasVolume}
            />
          </div>
        </main>

        {/* FOOTER: STATUS */}
        <footer className="h-8 border-t border-zinc-900 bg-zinc-950 flex items-center justify-between px-4 text-[9px] font-bold text-zinc-500 tracking-wider">
          <div className="flex items-center gap-4">
             <span className="text-[#00bcd4] flex items-center gap-1.5 lowercase">
               <div className="h-1.5 w-1.5 rounded-full bg-[#00bcd4] animate-pulse" />
               {status}
             </span>
             <span>DIMENSIONS: {WIDTH}x{HEIGHT}</span>
          </div>
          <div className="flex items-center gap-4">
             <span>ENGINE: SCULPTOR_V1.0</span>
             <span>MODE: SOVEREIGN_INTENT</span>
          </div>
        </footer>
      </div>

      {/* RIGHT: TUNING DECK */}
      <TuningDeck 
        weights={weights} 
        onWeightChange={(key, val) => setWeights(prev => ({...prev, [key]: val}))}
        telemetry={telemetry}
      />
    </div>
  );
}
