import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Layers, Save, FolderOpen, MousePointer2, Paintbrush2, Info, Compass } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import RemoteCanvas from './RemoteCanvas';

const API_BASE = 'http://localhost:8000/api';

const App = () => {
  const [zones, setZones] = useState<string[]>([]);
  const [activeZone, setActiveZone] = useState<string | null>(null);
  const [rooms, setRooms] = useState<any[]>([]);
  const [selectedRoom, setSelectedRoom] = useState<any | null>(null);
  const [brushMode, setBrushMode] = useState<'select' | 'paint'>('select');
  const [activeTerrain, setActiveTerrain] = useState('plains');
  const [terrainList, setTerrainList] = useState<string[]>([]);
  const [elevations, setElevations] = useState<Record<string, number>>({});
  const [brushSize, setBrushSize] = useState(1);
  const [currentZ, setCurrentZ] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState('connecting...');
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved'>('idle');

  useEffect(() => {
    checkStatus();
    loadZoneList();
    loadAssets();
  }, []);

  const checkStatus = async () => {
    try {
      const resp = await axios.get(`${API_BASE}/status`);
      setStatus(resp.data.mode);
    } catch (e) {
      setStatus('OFFLINE');
    }
  };

  const loadZoneList = async () => {
    try {
      const resp = await axios.get(`${API_BASE}/zones`);
      setZones(resp.data.zones);
    } catch (e) {}
  };

  const loadAssets = async () => {
    try {
      const resp = await axios.get(`${API_BASE}/assets`);
      setTerrainList(resp.data.terrains);
      setElevations(resp.data.elevations);
    } catch (e) {}
  };

  const loadZone = async (zone_id: string) => {
    setIsLoading(true);
    try {
      await axios.get(`${API_BASE}/load/${zone_id}`);
      const mapResp = await axios.get(`${API_BASE}/map-data`);
      setRooms(mapResp.data.rooms);
      setActiveZone(zone_id);
      setSelectedRoom(null);
    } catch (e) {}
    setIsLoading(false);
  };

  const createZone = async () => {
    const name = prompt("Enter shard identifier:");
    if (!name) return;
    setIsLoading(true);
    try {
      await axios.post(`${API_BASE}/create`, { id: name });
      const mapResp = await axios.get(`${API_BASE}/map-data`);
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
      await axios.post(`${API_BASE}/save`);
      setSaveStatus('saved');
      setTimeout(() => setSaveStatus('idle'), 3000);
    } catch (e) {
      alert('Failed to save');
      setSaveStatus('idle');
    }
  };

  const handleCellClick = async (x: number, y: number) => {
    if (brushMode === 'paint') {
      try {
        const resp = await axios.post(`${API_BASE}/update-room`, {
          x, y, z: currentZ,
          terrain: activeTerrain
        });
        
        setRooms(prev => {
          const idx = prev.findIndex(r => r.x === x && r.y === y && r.z === currentZ);
          if (idx >= 0) {
            const next = [...prev];
            next[idx] = resp.data.room;
            return next;
          }
          return [...prev, resp.data.room];
        });
      } catch (e) {}
    }
  };

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden text-sm bg-[#040406] text-slate-300 font-sans">
      {/* Top Header */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-white/5 bg-black/40 backdrop-blur-xl z-50">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-3">
             <div className="h-2 w-2 rounded-full bg-cyan-500 animate-pulse shadow-[0_0_8px_#00bcd4]" />
             <h1 className="font-black tracking-tighter text-white text-xl italic uppercase">Remote<span className="text-cyan-500">Studio</span></h1>
          </div>
          <div className="h-6 w-px bg-white/10" />
          <nav className="flex items-center gap-4">
             <button 
                onClick={() => setActiveZone(null)} 
                className="text-xs font-bold text-slate-500 hover:text-cyan-400 transition-colors uppercase tracking-widest flex items-center gap-2"
             >
               <FolderOpen size={14} /> {activeZone || 'Select Shard'}
             </button>
             {activeZone && (
               <div className="flex items-center gap-2 bg-white/5 px-3 py-1 rounded-full border border-white/5">
                  <Layers size={12} className="text-cyan-500" />
                  <span className="text-[10px] font-black uppercase text-slate-400">Level</span>
                  <button onClick={() => setCurrentZ(z => z - 1)} className="hover:text-cyan-400">▼</button>
                  <span className="w-4 text-center font-mono text-cyan-400">{currentZ}</span>
                  <button onClick={() => setCurrentZ(z => z + 1)} className="hover:text-cyan-400">▲</button>
               </div>
             )}
          </nav>
        </div>
        
        <div className="flex gap-4">
          <div className="flex items-center gap-2 text-[10px] font-bold text-slate-500 uppercase tracking-tighter italic">
            Engine: <span className="text-cyan-500">{status}</span>
          </div>
          <button 
            onClick={saveZone} 
            disabled={saveStatus === 'saving'}
            className={`flex items-center gap-2 px-6 py-2 rounded-lg transition-all font-black text-xs uppercase tracking-widest ${
              saveStatus === 'saved' ? 'bg-green-600 text-white' : 
              saveStatus === 'saving' ? 'bg-slate-800 text-slate-500' : 
              'bg-cyan-600 hover:bg-cyan-500 text-white shadow-[0_0_20px_rgba(8,145,178,0.3)]'
            }`}
          >
            <Save size={16} /> {saveStatus === 'saved' ? 'SYNCED' : saveStatus === 'saving' ? 'WRITING...' : 'SAVE SHARD'}
          </button>
        </div>
      </header>

      <main className="flex flex-1 overflow-hidden relative">
        {/* Left Toolbar */}
        <div className="w-20 flex flex-col items-center py-8 gap-8 border-r border-white/5 bg-black/20 backdrop-blur-2xl z-20">
          <button 
            onClick={() => setBrushMode('select')}
            title="Entity Probe (V)"
            className={`p-4 rounded-2xl transition-all ${brushMode === 'select' ? 'bg-cyan-500 text-white shadow-[0_0_20px_rgba(6,182,212,0.4)]' : 'hover:bg-white/5 text-slate-500'}`}
          >
            <MousePointer2 size={24} />
          </button>
          <button 
            onClick={() => setBrushMode('paint')}
            title="Terrain Brush (B)"
            className={`p-4 rounded-2xl transition-all ${brushMode === 'paint' ? 'bg-cyan-500 text-white shadow-[0_0_20px_rgba(6,182,212,0.4)]' : 'hover:bg-white/5 text-slate-500'}`}
          >
            <Paintbrush2 size={24} />
          </button>
          <div className="h-px w-10 bg-white/5" />
          <button className="p-4 hover:bg-white/5 text-slate-500 rounded-2xl transition-all">
            <Layers size={24} />
          </button>
          <button className="p-4 hover:bg-white/5 text-slate-500 rounded-2xl transition-all">
            <Compass size={24} />
          </button>
          <div className="mt-auto mb-4 text-[8px] font-black text-slate-700 uppercase vertical-text tracking-[0.5em]">
            Godless Engine v8.0
          </div>
        </div>

        {/* Zone Selector Popover */}
        {!activeZone && (
          <div className="absolute inset-0 flex items-center justify-center bg-[#020203]/90 z-[60] backdrop-blur-3xl px-6">
             <motion.div 
                initial={{ opacity: 0, scale: 0.9, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                className="max-w-2xl w-full p-1 border border-white/10 rounded-[2rem] bg-gradient-to-b from-white/10 to-transparent shadow-2xl"
             >
                <div className="bg-[#0a0a0c] rounded-[1.9rem] p-10 space-y-8">
                    <div className="space-y-2 text-center">
                        <h2 className="text-4xl font-black text-white tracking-tighter uppercase italic leading-none">
                          Initialize <span className="text-cyan-500">Shard</span>
                        </h2>
                        <p className="text-slate-500 font-medium italic underline decoration-cyan-500/30 underline-offset-4">Select a world-data stream to begin sculpting.</p>
                    </div>

                    <div className="grid grid-cols-2 gap-3 max-h-[50vh] overflow-y-auto p-2 scrollbar-hide">
                    {zones.map(z => (
                        <button 
                        key={z} 
                        onClick={() => loadZone(z)}
                        className="text-left px-6 py-5 rounded-2xl bg-white/5 hover:bg-cyan-500/10 border border-white/5 hover:border-cyan-500/30 transition-all group relative overflow-hidden"
                        >
                        <div className="absolute top-0 right-0 p-4 opacity-0 group-hover:opacity-20 transition-opacity">
                            <FolderOpen size={40} className="text-cyan-400" />
                        </div>
                        <div className="flex flex-col gap-1 relative z-10">
                            <span className="text-slate-500 text-[10px] font-black uppercase tracking-widest leading-none">Zone.v4</span>
                            <span className="text-slate-200 group-hover:text-cyan-400 font-bold tracking-tight text-lg uppercase truncate">{z.replace(/_/g, ' ')}</span>
                        </div>
                        </button>
                    ))}
                    </div>
                    
                    <button 
                        onClick={createZone}
                        className="w-full py-4 border border-dashed border-white/10 rounded-2xl text-slate-600 font-black uppercase tracking-[0.3em] text-[10px] hover:border-cyan-500/50 hover:text-cyan-500 transition-all"
                    >
                        + Create New Uncharted Expanse
                    </button>
                </div>
             </motion.div>
          </div>
        )}

        {/* Main Canvas Area */}
        <div className="flex-1 bg-black relative">
          <RemoteCanvas 
            rooms={rooms.filter(r => r.z === currentZ)} 
            selectedRoom={selectedRoom} 
            onRoomSelect={setSelectedRoom}
            brushSize={brushSize}
            activeTerrain={activeTerrain}
            elevations={elevations}
            onCellClick={handleCellClick}
          />
          
          {/* Overlay Stats */}
          <div className="absolute top-8 left-8 pointer-events-none space-y-4">
             <div className="text-6xl font-black text-white/[0.03] uppercase select-none leading-none tracking-tighter italic">
               {activeZone || 'OFFLINE'}
             </div>
             <div className="flex items-center gap-6 text-[10px] font-black text-cyan-500 bg-[#0a0a0c]/80 px-6 py-3 rounded-2xl border border-white/5 backdrop-blur-xl pointer-events-auto shadow-2xl tracking-[0.2em] uppercase">
               <div className="flex flex-col">
                  <span className="text-slate-600 text-[8px] mb-1">Stability</span>
                  <span>FPS: 120</span>
               </div>
               <div className="h-6 w-px bg-white/5" />
               <div className="flex flex-col">
                  <span className="text-slate-600 text-[8px] mb-1">Entities</span>
                  <span>{rooms.length}</span>
               </div>
               <div className="h-6 w-px bg-white/5" />
               <div className="flex flex-col">
                  <span className="text-slate-600 text-[8px] mb-1">Depth Matrix</span>
                  <span>Z: {currentZ}</span>
               </div>
             </div>
          </div>

          <div className="absolute bottom-8 right-8 flex flex-col gap-4 pointer-events-auto">
             <div className="flex flex-col gap-2 bg-[#0a0a0c]/80 p-4 rounded-2xl border border-white/5 backdrop-blur-xl shadow-2xl">
                <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest italic border-b border-white/5 pb-2 mb-2">Controls</span>
                <div className="flex items-center gap-4 text-xs font-medium">
                   <span className="flex items-center gap-2"><kbd className="bg-white/10 px-2 py-0.5 rounded border border-white/10 text-[10px]">SHIFT</kbd> Pan</span>
                   <span className="flex items-center gap-2"><kbd className="bg-white/10 px-2 py-0.5 rounded border border-white/10 text-[10px]">SCROLL</kbd> Zoom</span>
                </div>
             </div>
          </div>
        </div>

        {/* Right Panels (Sidebar) */}
        <AnimatePresence mode="wait">
          {brushMode === 'paint' && (
            <motion.div 
              key="palette"
              initial={{ x: 400, opacity: 0 }} 
              animate={{ x: 0, opacity: 1 }} 
              exit={{ x: 400, opacity: 0 }}
              className="w-96 border-l border-white/5 bg-[#0a0a0c]/80 backdrop-blur-3xl p-8 z-20 space-y-8 h-full overflow-y-auto shadow-[-20px_0_40px_rgba(0,0,0,0.5)]"
            >
              <section className="space-y-6">
                <div className="flex justify-between items-end">
                  <div className="space-y-1">
                    <h3 className="text-cyan-500 font-black uppercase tracking-[0.2em] text-[10px] flex items-center gap-2 italic">
                        <Paintbrush2 size={12} /> Asset Library
                    </h3>
                    <div className="text-2xl font-black text-white tracking-tighter uppercase italic">Terrain Matrix</div>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  {terrainList.map(t => (
                    <button 
                      key={t}
                      onClick={() => setActiveTerrain(t)}
                      className={`px-4 py-5 rounded-2xl flex flex-col items-center gap-3 transition-all border group relative overflow-hidden ${activeTerrain === t ? 'bg-cyan-500 border-cyan-400 text-white shadow-[0_0_20px_rgba(6,182,212,0.3)]' : 'bg-white/5 border-white/5 hover:border-white/10 text-slate-400 hover:text-slate-200'}`}
                    >
                      <span className="text-[9px] font-black uppercase tracking-[0.2em] relative z-10">{t.replace(/_/g, ' ')}</span>
                      {activeTerrain === t && <motion.div layoutId="terrain-active" className="absolute inset-0 bg-gradient-to-br from-white/20 to-transparent" />}
                    </button>
                  ))}
                </div>
              </section>
            </motion.div>
          )}

          {selectedRoom && (
            <motion.div 
               key="inspector"
               initial={{ x: 400, opacity: 0 }} 
               animate={{ x: 0, opacity: 1 }} 
               exit={{ x: 400, opacity: 0 }}
               className="w-96 border-l border-white/10 bg-[#0c0c0e] p-10 z-30 shadow-[-30px_0_60px_rgba(0,0,0,0.8)] space-y-10"
            >
              <div className="space-y-2">
                <div className="flex justify-between items-center text-cyan-500">
                  <span className="text-[10px] font-black uppercase tracking-[0.3em] flex items-center gap-2 italic">
                    <Info size={12} /> Entity Probe
                  </span>
                  <button onClick={() => setSelectedRoom(null)} className="text-slate-500 hover:text-white transition-colors">✕</button>
                </div>
                <h3 className="text-4xl font-black text-white uppercase italic tracking-tighter leading-none">{selectedRoom.name}</h3>
              </div>
              
              <div className="space-y-8">
                 <div className="space-y-3">
                   <label className="text-[10px] text-slate-600 uppercase font-black tracking-widest">Vector Coordinates</label>
                   <div className="bg-black p-4 rounded-2xl border border-white/5 group transition-colors hover:border-cyan-500/30">
                     <span className="font-mono text-cyan-500 font-bold text-lg">
                        X:{selectedRoom.x} <span className="opacity-20 mx-2">/</span> 
                        Y:{selectedRoom.y} <span className="opacity-20 mx-2">/</span> 
                        Z:{selectedRoom.z}
                     </span>
                   </div>
                 </div>

                 <div className="space-y-3">
                   <label className="text-[10px] text-slate-600 uppercase font-black tracking-widest">Substance Profile</label>
                   <div className="bg-white/5 p-5 rounded-2xl border border-white/5 flex items-center justify-between">
                     <span className="font-black text-slate-200 uppercase tracking-[0.2em] text-xs">
                       {selectedRoom.terrain}
                     </span>
                     <div className="h-4 w-4 rounded-full bg-cyan-500" style={{ backgroundColor: selectedRoom.terrain_color }} />
                   </div>
                 </div>
              </div>

              <div className="pt-10">
                <button className="w-full py-5 bg-red-950/20 text-red-500 border border-red-900/20 rounded-2xl font-black uppercase tracking-[0.3em] text-[10px] hover:bg-red-500 hover:text-white transition-all shadow-xl">
                  Deconstruct Entity
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>
      
      {isLoading && (
        <div className="absolute inset-0 bg-[#020203]/80 z-[100] flex items-center justify-center backdrop-blur-xl">
           <div className="flex flex-col items-center gap-6">
              <div className="relative">
                <div className="h-20 w-20 border-2 border-cyan-500/20 rounded-full" />
                <div className="h-20 w-20 border-t-2 border-cyan-500 rounded-full animate-spin absolute inset-0" />
              </div>
              <div className="flex flex-col items-center">
                 <div className="text-white text-xl font-black uppercase italic tracking-tighter">Syncing Engine</div>
                 <div className="text-cyan-500/60 text-[10px] font-bold uppercase tracking-[0.4em] animate-pulse">Establishing Logic Bridge...</div>
              </div>
           </div>
        </div>
      )}
    </div>
  );
};

export default App;
