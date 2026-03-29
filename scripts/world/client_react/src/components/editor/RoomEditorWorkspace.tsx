import React, { useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';
import {
    Dna, Box, Palette as PaletteIcon, Settings,
    Map as MapIcon, ChevronRight, Database,
    Plus, X, Zap, Layers, Compass, Save
} from 'lucide-react';
import { useStore } from '../../store/useStore';
import { motion, AnimatePresence } from 'framer-motion';
import { clsx } from 'clsx';

const TILE_SIZE = 32;
const GRID_SIZE = 50;

export default function EditorWorkspace() {
    const { setWorkspace } = useStore();
    const [metadata, setMetadata] = useState<any>({
        id: "new_zone", name: "New Uncharted Expanse", security_level: "mortal", grid_logic: true, target_cr: 1
    });
    const [rooms, setRooms] = useState<Record<string, any>>({});
    const [selectedPos, setSelectedPos] = useState<{ x: number, y: number } | null>(null);
    const [currentZ, setCurrentZ] = useState(0);
    const [activeTool, setActiveTool] = useState<string>("select");
    const [activeTemplate, setActiveTemplate] = useState<any>({
        name: "New Room", description: "Obsidian Chamber", terrain: "indoors", tags: []
    });

    const [mobs, setMobs] = useState<any[]>([]);
    const [terrain, setTerrain] = useState<any>({ terrains: [], elevations: {} });
    const [pan, setPan] = useState({ x: 0, y: 0 });
    const [zoom, setZoom] = useState(1);
    const [isPanning, setIsPanning] = useState(false);
    const [isPainting, setIsPainting] = useState(false);
    const [hoverPos, setHoverPos] = useState<{ x: number, y: number } | null>(null);
    const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved'>('idle');

    const canvasRef = useRef<HTMLCanvasElement>(null);
    const startPanRef = useRef({ x: 0, y: 0 });
    const startMouseRef = useRef({ x: 0, y: 0 });

    const getRoomKey = (x: number, y: number, z: number) => `${x}.${y}.${z}`;

    // Load Metadata & Assets
    useEffect(() => {
        const init = async () => {
            try {
                const [mRes, tRes] = await Promise.all([
                    axios.get('/api/mobs'),
                    axios.get('/api/assets')
                ]);
                setMobs(mRes.data);
                setTerrain(tRes.data);
            } catch (e) {
                console.error("Editor API offline", e);
            }
        };
        init();
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

        // Smooth Grid
        const startX = -GRID_SIZE / 2, startY = -GRID_SIZE / 2;
        ctx.lineWidth = 1 / zoom;
        for (let i = 0; i <= GRID_SIZE; i++) {
            const isMajor = i % 10 === 0;
            ctx.strokeStyle = isMajor ? "rgba(6, 182, 212, 0.2)" : "rgba(255,255,255,0.03)";

            ctx.beginPath();
            ctx.moveTo(startX * TILE_SIZE + i * TILE_SIZE, startY * TILE_SIZE);
            ctx.lineTo(startX * TILE_SIZE + i * TILE_SIZE, (startY + GRID_SIZE) * TILE_SIZE);
            ctx.stroke();

            ctx.beginPath();
            ctx.moveTo(startX * TILE_SIZE, startY * TILE_SIZE + i * TILE_SIZE);
            ctx.lineTo((startX + GRID_SIZE) * TILE_SIZE, startY * TILE_SIZE + i * TILE_SIZE);
            ctx.stroke();
        }

        // Rooms (Static Shard View)
        Object.values(rooms).forEach(r => {
            if (r.z === currentZ) {
                ctx.fillStyle = r.terrain === "forest" ? "rgba(34, 197, 94, 0.4)" :
                    r.terrain === "mountain" ? "rgba(100, 116, 139, 0.5)" :
                        "rgba(30, 41, 59, 0.6)";
                ctx.fillRect(r.x * TILE_SIZE, r.y * TILE_SIZE, TILE_SIZE, TILE_SIZE);
                ctx.strokeStyle = "rgba(255,255,255,0.1)";
                ctx.strokeRect(r.x * TILE_SIZE, r.y * TILE_SIZE, TILE_SIZE, TILE_SIZE);
            }
        });

        // Selection & Brushes
        if (selectedPos) {
            ctx.lineWidth = 2 / zoom;
            ctx.strokeStyle = "#06b6d4";
            ctx.strokeRect(selectedPos.x * TILE_SIZE, selectedPos.y * TILE_SIZE, TILE_SIZE, TILE_SIZE);
            ctx.fillStyle = "rgba(6, 182, 212, 0.1)";
            ctx.fillRect(selectedPos.x * TILE_SIZE, selectedPos.y * TILE_SIZE, TILE_SIZE, TILE_SIZE);
        }

        if (hoverPos && (activeTool === "paint" || activeTool === "erase")) {
            ctx.fillStyle = activeTool === "erase" ? "rgba(239, 68, 68, 0.2)" : "rgba(6, 182, 212, 0.2)";
            ctx.fillRect(hoverPos.x * TILE_SIZE, hoverPos.y * TILE_SIZE, TILE_SIZE, TILE_SIZE);
            ctx.strokeStyle = activeTool === "erase" ? "#ef4444" : "#06b6d4";
            ctx.setLineDash([4, 4]);
            ctx.strokeRect(hoverPos.x * TILE_SIZE, hoverPos.y * TILE_SIZE, TILE_SIZE, TILE_SIZE);
            ctx.setLineDash([]);
        }

        ctx.restore();
    }, [rooms, currentZ, selectedPos, hoverPos, activeTool, zoom, pan]);

    useEffect(() => {
        draw();
        const handleResize = () => {
            if (canvasRef.current) {
                canvasRef.current.width = canvasRef.current.parentElement?.clientWidth || 0;
                canvasRef.current.height = canvasRef.current.parentElement?.clientHeight || 0;
                draw();
            }
        };
        window.addEventListener('resize', handleResize);
        handleResize();
        return () => window.removeEventListener('resize', handleResize);
    }, [draw]);

    const onMouseDown = (e: React.MouseEvent) => {
        startMouseRef.current = { x: e.clientX, y: e.clientY };
        startPanRef.current = { ...pan };

        if (e.button === 1 || e.button === 2) {
            setIsPanning(true);
            return;
        }

        const rect = canvasRef.current?.getBoundingClientRect(); if (!rect) return;
        const gx = Math.floor(((e.clientX - rect.left - rect.width / 2 - pan.x) / zoom) / TILE_SIZE);
        const gy = Math.floor(((e.clientY - rect.top - rect.height / 2 - pan.y) / zoom) / TILE_SIZE);

        if (activeTool === "paint") {
            setIsPainting(true);
            const key = getRoomKey(gx, gy, currentZ);
            setRooms(prev => ({ ...prev, [key]: { ...activeTemplate, id: `${metadata.id}.${gx}.${gy}.${currentZ}`, zone_id: metadata.id, x: gx, y: gy, z: currentZ } }));
        } else if (activeTool === "erase") {
            const key = getRoomKey(gx, gy, currentZ);
            setRooms(prev => { const n = { ...prev }; delete n[key]; return n; });
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

        const gx = Math.floor(((e.clientX - rect.left - rect.width / 2 - pan.x) / zoom) / TILE_SIZE);
        const gy = Math.floor(((e.clientY - rect.top - rect.height / 2 - pan.y) / zoom) / TILE_SIZE);
        setHoverPos({ x: gx, y: gy });

        if (isPainting && activeTool === "paint" && !isPanning) {
            const key = getRoomKey(gx, gy, currentZ);
            if (!rooms[key]) {
                setRooms(prev => ({ ...prev, [key]: { ...activeTemplate, id: `${metadata.id}.${gx}.${gy}.${currentZ}`, zone_id: metadata.id, x: gx, y: gy, z: currentZ } }));
            }
        }
    };

    const saveShard = async () => {
        setSaveStatus('saving');
        try {
            // [V8.9 Monolith Sync]
            const roomArray = Object.values(rooms);
            await axios.post('/api/manifest-shard', {
                metadata,
                rooms: roomArray
            });
            setSaveStatus('saved');
            setTimeout(() => setSaveStatus('idle'), 3000);
        } catch (e) {
            alert("Failed to manifest shard");
            setSaveStatus('idle');
        }
    };

    return (
        <div className="absolute inset-0 bg-slate-950 flex flex-col overflow-hidden animate-in fade-in duration-500 z-[100] font-display">
            {/* Monolith Header */}
            <header className="h-16 border-b border-white/5 bg-slate-900/40 backdrop-blur-xl flex items-center justify-between px-8 z-50">
                <div className="flex items-center gap-8">
                    <div className="flex items-center gap-3">
                        <div className="h-2 w-2 rounded-full bg-purple-500 animate-pulse shadow-[0_0_10px_#a855f7]" />
                        <h1 className="font-black tracking-tighter text-white text-xl italic uppercase">
                            Area<span className="text-purple-500">Editor</span>
                        </h1>
                    </div>

                    <div className="h-6 w-px bg-white/10" />

                    <nav className="flex items-center gap-6">
                        <div className="flex items-center gap-2">
                            <Database size={14} className="text-purple-400" />
                            <span className="text-[11px] font-black uppercase tracking-widest text-slate-300">
                                {metadata.name}
                            </span>
                        </div>

                        <div className="flex items-center gap-3 bg-white/5 px-4 py-1.5 rounded-full border border-white/5">
                            <Layers size={13} className="text-purple-500" />
                            <span className="text-[10px] font-black uppercase text-slate-500 tracking-tighter">Plane Index</span>
                            <div className="flex items-center gap-3 ml-2">
                                <button onClick={() => setCurrentZ(z => z - 1)} className="hover:text-purple-400 text-xs">▼</button>
                                <span className="w-4 text-center font-mono text-purple-400 font-bold">{currentZ}</span>
                                <button onClick={() => setCurrentZ(z => z + 1)} className="hover:text-purple-400 text-xs">▲</button>
                            </div>
                        </div>
                    </nav>
                </div>

                <div className="flex items-center gap-6">
                    <button
                        onClick={saveShard}
                        disabled={saveStatus === 'saving'}
                        className={clsx(
                            "flex items-center gap-2 px-8 py-2.5 rounded-lg transition-all font-black text-[10px] uppercase tracking-[0.2em]",
                            saveStatus === 'saved' ? "bg-green-500 text-white shadow-[0_0_20px_rgba(34,197,94,0.3)]" :
                                saveStatus === 'saving' ? "bg-slate-800 text-slate-500" :
                                    "bg-purple-600 hover:bg-purple-500 text-white shadow-[0_0_20px_rgba(168,85,247,0.3)]"
                        )}
                    >
                        <Save size={14} />
                        {saveStatus === 'saved' ? 'MANIFESTED' : saveStatus === 'saving' ? 'WRITING...' : 'MANIFEST SHARD'}
                    </button>

                    <div className="h-6 w-px bg-white/10" />

                    <button
                        onClick={() => setWorkspace('game')}
                        className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-white/5 transition-all text-[10px] font-black uppercase tracking-widest"
                    >
                        <Compass size={14} />
                        Return
                    </button>
                </div>
            </header>

            <main className="flex-1 flex overflow-hidden">
                {/* Toolbelt */}
                <aside className="w-20 border-r border-white/5 bg-slate-900/20 backdrop-blur-xl flex flex-col items-center py-10 gap-8">
                    <button
                        onClick={() => setActiveTool('select')}
                        className={clsx(
                            "p-4 rounded-2xl transition-all border",
                            activeTool === 'select' ? "bg-purple-500 text-white border-purple-400" : "text-slate-500 border-transparent hover:bg-white/5"
                        )}
                    >
                        <Compass size={22} />
                    </button>

                    <button
                        onClick={() => setActiveTool('paint')}
                        className={clsx(
                            "p-4 rounded-2xl transition-all border",
                            activeTool === 'paint' ? "bg-purple-500 text-white border-purple-400" : "text-slate-500 border-transparent hover:bg-white/5"
                        )}
                    >
                        <Box size={22} />
                    </button>

                    <button
                        onClick={() => setActiveTool('erase')}
                        className={clsx(
                            "p-4 rounded-2xl transition-all border",
                            activeTool === 'erase' ? "bg-red-500 text-white border-red-400" : "text-slate-500 border-transparent hover:bg-white/5"
                        )}
                    >
                        <X size={22} />
                    </button>
                </aside>

                {/* Canvas Viewport */}
                <section className="flex-1 bg-slate-950 relative overflow-hidden">
                    <canvas
                        ref={canvasRef}
                        onMouseDown={onMouseDown}
                        onMouseMove={onMouseMove}
                        onMouseUp={() => { setIsPanning(false); setIsPainting(false); }}
                        onContextMenu={(e) => e.preventDefault()}
                        onWheel={(e) => setZoom(z => Math.max(0.2, Math.min(5, z * (e.deltaY > 0 ? 0.9 : 1.1))))}
                        className="w-full h-full cursor-crosshair"
                    />

                    <div className="absolute bottom-10 left-10 pointer-events-none">
                        <div className="bg-slate-900/90 backdrop-blur-xl border border-white/10 px-6 py-4 rounded-2xl flex flex-col gap-2 shadow-2xl">
                            <div className="flex items-center gap-4">
                                <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Vector</span>
                                <span className="text-xs font-mono font-bold text-purple-400">{hoverPos?.x ?? 0}, {hoverPos?.y ?? 0}</span>
                            </div>
                        </div>
                    </div>
                </section>

                {/* Inspector Panel */}
                <aside className="w-96 border-l border-white/5 bg-slate-900/40 backdrop-blur-2xl p-10 flex flex-col gap-10">
                    {selectedPos ? (
                        <>
                            <div className="space-y-2">
                                <h3 className="text-[10px] font-black text-purple-500 uppercase tracking-[0.3em] italic">Entity Probe</h3>
                                <div className="text-3xl font-black text-white italic uppercase tracking-tighter">
                                    {rooms[getRoomKey(selectedPos.x, selectedPos.y, currentZ)]?.name || "Space Gap"}
                                </div>
                            </div>

                            <div className="space-y-6">
                                <div className="space-y-2">
                                    <label className="text-[10px] text-slate-500 uppercase font-black tracking-widest">Designation</label>
                                    <input
                                        className="w-full bg-black/40 p-4 rounded-2xl border border-white/5 text-white font-bold"
                                        value={rooms[getRoomKey(selectedPos.x, selectedPos.y, currentZ)]?.name || ""}
                                        onChange={(e) => {
                                            const key = getRoomKey(selectedPos.x, selectedPos.y, currentZ);
                                            setRooms(prev => ({
                                                ...prev,
                                                [key]: { ...prev[key], name: e.target.value }
                                            }));
                                        }}
                                    />
                                </div>

                                <div className="space-y-2">
                                    <label className="text-[10px] text-slate-500 uppercase font-black tracking-widest">Atmosphere</label>
                                    <textarea
                                        className="w-full h-32 bg-black/40 p-4 rounded-2xl border border-white/5 text-slate-300 text-xs resize-none"
                                        value={rooms[getRoomKey(selectedPos.x, selectedPos.y, currentZ)]?.description || ""}
                                        onChange={(e) => {
                                            const key = getRoomKey(selectedPos.x, selectedPos.y, currentZ);
                                            setRooms(prev => ({
                                                ...prev,
                                                [key]: { ...prev[key], description: e.target.value }
                                            }));
                                        }}
                                    />
                                </div>
                            </div>
                        </>
                    ) : (
                        <div className="flex flex-col items-center justify-center h-full text-center opacity-30 gap-4">
                            <Dna size={48} className="text-purple-500" />
                            <span className="text-[10px] font-black uppercase tracking-[0.4em]">Initialize Probe Selection</span>
                        </div>
                    )}
                </aside>
            </main>
        </div>
    );
}
