import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  Layers, Map, Database, Info, 
  Compass, ChevronRight, Plus, X, 
  Zap, Users, Search
} from 'lucide-react';
import { useStore } from '../../store/useStore';
import { motion, AnimatePresence } from 'framer-motion';
import { clsx } from 'clsx';
import RemoteCanvas from './RemoteCanvas';

export default function StudioWorkspace() {
  const { setWorkspace } = useStore();
  const [zones, setZones] = useState<string[]>([]);
  const [activeZone, setActiveZone] = useState<string | null>(null);
  const [rooms, setRooms] = useState<any[]>([]);
  const [selectedRoom, setSelectedRoom] = useState<any | null>(null);
  const [players, setPlayers] = useState<any[]>([]);
  const [showPlayerList, setShowPlayerList] = useState(false);
  const [brushMode, setBrushMode] = useState<'select' | 'paint' | 'erase'>('select');
  const [brushSize, setBrushSize] = useState(1);
  const [activeTerrain, setActiveTerrain] = useState('plains');
  const [terrainList, setTerrainList] = useState<string[]>([]);
  const [elevations, setElevations] = useState<Record<string, number>>({});
  const [currentZ, setCurrentZ] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState('connecting...');
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved'>('idle');
  const [centerRequest, setCenterRequest] = useState<{x: number, y: number} | null>(null);
  const [hoveredCell, setHoveredCell] = useState<{x: number, y: number, terrain?: string} | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [selectedRooms, setSelectedRooms] = useState<any[]>([]);
  const [contextMenu, setContextMenu] = useState<{x: number, y: number, coords: {x: number, y: number}} | null>(null);

  // Load Initial Data
  useEffect(() => {
    checkStatus();
    loadZoneList();
    loadAssets();
    refreshMapData();

    const handleKeyDown = (e: KeyboardEvent) => {
        if (e.key.toLowerCase() === 'b') setBrushMode('paint');
        if (e.key.toLowerCase() === 'v') setBrushMode('select');
        if (e.key.toLowerCase() === 'e') setBrushMode('erase');
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const checkStatus = async () => {
    try {
      const resp = await axios.get('/api/status');
      setStatus(resp.data.mode);
    } catch (e) {
      setStatus('OFFLINE');
    }
  };

  const loadZoneList = async () => {
    try {
      const resp = await axios.get('/api/zones');
      setZones(resp.data.zones);
    } catch (e) {
        console.error("Failed to load zones", e);
    }
  };

  const refreshMapData = async () => {
    try {
        const mapResp = await axios.get('/api/map-data');
        setRooms(mapResp.data.rooms || []);
        if (mapResp.data.source === 'live_memory') setIsStreaming(true);
    } catch (e) {
        console.error("Auto-load failed", e);
    }
  };

  const loadPlayers = async () => {
    try {
      const resp = await axios.get('/api/players');
      setPlayers(resp.data.players);
    } catch (e) {
      console.error("Failed to load players", e);
    }
  };

  const unloadZone = async () => {
    setIsLoading(true);
    try {
      await axios.get('/api/unload');
      const mapResp = await axios.get('/api/map-data');
      setRooms(mapResp.data.rooms || []);
      setActiveZone(null);
      setIsStreaming(true);
    } catch (e) {
      console.error("Unload failed", e);
    } finally {
      setIsLoading(false);
    }
  };

  const loadAssets = async () => {
    try {
      const resp = await axios.get('/api/assets');
      setTerrainList(resp.data.terrains);
      setElevations(resp.data.elevations);
    } catch (e) {
        console.error("Failed to load assets", e);
    }
  };

  const loadZone = async (zone_id: string) => {
    setIsLoading(true);
    setIsStreaming(false);
    try {
      await axios.get(`/api/load/${zone_id}`);
      const mapResp = await axios.get('/api/map-data');
      setRooms(mapResp.data.rooms);
      setActiveZone(zone_id);
      setSelectedRoom(null);
    } catch (e) {
        console.error("Failed to load zone", e);
    }
    setIsLoading(false);
  };

  const createZone = async () => {
    const name = prompt("Enter shard identifier (e.g. 'aetheria_heights'):");
    if (!name) return;
    setIsLoading(true);
    try {
      await axios.post('/api/create', { id: name });
      const mapResp = await axios.get('/api/map-data');
      setRooms(mapResp.data.rooms);
      setActiveZone(name);
      setSelectedRoom(null);
      loadZoneList();
    } catch (e) {
      alert("Failed to create shard");
    } finally {
      setIsLoading(false);
    }
  };

  const saveZone = async () => {
    setSaveStatus('saving');
    try {
      await axios.post('/api/save');
      setSaveStatus('saved');
      setTimeout(() => setSaveStatus('idle'), 3000);
    } catch (e) {
      alert('Failed to save');
      setSaveStatus('idle');
    }
  };

  const handleCellAction = async (x: number, y: number) => {
    if (brushMode === 'select') {
        const room = rooms.find(r => r.x === x && r.y === y && r.z === currentZ);
        setSelectedRoom(room || { x, y, z: currentZ, terrain: 'plains', name: "Empty Space", description: "" });
        if (room) setSelectedRooms(prev => prev.some(r => r.x === x && r.y === y) ? prev : [...prev, room]);
        setContextMenu(null);
        return;
    }

    const terrainToApply = brushMode === 'erase' ? 'ocean' : activeTerrain;
    
    // Optimistic Update
    const affectedRooms: any[] = [];
    const half = Math.floor(brushSize / 2);
    
    for (let dx = -half; dx <= half; dx++) {
        for (let dy = -half; dy <= half; dy++) {
            affectedRooms.push({ x: x + dx, y: y + dy, z: currentZ, terrain: terrainToApply });
        }
    }

    setRooms(prev => {
        const next = [...prev];
        affectedRooms.forEach(ar => {
            const idx = next.findIndex(r => r.x === ar.x && r.y === ar.y && r.z === ar.z);
            if (idx >= 0) next[idx] = { ...next[idx], terrain: ar.terrain, name: next[idx].name || "Modified Room" };
            else next.push({ ...ar, name: "New Room", description: "Sculpted Area" });
        });
        return next;
    });

    // Network Sync
    try {
        await Promise.all(affectedRooms.map(ar => 
            axios.post('/api/update-room', ar)
        ));
    } catch (e) {
        console.error("Failed to sync room update", e);
    }
  };

  const handleSelectionChange = (bounds: {x1: number, y1: number, x2: number, y2: number}) => {
    const selected = rooms.filter(r => 
        r.x >= bounds.x1 && r.x <= bounds.x2 && 
        r.y >= bounds.y1 && r.y <= bounds.y2 && 
        r.z === currentZ
    );
    setSelectedRooms(selected);
    if (selected.length > 0) setSelectedRoom(selected[0]);
  };

  const handleBulkUpdate = async (field: string, value: any) => {
    const updated = selectedRooms.map(r => ({ ...r, [field]: value }));
    setSelectedRooms(updated);
    if (selectedRoom) setSelectedRoom({ ...selectedRoom, [field]: value });
    
    setRooms(prev => prev.map(r => {
        const up = updated.find(u => u.x === r.x && u.y === r.y && u.z === r.z);
        return up || r;
    }));

    try {
        await Promise.all(updated.map(r => axios.post('/api/update-room', r)));
        setSaveStatus('saved');
        setTimeout(() => setSaveStatus('idle'), 2000);
    } catch (e) {
        console.error("Bulk update failed", e);
    }
  };

  const handleRightClick = (x: number, y: number) => {
    setContextMenu({ x: window.innerWidth / 2, y: window.innerHeight / 2, coords: { x, y } });
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setSaveStatus('saved');
    setTimeout(() => setSaveStatus('idle'), 1000);
  };

  const dispatchTeleport = async (player: string, x: number, y: number) => {
    try {
      await axios.post('/api/teleport', { name: player, x, y, z: currentZ });
      loadPlayers();
    } catch (e) {
      console.error("Teleport failed", e);
    }
  };

  return (
    <div className="absolute inset-0 bg-slate-950 flex flex-col overflow-hidden animate-in fade-in duration-500 z-[100]">
      {/* Studio Header */}
      <header className="h-16 border-b border-white/5 bg-slate-900/40 backdrop-blur-xl flex items-center justify-between px-8 z-50">
        <div className="flex items-center gap-8">
          <div className="flex items-center gap-3">
             <div className="h-2 w-2 rounded-full bg-cyan-500 animate-pulse shadow-[0_0_10px_#00bcd4]" />
             <h1 className="font-black tracking-tighter text-white text-xl italic uppercase">
                Divine<span className="text-cyan-500">Studio</span>
             </h1>
          </div>
          
          <div className="h-6 w-px bg-white/10" />
          
          <nav className="flex items-center gap-6">
             <button 
                onClick={unloadZone} 
                className="group flex items-center gap-2"
             >
               <Map size={16} className="text-slate-400 group-hover:text-cyan-400 transition-colors" />
               <span className={clsx(
                 "text-[11px] font-black uppercase tracking-widest transition-colors",
                 activeZone ? "text-cyan-400" : "text-slate-500 group-hover:text-white"
               )}>
                 {activeZone || 'Streaming Live Engine'}
               </span>
               <ChevronRight size={12} className="text-slate-700" />
             </button>

             {activeZone && (
               <div className="flex items-center gap-3 bg-white/5 px-4 py-1.5 rounded-full border border-white/5 self-center">
                  <Layers size={13} className="text-cyan-500" />
                  <span className="text-[10px] font-black uppercase text-slate-500 tracking-tighter">Vertical Plane</span>
                  <div className="flex items-center gap-3 ml-2">
                    <button onClick={() => setCurrentZ(z => z - 1)} className="hover:text-cyan-400 text-xs">▼</button>
                    <span className="w-4 text-center font-mono text-cyan-400 font-bold">{currentZ}</span>
                    <button onClick={() => setCurrentZ(z => z + 1)} className="hover:text-cyan-400 text-xs">▲</button>
                  </div>
               </div>
             )}
          </nav>
        </div>

        <div className="flex items-center gap-6">
            <div className="flex flex-col items-end">
                <span className="text-[9px] font-bold text-slate-600 uppercase tracking-widest leading-none mb-1">Engine Stability</span>
                <span className="text-[10px] font-black text-cyan-500 uppercase tracking-tighter italic">Mode: {status}</span>
            </div>
            
            <button 
                onClick={saveZone} 
                disabled={saveStatus === 'saving' || !activeZone}
                className={clsx(
                    "flex items-center gap-2 px-8 py-2.5 rounded-lg transition-all font-black text-[10px] uppercase tracking-[0.2em]",
                    !activeZone ? "opacity-20 cursor-not-allowed grayscale" : 
                    saveStatus === 'saved' ? "bg-green-500 text-white shadow-[0_0_20px_rgba(34,197,94,0.3)]" :
                    saveStatus === 'saving' ? "bg-slate-800 text-slate-500" :
                    "bg-cyan-600 hover:bg-cyan-500 text-white shadow-[0_0_20px_rgba(8,145,178,0.3)]"
                )}
            >
                <Database size={14} />
                {saveStatus === 'saved' ? 'SYNCED' : saveStatus === 'saving' ? 'WRITING...' : 'SAVE SHARD'}
            </button>

            <div className="h-6 w-px bg-white/10" />

            <button 
                onClick={() => setWorkspace('game')}
                className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-white/5 transition-all text-[10px] font-black uppercase tracking-widest"
            >
                <Zap size={14} />
                Game
            </button>
        </div>
      </header>

      {/* Main Workspace Area */}
      <main className="flex-1 flex overflow-hidden relative">
        {/* Left Vertical Toolbelt */}
        <aside className="w-20 border-r border-white/5 bg-slate-900/20 backdrop-blur-xl flex flex-col items-center py-10 gap-8 z-20">
            <button 
              onClick={() => { 
                const newState = !showPlayerList;
                setShowPlayerList(newState); 
                if (newState) loadPlayers(); 
              }}
              title="Player Tracker (P)"
              className={clsx(
                "p-4 rounded-2xl transition-all border",
                showPlayerList 
                 ? "bg-purple-500 text-white border-purple-400 shadow-[0_0_20px_rgba(168,85,247,0.4)]" 
                 : "text-slate-500 border-transparent hover:bg-white/5 hover:text-slate-300"
              )}
            >
              <Users size={22} />
            </button>

            <div className="h-px w-10 bg-white/5" />

            <button 
              onClick={() => setBrushMode('select')}
             title="Entity Probe (V)"
             className={clsx(
               "p-4 rounded-2xl transition-all border",
               brushMode === 'select' 
                ? "bg-cyan-500 text-white border-cyan-400 shadow-[0_0_20px_rgba(6,182,212,0.4)]" 
                : "text-slate-500 border-transparent hover:bg-white/5 hover:text-slate-300"
             )}
           >
             <Map size={22} />
           </button>

           <button 
             onClick={() => setBrushMode('paint')}
             title="Terrain Brush (B)"
             className={clsx(
               "p-4 rounded-2xl transition-all border",
               brushMode === 'paint' 
                ? "bg-cyan-500 text-white border-cyan-400 shadow-[0_0_20px_rgba(6,182,212,0.4)]" 
                : "text-slate-500 border-transparent hover:bg-white/5 hover:text-slate-300"
             )}
           >
             <Map size={22} />
           </button>

           <div className="h-px w-10 bg-white/5" />

            <button 
              onClick={() => setBrushMode('erase')}
              title="Void Eraser (E)"
              className={clsx(
                "p-4 rounded-2xl transition-all border",
                brushMode === 'erase' 
                 ? "bg-red-500 text-white border-red-400 shadow-[0_0_20px_rgba(239,68,68,0.4)]" 
                 : "text-slate-500 border-transparent hover:bg-white/5 hover:text-slate-300"
              )}
            >
              <X size={22} />
            </button>

            <div className="h-px w-10 bg-white/5" />

            <div className="flex flex-col gap-2">
                {[1, 3, 5].map(size => (
                    <button
                        key={size}
                        onClick={() => { setBrushSize(size); setBrushMode('paint'); }}
                        className={clsx(
                            "w-10 h-10 rounded-xl border flex items-center justify-center text-[10px] font-black transition-all",
                            brushSize === size 
                                ? "bg-cyan-500/20 border-cyan-400 text-cyan-400" 
                                : "bg-white/5 border-transparent text-slate-500 hover:text-slate-300"
                        )}
                    >
                        {size}x
                    </button>
                ))}
            </div>

           <div className="mt-auto mb-6 flex flex-col items-center gap-1 opacity-20">
              <Map size={14} />
              <span className="text-[8px] font-black uppercase tracking-[0.3em] vertical-text">V8.0</span>
           </div>
        </aside>

        {/* The World Canvas */}
        <section className="flex-1 bg-slate-950 relative overflow-hidden">
           {(activeZone || isStreaming) ? (
             <>
                <RemoteCanvas 
                    rooms={rooms.filter(r => r.z === currentZ)}
                    selectedRoom={selectedRoom}
                    onRoomSelect={setSelectedRoom}
                    brushSize={brushSize}
                    activeTerrain={brushMode === 'select' ? '' : brushMode === 'erase' ? 'ocean' : activeTerrain}
                    elevations={elevations}
                    onCellClick={handleCellAction}
                    onHover={(x: number, y: number) => {
                        const r = rooms.find(rm => rm.x === x && rm.y === y && rm.z === currentZ);
                        setHoveredCell({ x, y, terrain: r?.terrain });
                    }}
                    onRightClick={handleRightClick}
                    onSelectionChange={handleSelectionChange}
                    centerPos={centerRequest}
                />

                {/* Divine Context Menu */}
                <AnimatePresence>
                    {contextMenu && (
                        <motion.div
                            initial={{ opacity: 0, scale: 0.9, y: 10 }}
                            animate={{ opacity: 1, scale: 1, y: 0 }}
                            exit={{ opacity: 0, scale: 0.9, y: 10 }}
                            className="absolute z-[100] bg-slate-900/95 border border-white/10 rounded-3xl shadow-[0_20px_50px_rgba(0,0,0,0.5)] backdrop-blur-3xl p-3 w-64 space-y-1"
                            style={{ left: window.innerWidth / 2 - 128, top: window.innerHeight / 2 - 120 }}
                        >
                            <div className="px-4 py-3 text-[10px] font-black text-slate-500 uppercase tracking-[0.3em] border-b border-white/5 mb-2 flex justify-between items-center italic">
                                <span>Spatial Flux</span>
                                <span className="text-cyan-500/50">{contextMenu.coords.x},{contextMenu.coords.y}</span>
                            </div>
                            
                            <button 
                                onClick={() => {
                                    const r = rooms.find(rm => rm.x === contextMenu.coords.x && rm.y === contextMenu.coords.y && rm.z === currentZ);
                                    if (r) {
                                        setActiveTerrain(r.terrain);
                                        setBrushMode('paint');
                                    }
                                    setContextMenu(null);
                                }}
                                className="w-full flex items-center gap-4 px-4 py-3 text-xs font-bold text-slate-300 hover:bg-white/5 hover:text-cyan-400 rounded-2xl transition-all group"
                            >
                                <div className="w-8 h-8 rounded-xl bg-white/5 flex items-center justify-center group-hover:bg-cyan-500/20 group-hover:text-cyan-400 transition-all">
                                    <Map size={14} /> 
                                </div>
                                Copy Substance
                            </button>

                            <button 
                                onClick={() => {
                                    copyToClipboard(`${contextMenu.coords.x}, ${contextMenu.coords.y}`);
                                    setContextMenu(null);
                                }}
                                className="w-full flex items-center gap-4 px-4 py-3 text-xs font-bold text-slate-300 hover:bg-white/5 hover:text-cyan-400 rounded-2xl transition-all group"
                            >
                                <div className="w-8 h-8 rounded-xl bg-white/5 flex items-center justify-center group-hover:bg-cyan-500/20 group-hover:text-cyan-400 transition-all">
                                    <Database size={14} /> 
                                </div>
                                Copy Vector
                            </button>

                            <button 
                                onClick={() => {
                                    dispatchTeleport("self", contextMenu.coords.x, contextMenu.coords.y);
                                    setContextMenu(null);
                                }}
                                className="w-full flex items-center gap-4 px-4 py-4 text-xs font-black text-white hover:bg-cyan-500 rounded-2xl transition-all group shadow-xl hover:shadow-cyan-500/20"
                            >
                                <Zap size={14} className="fill-current" /> Teleport Here
                            </button>
                            
                            <button 
                                onClick={() => setContextMenu(null)}
                                className="w-full flex items-center justify-center py-3 text-[9px] font-black text-slate-600 hover:text-white uppercase tracking-widest transition-colors"
                            >
                                Dismiss
                            </button>
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* Lense Overlay (Floating Coordinates) */}
                <div className="absolute bottom-10 left-10 flex flex-col gap-1 pointer-events-none">
                    <div className="bg-slate-900/90 backdrop-blur-xl border border-white/10 px-6 py-4 rounded-2xl flex flex-col gap-2 shadow-2xl">
                        <div className="flex items-center justify-between gap-8">
                            <span className="text-[10px] font-black text-slate-500 uppercase tracking-[0.3em]">Temporal Vector</span>
                            <span className="text-xs font-mono font-bold text-cyan-400">
                                {hoveredCell?.x ?? 0} , {hoveredCell?.y ?? 0}
                            </span>
                        </div>
                        <div className="flex items-center justify-between gap-8">
                            <span className="text-[10px] font-black text-slate-500 uppercase tracking-[0.3em]">Substance</span>
                            <span className="text-xs font-black uppercase italic text-white flex items-center gap-2">
                            <div className="h-1.5 w-1.5 rounded-full bg-cyan-500" />
                            {hoveredCell?.terrain || 'void'}
                            </span>
                        </div>
                    </div>
                </div>
             </>
           ) : (
             <div className="absolute inset-0 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm z-[60]">
                <motion.div 
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="max-w-2xl w-full p-1 bg-gradient-to-br from-cyan-500/20 to-transparent rounded-[2.5rem] border border-white/10"
                >
                    <div className="bg-slate-900 rounded-[2.4rem] p-12 flex flex-col items-center text-center space-y-8">
                        <div className="space-y-3">
                            <h2 className="text-4xl font-black text-white italic tracking-tighter uppercase leading-none">
                                Initialize <span className="text-cyan-500">Shard</span>
                            </h2>
                            <p className="text-slate-500 font-medium italic">Select a world-data stream to begin sculpting the verse.</p>
                        </div>

                        <div className="w-full grid grid-cols-2 gap-4 max-h-[40vh] overflow-y-auto px-2 custom-scrollbar">
                            {zones.map(z => (
                                <button
                                    key={z}
                                    onClick={() => loadZone(z)}
                                    className="group relative flex flex-col items-start gap-1 p-6 rounded-3xl bg-white/5 border border-white/5 hover:border-cyan-500/50 hover:bg-cyan-500/5 transition-all text-left overflow-hidden"
                                >
                                    <Database size={40} className="absolute -right-4 -bottom-4 text-cyan-500/10 group-hover:text-cyan-500/20 transition-colors" />
                                    <span className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Shard.v4</span>
                                    <span className="text-lg font-bold text-slate-200 group-hover:text-cyan-400 transition-colors uppercase truncate w-full">
                                        {z.replace(/_/g, ' ')}
                                    </span>
                                </button>
                            ))}
                        </div>

                        <button 
                            onClick={createZone}
                            className="w-full py-5 rounded-3xl border border-dashed border-white/10 text-slate-600 hover:text-cyan-500 hover:border-cyan-500/50 transition-all font-black uppercase text-[10px] tracking-[0.4em]"
                        >
                            + Manifest New Uncharted Expanse
                        </button>
                    </div>
                </motion.div>
             </div>
           )}

           {/* In-Canvas HUD */}
           {activeZone && (
             <div className="absolute top-10 left-10 pointer-events-none">
                <div className="flex flex-col gap-1">
                   <span className="text-5xl font-black text-white/[0.03] italic uppercase select-none tracking-tighter">
                      {activeZone}
                   </span>
                   <div className="flex items-center gap-6 bg-slate-900/80 backdrop-blur-xl border border-white/5 px-6 py-3 rounded-2xl pointer-events-auto shadow-2xl mt-4">
                      <div className="flex flex-col">
                         <span className="text-[8px] font-bold text-slate-600 uppercase tracking-widest">Depth Index</span>
                         <span className="text-xs font-black text-cyan-500 uppercase">Z: {currentZ}</span>
                      </div>
                      <div className="h-6 w-px bg-white/5" />
                      <div className="flex flex-col">
                         <span className="text-[8px] font-bold text-slate-600 uppercase tracking-widest">Entities</span>
                         <span className="text-xs font-black text-cyan-500 uppercase">{rooms.length} Units</span>
                      </div>
                      <div className="h-6 w-px bg-white/5" />
                      <div className="flex flex-col">
                         <span className="text-[8px] font-bold text-slate-600 uppercase tracking-widest">Bridge</span>
                         <span className="text-xs font-black text-green-500 uppercase tracking-widest animate-pulse">Stable</span>
                      </div>
                   </div>
                </div>
             </div>
           )}
        </section>

        {/* Right Details Panel (Inspector / Palette) */}
        <AnimatePresence mode="wait">
            {brushMode === 'paint' && (
                <motion.aside
                    key="palette"
                    initial={{ x: 400, opacity: 0 }}
                    animate={{ x: 0, opacity: 1 }}
                    exit={{ x: 400, opacity: 0 }}
                    className="w-96 border-l border-white/10 bg-slate-950/80 backdrop-blur-2xl p-10 z-30 flex flex-col gap-10 scrollbar-hide"
                >
                    <header className="space-y-1">
                        <h3 className="text-[10px] font-black text-cyan-500 uppercase tracking-[0.3em] flex items-center gap-2 italic">
                            <Map size={12} /> Resource Library
                        </h3>
                        <div className="text-3xl font-black text-white uppercase italic tracking-tighter">Terrain Matrix</div>
                    </header>

                    <div className="flex-1 overflow-y-auto px-1 custom-scrollbar">
                        <div className="grid grid-cols-2 gap-3 pb-10">
                            {terrainList.map(t => (
                                <button
                                    key={t}
                                    onClick={() => setActiveTerrain(t)}
                                    className={clsx(
                                        "relative group flex flex-col items-center justify-center p-5 rounded-3xl border transition-all overflow-hidden",
                                        activeTerrain === t 
                                            ? "bg-cyan-500 border-cyan-400 text-white shadow-[0_0_20px_rgba(6,182,212,0.3)]" 
                                            : "bg-white/5 border-white/5 text-slate-500 hover:border-white/20 hover:text-slate-300"
                                    )}
                                >
                                    <span className="relative z-10 text-[9px] font-black uppercase tracking-widest text-center leading-tight">
                                        {t.replace(/_/g, ' ')}
                                    </span>
                                    {activeTerrain === t && (
                                        <motion.div layoutId="t-active" className="absolute inset-0 bg-gradient-to-br from-white/20 to-transparent" />
                                    )}
                                </button>
                            ))}
                        </div>
                    </div>
                </motion.aside>
            )}

            {selectedRoom && brushMode === 'select' && (
                <motion.aside
                    key="inspector"
                    initial={{ x: 400, opacity: 0 }}
                    animate={{ x: 0, opacity: 1 }}
                    exit={{ x: 400, opacity: 0 }}
                    className="w-96 border-l border-white/10 bg-slate-900 p-10 z-30 flex flex-col gap-10 shadow-[-20px_0_60px_rgba(0,0,0,0.5)]"
                >
                    <div className="space-y-2">
                        <div className="flex justify-between items-center text-cyan-500">
                            <span className="text-[10px] font-black uppercase tracking-[0.3em] flex items-center gap-2 italic">
                                <Info size={12} /> {selectedRooms.length > 1 ? `Bulk Probe (${selectedRooms.length})` : 'Entity Probe'}
                            </span>
                            <button onClick={() => { setSelectedRoom(null); setSelectedRooms([]); }} className="text-slate-500 hover:text-white transition-colors">
                                <X size={16} />
                            </button>
                        </div>
                        <h3 className="text-4xl font-black text-white uppercase italic tracking-tighter leading-none truncate pr-4">
                            {selectedRooms.length > 1 ? 'Multiple Units' : selectedRoom.name}
                        </h3>
                    </div>

                    <div className="space-y-8 flex-1 overflow-y-auto custom-scrollbar pr-2">
                        <div className="space-y-3">
                            <label className="text-[10px] text-slate-600 uppercase font-black tracking-widest">Metadata Identity</label>
                            <input 
                                className="w-full bg-black/40 p-5 rounded-3xl border border-white/5 text-white font-bold uppercase italic tracking-tight focus:outline-none focus:border-cyan-500/50 transition-all"
                                value={selectedRooms.length > 1 ? "" : selectedRoom.name}
                                placeholder={selectedRooms.length > 1 ? "Update multiple units..." : "Identity"}
                                onChange={(e) => {
                                    const val = e.target.value;
                                    if (selectedRooms.length > 1) handleBulkUpdate('name', val);
                                    else {
                                        setSelectedRoom({ ...selectedRoom, name: val });
                                        setRooms(prev => prev.map(r => (r.x === selectedRoom.x && r.y === selectedRoom.y && r.z === currentZ) ? { ...r, name: val } : r));
                                        axios.post('/api/update-room', { ...selectedRoom, name: val });
                                    }
                                }}
                            />
                        </div>

                        <div className="space-y-3">
                            <label className="text-[10px] text-slate-600 uppercase font-black tracking-widest">Atmosphere / Lore</label>
                            <textarea 
                                className="w-full h-32 bg-black/40 p-5 rounded-3xl border border-white/5 text-slate-400 text-xs focus:outline-none focus:border-cyan-500/50 transition-all resize-none custom-scrollbar"
                                value={selectedRooms.length > 1 ? "" : selectedRoom.description || ""}
                                onChange={(e) => {
                                    const val = e.target.value;
                                    if (selectedRooms.length > 1) handleBulkUpdate('description', val);
                                    else {
                                        setSelectedRoom({ ...selectedRoom, description: val });
                                        setRooms(prev => prev.map(r => (r.x === selectedRoom.x && r.y === selectedRoom.y && r.z === currentZ) ? { ...r, description: val } : r));
                                        axios.post('/api/update-room', { ...selectedRoom, description: val });
                                    }
                                }}
                                placeholder={selectedRooms.length > 1 ? "Update lore for selections..." : "A vast stretch of untamed wilderness..."}
                            />
                        </div>

                        <div className="space-y-3">
                             <div className="flex justify-between items-center">
                                <label className="text-[10px] text-slate-600 uppercase font-black tracking-widest">Substance Profile</label>
                                <span className="text-[9px] font-mono text-cyan-500 uppercase">{selectedRoom.terrain}</span>
                             </div>
                            
                            <div className="grid grid-cols-4 gap-2">
                                {['plains', 'forest', 'mountain', 'water'].map(t => (
                                    <button 
                                        key={t}
                                        onClick={() => {
                                            const updated = { ...selectedRoom, terrain: t };
                                            setSelectedRoom(updated);
                                            setRooms(prev => prev.map(r => (r.x === selectedRoom.x && r.y === selectedRoom.y && r.z === currentZ) ? { ...r, terrain: t } : r));
                                            axios.post('/api/update-room', updated);
                                        }}
                                        className={clsx(
                                            "aspect-square rounded-2xl border transition-all flex items-center justify-center text-[8px] font-black uppercase",
                                            selectedRoom.terrain === t ? "bg-cyan-500 border-cyan-400 text-white" : "bg-white/5 border-white/5 text-slate-500 hover:border-slate-700"
                                        )}
                                    >
                                        {t.slice(0, 3)}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className="pt-4 flex gap-3">
                            <button 
                                onClick={() => copyToClipboard(`${selectedRoom.x}, ${selectedRoom.y}`)}
                                className="flex-1 py-4 bg-white/5 hover:bg-white/10 text-slate-300 border border-white/5 rounded-2xl transition-all font-black uppercase text-[10px] tracking-widest flex items-center justify-center gap-2"
                            >
                                <Database size={14} /> Link Vector
                            </button>
                            <button 
                                onClick={() => dispatchTeleport("self", selectedRoom.x, selectedRoom.y)}
                                className="flex-1 py-4 bg-cyan-500 hover:bg-cyan-400 text-white rounded-2xl transition-all font-black uppercase text-[10px] tracking-widest flex items-center justify-center gap-2 shadow-xl shadow-cyan-500/20"
                            >
                                <Zap size={14} className="fill-current" /> Manifest
                            </button>
                        </div>
                    </div>

                    <footer className="pt-8 border-t border-white/5">
                        <div className="bg-slate-950 p-4 rounded-2xl border border-white/5">
                            <div className="flex items-center gap-3 text-cyan-500/50">
                                <Zap size={12} />
                                <span className="text-[9px] font-bold uppercase tracking-widest">Shard Integrity: 100%</span>
                            </div>
                        </div>
                    </footer>
                </motion.aside>
            )}
        </AnimatePresence>

        {/* Player List Sidebar */}
        <AnimatePresence>
            {showPlayerList && (
                <motion.aside
                    initial={{ x: 400, opacity: 0 }}
                    animate={{ x: 0, opacity: 1 }}
                    exit={{ x: 400, opacity: 0 }}
                    className="w-80 border-l border-white/5 bg-slate-950/90 backdrop-blur-3xl p-8 z-40 flex flex-col gap-8 shadow-[-20px_0_40px_rgba(0,0,0,0.4)]"
                >
                    <header className="flex items-center justify-between">
                        <div className="flex flex-col">
                            <span className="text-[9px] font-black text-purple-500 uppercase tracking-widest">Divine Monitoring</span>
                            <h3 className="text-xl font-black text-white italic uppercase tracking-tighter">Active Souls</h3>
                        </div>
                        <button 
                            onClick={() => loadPlayers()} 
                            className="p-2 rounded-lg hover:bg-white/5 text-slate-500 hover:text-white transition-colors"
                        >
                            <Zap size={16} />
                        </button>
                    </header>

                    <div className="flex-1 overflow-y-auto custom-scrollbar flex flex-col gap-3">
                        {players.length === 0 ? (
                            <div className="flex flex-col items-center justify-center h-40 opacity-20">
                                <Users size={32} />
                                <span className="text-[10px] uppercase font-bold tracking-widest mt-4">No mortals detected</span>
                            </div>
                        ) : (
                            players.map(p => (
                                <button
                                    key={p.name}
                                    onClick={() => {
                                        setCurrentZ(p.z);
                                        setCenterRequest({ x: p.x, y: p.y });
                                        // Reset request after a frame to allow repeated clicks
                                        setTimeout(() => setCenterRequest(null), 100);
                                    }}
                                    className="group flex items-center justify-between p-4 rounded-2xl bg-white/5 border border-white/5 hover:border-purple-500/50 hover:bg-purple-500/5 transition-all text-left"
                                >
                                    <div className="flex flex-col">
                                        <span className="text-sm font-bold text-white group-hover:text-purple-400 transition-colors uppercase italic">{p.name}</span>
                                        <span className="text-[9px] font-bold text-slate-500 uppercase tracking-tight">{p.class}</span>
                                    </div>
                                    <div className="flex flex-col items-end">
                                        <span className="text-[8px] font-black text-slate-600 uppercase">Vector</span>
                                        <span className="text-[10px] font-mono font-bold text-purple-500">{p.x},{p.y}</span>
                                    </div>
                                </button>
                            ))
                        )}
                    </div>
                </motion.aside>
            )}
        </AnimatePresence>
      </main>

      {/* Persistence Loading Overlay */}
      {isLoading && (
        <div className="absolute inset-0 bg-slate-950/80 z-[100] flex items-center justify-center backdrop-blur-xl">
           <div className="flex flex-col items-center gap-6">
              <div className="relative h-20 w-20">
                <div className="absolute inset-0 border-2 border-cyan-500/10 rounded-full" />
                <div className="absolute inset-0 border-t-2 border-cyan-500 rounded-full animate-spin" />
              </div>
              <div className="flex flex-col items-center gap-1">
                 <div className="text-white text-xl font-black uppercase italic tracking-tighter">Syncing Shard Matrix</div>
                 <div className="text-cyan-500/60 text-[10px] font-bold uppercase tracking-[0.4em] animate-pulse">Establishing Logic Bridge...</div>
              </div>
           </div>
        </div>
      )}
    </div>
  );
}
