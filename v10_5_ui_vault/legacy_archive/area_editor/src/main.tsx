import { useState, useEffect, useCallback, useRef } from "react";
import { createRoot } from 'react-dom/client'
// axios removed to lighten dependencies
import './index.css'

import type { Room, ZoneMetadata } from "./types";

// Components
import TopBar from "./components/TopBar";
import Palette from "./components/Palette";
import Viewport from "./components/Viewport";
import Inspector from "./components/Inspector";

const API_URL = "http://localhost:8000/api";
const GRID_SIZE = 50; 
const TILE_SIZE = 32;

function ShardEditor() {
  const [metadata, setMetadata] = useState<ZoneMetadata>({
    id: "new_zone", name: "New Uncharted Expanse", security_level: "mortal", grid_logic: true, target_cr: 1
  });
  const [rooms, setRooms] = useState<Record<string, Room>>({});
  const [selectedPos, setSelectedPos] = useState<{x: number, y: number} | null>(null);
  const [currentZ, setCurrentZ] = useState(0);
  const [activeTool, setActiveTool] = useState<string>("select");
  const [activeTemplate, setActiveTemplate] = useState<any>({
    name: "New Room", description: "Obsidian Chamber", terrain: "indoors", tags: []
  });
  const [mobs, setMobs] = useState<any[]>([]);
  const [terrain, setTerrain] = useState<any>({ multipliers: {}, opacity: {} });
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(1);
  const [isPanning, setIsPanning] = useState(false);
  const [activeViews, setActiveViews] = useState({ palette: true, inspector: true });
  const [hoverPos, setHoverPos] = useState<{x: number, y: number} | null>(null);
  const [isPainting, setIsPainting] = useState(false);
  const [showGhost, setShowGhost] = useState(true);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const startPanRef = useRef({ x: 0, y: 0 });
  const startMouseRef = useRef({ x: 0, y: 0 });

  const getRoomKey = (x: number, y: number, z: number) => `${x}.${y}.${z}`;

  useEffect(() => {
    const load = async () => {
      try {
        const [mRes, tRes] = await Promise.all([
          fetch(`${API_URL}/mobs`),
          fetch(`${API_URL}/terrain`)
        ]);
        const mData = await mRes.json();
        const tData = await tRes.json();
        setMobs(mData); 
        setTerrain(tData);
      } catch (e) { 
        console.warn("API Offline or Network Error", e); 
      }
    };
    load();
  }, []);

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.save();
    ctx.translate(canvas.width / 2 + pan.x, canvas.height / 2 + pan.y);
    ctx.scale(zoom, zoom);
    
    // Grid
    const startX = -GRID_SIZE/2, startY = -GRID_SIZE/2;
    for(let i=0; i<=GRID_SIZE; i++) {
      const isMajor = i % 10 === 0;
      ctx.strokeStyle = isMajor ? "rgba(255,255,255,0.15)" : "rgba(255,255,255,0.06)";
      ctx.lineWidth = 1 / zoom;
      
      ctx.beginPath(); 
      ctx.moveTo(startX*TILE_SIZE+i*TILE_SIZE, startY*TILE_SIZE); 
      ctx.lineTo(startX*TILE_SIZE+i*TILE_SIZE, (startY+GRID_SIZE)*TILE_SIZE); 
      ctx.stroke();

      ctx.beginPath(); 
      ctx.moveTo(startX*TILE_SIZE, startY*TILE_SIZE+i*TILE_SIZE); 
      ctx.lineTo((startX+GRID_SIZE)*TILE_SIZE, startY*TILE_SIZE+i*TILE_SIZE); 
      ctx.stroke();
    }

    // Rooms
    Object.values(rooms).forEach(r => {
      if (r.z === currentZ) {
        ctx.fillStyle = r.terrain === "forest" ? "rgba(34, 139, 34, 0.4)" : "rgba(100, 100, 110, 0.6)";
        ctx.fillRect(r.x * TILE_SIZE, r.y * TILE_SIZE, TILE_SIZE, TILE_SIZE);
        ctx.strokeStyle = "rgba(255,255,255,0.1)";
        ctx.strokeRect(r.x * TILE_SIZE, r.y * TILE_SIZE, TILE_SIZE, TILE_SIZE);
      }
    });

    // Highlight Selected
    if (selectedPos) {
      ctx.lineWidth = 2 / zoom;
      ctx.strokeStyle = "cyan";
      ctx.strokeRect(selectedPos.x * TILE_SIZE, selectedPos.y * TILE_SIZE, TILE_SIZE, TILE_SIZE);
    }

    // Brush Preview
    if (hoverPos && activeTool === "paint") {
      ctx.fillStyle = "rgba(0, 243, 255, 0.2)";
      ctx.fillRect(hoverPos.x * TILE_SIZE, hoverPos.y * TILE_SIZE, TILE_SIZE, TILE_SIZE);
      ctx.strokeStyle = "cyan";
      ctx.setLineDash([4, 4]);
      ctx.strokeRect(hoverPos.x * TILE_SIZE, hoverPos.y * TILE_SIZE, TILE_SIZE, TILE_SIZE);
      ctx.setLineDash([]);
    }

    ctx.restore();
  }, [rooms, currentZ, selectedPos, hoverPos, activeTool, zoom, pan]);

  useEffect(() => {
    draw();
    const handleResize = () => { if(canvasRef.current) { canvasRef.current.width = canvasRef.current.parentElement?.clientWidth || 0; canvasRef.current.height = canvasRef.current.parentElement?.clientHeight || 0; draw(); }};
    const handleKeyDown = (e: KeyboardEvent) => {
        if (e.key === "Home" || e.key === "h") { setPan({ x: 0, y: 0 }); setZoom(1); }
        if (e.key === "Escape") { setActiveTool("select"); setSelectedPos(null); }
    };
    window.addEventListener('resize', handleResize); handleResize();
    window.addEventListener('keydown', handleKeyDown);
    return () => {
        window.removeEventListener('resize', handleResize);
        window.removeEventListener('keydown', handleKeyDown);
    };
  }, [draw]);

  const onMouseDown = (e: React.MouseEvent) => {
    startMouseRef.current = { x: e.clientX, y: e.clientY };
    startPanRef.current = { ...pan };
    
    if (e.button === 1 || e.button === 2) { 
        setIsPanning(true); 
        return; 
    }
    
    const rect = canvasRef.current?.getBoundingClientRect(); if (!rect) return;
    const gx = Math.floor(((e.clientX - rect.left - rect.width/2 - pan.x)/zoom)/TILE_SIZE);
    const gy = Math.floor(((e.clientY - rect.top - rect.height/2 - pan.y)/zoom)/TILE_SIZE);
    
    if (activeTool === "paint") {
      setIsPainting(true);
      const key = getRoomKey(gx, gy, currentZ);
      setRooms(prev => ({ ...prev, [key]: { ...activeTemplate, id: `${gx}.${gy}.${currentZ}`, zone_id: metadata.id, x: gx, y: gy, z: currentZ } }));
    } else if (activeTool === "erase") {
      const key = getRoomKey(gx, gy, currentZ);
      setRooms(prev => { const n = {...prev}; delete n[key]; return n; });
    } else { 
      setSelectedPos({ x: gx, y: gy }); 
    }
  };

  const onMouseMove = (e: React.MouseEvent) => {
    const rect = canvasRef.current?.getBoundingClientRect(); if (!rect) return;
    
    if (isPanning) { 
      const dx = e.clientX - startMouseRef.current.x;
      const dy = e.clientY - startMouseRef.current.y;
      setPan({ x: startPanRef.current.x + dx, y: startPanRef.current.y + dy });
    }

    const gx = Math.floor(((e.clientX - rect.left - rect.width/2 - pan.x)/zoom)/TILE_SIZE);
    const gy = Math.floor(((e.clientY - rect.top - rect.height/2 - pan.y)/zoom)/TILE_SIZE);
    setHoverPos({ x: gx, y: gy });

    if (isPainting && activeTool === "paint" && !isPanning) {
      const key = getRoomKey(gx, gy, currentZ);
      if (!rooms[key]) {
        setRooms(prev => ({ ...prev, [key]: { ...activeTemplate, id: `${gx}.${gy}.${currentZ}`, zone_id: metadata.id, x: gx, y: gy, z: currentZ } }));
      }
    }
  };

  return (
    <div className="flex h-screen w-screen bg-[#030303] text-zinc-300 font-sans overflow-hidden flex-col">
      <TopBar onSave={() => {}} activeViews={activeViews} onToggleView={(v) => setActiveViews(p => ({...p, [v]: !((p as any)[v])}))} onOpen={() => {}} />
      <div className="flex flex-1 overflow-hidden">
        {activeViews.palette && <div className="w-64 border-r border-white/5 bg-[#080808]"><Palette activeTool={activeTool} activeTemplateName={activeTemplate.name} mobs={mobs} currentZ={currentZ} showGhost={showGhost} onSelectTool={setActiveTool} onSelectTemplate={setActiveTemplate} onUpdateZ={(d) => setCurrentZ(z=>z+d)} onToggleGhost={()=>setShowGhost(!showGhost)} /></div>}
        <div className="flex-1 overflow-hidden">
          <Viewport 
            canvasRef={canvasRef} 
            selectedPos={selectedPos} 
            hoverPos={hoverPos}
            activeTool={activeTool} 
            pan={pan} 
            zoom={zoom} 
            currentZ={currentZ} 
            onMouseDown={onMouseDown} 
            onMouseMove={onMouseMove} 
            onMouseUp={()=>{setIsPanning(false); setIsPainting(false);}} 
            onWheel={(e)=>setZoom(z=>Math.max(0.2, Math.min(5, z*(e.deltaY>0?0.9:1.1))))} 
            onResetView={()=>{setPan({x:0,y:0});setZoom(1);}} 
            onSelectTool={setActiveTool} 
          />
        </div>
        {activeViews.inspector && <div className="w-80 border-l border-white/5 bg-[#080808]"><Inspector selectedRoom={selectedPos ? rooms[getRoomKey(selectedPos.x, selectedPos.y, currentZ)] : null} metadata={metadata} terrain={terrain} onUpdateRoom={(d) => { if(!selectedPos) return; const k=getRoomKey(selectedPos.x,selectedPos.y,currentZ); setRooms(p=>({...p,[k]:{...p[k],...d}})) }} onClose={()=>setActiveViews(p=>({...p,inspector:false}))}/></div>}
      </div>
    </div>
  );
}

const root = document.getElementById('root')
if (root) createRoot(root).render(<ShardEditor />)
