import React, { useMemo, useState, useEffect, useRef } from 'react';
import { useStore } from '../store/useStore';
import { sendCommand } from '../lib/ges';
import { clsx } from 'clsx';
import { Layers, Info, Sun, Settings } from 'lucide-react';
import { motion } from 'framer-motion';
import { CombatTextOverlay } from './CombatTextOverlay';

interface ViewportProps {
   radius: number;
   context: 'mini' | 'tactical' | 'map';
   scale: number;
}

/**
 * [V10.4] Graduated Visibility & Projection Lock
 */
const Tile = React.memo(({ tile, tileSize, isTactical }: any) => {
    const { setSelectedTargetId } = useStore();
    const elev = tile.elevation || 0;
    const lift = isTactical ? -elev * 3 : 0;
    const isDiscovered = tile.visible;
    const isInLos = tile.in_los;
    const isHazy = tile.is_hazy;

    const monsters = tile.top_entities?.filter((e: any) => !e.is_player && !e.is_self && !e.is_ping) || [];
    const otherPlayers = tile.top_entities?.filter((e: any) => e.is_player && !e.is_self) || [];
    const isSelf = tile.top_entities?.some((e: any) => e.is_self);

    const tileStyle = useMemo(() => ({
       width: tileSize,
       height: tileSize,
       // [V11.7] High Contrast: LoS is Clear, Knowledge (FoW) is Solid Slate.
       backgroundColor: isDiscovered 
         ? (isInLos ? 'transparent' : 'rgba(15, 23, 42, 0.95)') 
         : 'transparent',
       transform: `translateY(${lift}px)`,
       boxShadow: isTactical && elev > 0 && isDiscovered 
         ? `0 ${elev * 2}px 10px rgba(0,0,0,0.5)` 
         : 'none',
    }), [tileSize, isDiscovered, isInLos, lift, isTactical, elev]);

    const handleTileActions = (e: React.MouseEvent) => {
        if (!isDiscovered || monsters.length === 0) return;
        
        if (e.type === 'click') {
           setSelectedTargetId(monsters[0].id);
        } else if (e.type === 'dblclick') {
           e.stopPropagation();
           sendCommand(`kill ${monsters[0].name}`);
        }
    };

    return (
       <div 
         onClick={handleTileActions}
         onDoubleClick={handleTileActions}
         className={clsx(
           "relative flex items-center justify-center transition-all duration-100", 
           isDiscovered ? "border-slate-800/10" : "opacity-0",
           isDiscovered && monsters.length > 0 ? "cursor-crosshair hover:bg-red-500/10" : ""
         )} 
         style={tileStyle}
       >
          {/* 1. Terrain Glyph */}
          <span className="text-base font-black transition-colors duration-100 shadow-sm" style={{ color: isDiscovered ? tile.color : 'transparent', filter: isHazy ? 'blur(0.5px) grayscale(0.5)' : 'none' }}>
             {isDiscovered ? (tile.char || '.') : '?'}
          </span>

          {/* 2. Entity Overlays */}
          {isDiscovered && (
              <div className="absolute inset-0 pointer-events-none z-30">
                 {monsters.length > 0 && (
                     <div className="absolute top-0.5 right-0.5">
                         <div className={clsx("w-2 h-2 rounded-full shadow-sm flex items-center justify-center border border-white/10", monsters[0].is_hostile ? "bg-red-500" : "bg-yellow-500")}>
                            <span className="text-[6px] font-black text-white">{monsters[0].symbol}</span>
                         </div>
                     </div>
                 )}
                 {otherPlayers.length > 0 && (
                     <div className="absolute top-0.5 left-0.5">
                         <div className="w-2 h-2 rounded-full bg-blue-500 border border-white/10 flex items-center justify-center">
                            <span className="text-[6px] font-black text-white">{otherPlayers[0].symbol}</span>
                         </div>
                     </div>
                 )}
                 {isSelf && (
                     <div className="absolute inset-0 flex items-center justify-center">
                        <div className="w-2.5 h-2.5 rounded-full border border-blue-400 bg-blue-400/40 animate-pulse" />
                     </div>
                 )}
                 {tile.has_pings && (tile.top_entities?.length || 0) === 0 && (
                     <div className="absolute bottom-0.5 right-0.5"><div className="w-1.5 h-1.5 rounded-full bg-yellow-500/40 animate-ping" /></div>
                 )}
              </div>
          )}

          {/* 3. Deep-Height Shading */}
          {isTactical && elev > 0 && isDiscovered && (
             <>
                <div className="absolute left-0 right-0 -bottom-[1px] bg-black/40 z-0 rounded-b-sm pointer-events-none" style={{ height: `${elev * 4}px` }} />
                <div className={clsx("absolute inset-x-0 top-0 h-[2px] z-40 pointer-events-none", elev > 5 ? "bg-white/40" : "bg-white/20")} />
             </>
          )}

          {/* [V10.4] Environmental Haze / Fog of Shadow */}
          {isHazy && isDiscovered && (
             <motion.div 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="absolute inset-0 bg-slate-900/60 backdrop-blur-[1px] z-20 pointer-events-none flex items-center justify-center"
             >
                <div className="w-full h-full bg-emerald-900/5 animate-pulse" style={{ animationDuration: '6s' }} />
             </motion.div>
          )}
       </div>
    );
});

export function Viewport({ radius, context, scale: propScale = 1 }: ViewportProps) {
  const { isConnected, tacticalMapData, showInfluence, setShowInfluence, combatNotifications } = useStore();
  const [userZoom, setUserZoom] = useState(1);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  
  const mapData = tacticalMapData;
  const isTactical = context === 'tactical';
  const tileSize = 54 * propScale * userZoom;

  const displayedGrid = useMemo(() => {
     if (!mapData || !mapData.grid) return [];
     const sr = mapData.radius;
     return mapData.grid
       .filter((row, yIdx) => Math.abs(yIdx - sr) <= radius)
       .map(row => row.filter((tile, xIdx) => Math.abs(xIdx - sr) <= radius));
  }, [mapData, radius]);

  const tiles = displayedGrid.flat();
  const columnCount = displayedGrid.length > 0 ? displayedGrid[0].length : 0;
  const gridPixelSize = columnCount * (tileSize + 2);

  const handleWheel = (e: React.WheelEvent) => {
    if (e.ctrlKey) return; 
    const delta = e.deltaY;
    // Smoother scaling with delta sensitivity
    setUserZoom(prev => Math.min(3.0, Math.max(0.1, prev - (delta * 0.001 * prev))));
  };

   if (!isConnected) {
      return (
         <div className="w-full h-full flex flex-col items-center justify-center bg-slate-900/40">
            <div className="w-12 h-12 border-2 border-dashed border-slate-700 animate-spin rounded-full" />
            <p className="mt-4 text-[10px] uppercase tracking-[0.2em] text-slate-500 animate-pulse">Establishing Divine Link...</p>
         </div>
      );
   }

   return (
     <div 
        onWheel={handleWheel}
        className="w-full h-full overflow-hidden relative bg-slate-950/20 perspective-1000 flex items-center justify-center"
     >
         
         {/* DIVINE MAP PROJECTION (Restored & Locked) */}
         <div 
           className="w-full h-full flex items-center justify-center pointer-events-none" 
           style={{ 
             transform: isTactical ? 'rotateX(25deg) rotateZ(-5deg)' : 'none',
             transformStyle: 'preserve-3d',
             perspectiveOrigin: 'center center'
           }}
         >
             {/* DRAGGABLE CANVAS HOOK (Pans INSIDE the tilted projection) */}
             <motion.div 
               drag
               dragElastic={0}
               dragMomentum={true}
               initial={false}
               className="relative cursor-grab active:cursor-grabbing pointer-events-auto" 
               style={{ 
                  display: 'grid',
                  gap: '2px',
                  gridTemplateColumns: `repeat(${columnCount}, ${tileSize}px)`,
                  width: `${gridPixelSize}px`,
                  height: `${gridPixelSize}px`,
                  transformStyle: 'preserve-3d'
               }}
             >
                {tiles.map((tile: any) => (
                    <Tile key={`${tile.x}-${tile.y}`} tile={tile} tileSize={tileSize} isTactical={isTactical} />
                ))}
                
                {/* COMBAT TEXT OVERLAY */}
                <div className="absolute inset-0 z-50 pointer-events-none">
                    <CombatTextOverlay combatNotifications={combatNotifications} mapData={mapData} tileSize={tileSize} />
                </div>
             </motion.div>
         </div>

         {/* [V12.2] MAP CONTROLS - RELOCATED TO CENTER-BOTTOM (Occlusion Rescue) */}
         <div className="absolute bottom-10 left-1/2 -translate-x-1/2 z-[20000] flex gap-3 pointer-events-none">
            <button 
              onClick={(e) => { e.preventDefault(); e.stopPropagation(); setUserZoom(prev => Math.max(0.1, prev - 0.15)); }} 
              className="relative p-2.5 rounded-xl bg-slate-900/90 border border-white/10 text-slate-400 hover:text-cyan-400 hover:border-cyan-500/50 transition-all z-[20000] pointer-events-auto cursor-pointer shadow-2xl flex items-center justify-center group active:scale-95" 
              title="Zoom Out"
            >
              <div className="absolute inset-0 bg-cyan-500/5 opacity-0 group-hover:opacity-100 rounded-xl transition-opacity" />
              <Layers size={16} />
            </button>
            <button 
              onClick={(e) => { e.preventDefault(); e.stopPropagation(); setUserZoom(prev => Math.min(3.0, prev + 0.15)); }} 
              className="relative p-2.5 rounded-xl bg-slate-900/90 border border-white/10 text-slate-400 hover:text-cyan-400 hover:border-cyan-500/50 transition-all z-[20000] pointer-events-auto cursor-pointer shadow-2xl flex items-center justify-center group active:scale-95" 
              title="Zoom In"
            >
              <div className="absolute inset-0 bg-cyan-500/5 opacity-0 group-hover:opacity-100 rounded-xl transition-opacity" />
              <Layers size={16} />
            </button>
            <button 
              onClick={(e) => { e.preventDefault(); e.stopPropagation(); setUserZoom(1); setOffset({x:0, y:0}); }} 
              className="relative p-2.5 rounded-xl bg-slate-900/90 border border-white/10 text-slate-400 hover:text-cyan-400 hover:border-cyan-500/50 transition-all z-[20000] pointer-events-auto cursor-pointer shadow-2xl flex items-center justify-center group active:scale-95" 
              title="Reset View"
            >
              <div className="absolute inset-0 bg-yellow-500/5 opacity-0 group-hover:opacity-100 rounded-xl transition-opacity" />
              <Settings size={16} />
            </button>
            <button 
              onClick={(e) => { e.preventDefault(); e.stopPropagation(); setShowInfluence(!showInfluence); }} 
              className={clsx("relative p-2.5 rounded-xl border backdrop-blur-md transition-all z-[20000] pointer-events-auto cursor-pointer shadow-2xl flex items-center justify-center group active:scale-95", showInfluence ? "bg-cyan-500/30 border-cyan-500/50 text-cyan-400 shadow-[0_0_20px_rgba(34,211,238,0.3)]" : "bg-slate-900/90 border-white/10 text-slate-500")} 
              title="Influence Overlay"
            >
              <div className={clsx("absolute inset-0 rounded-xl transition-opacity", showInfluence ? "bg-cyan-500/10" : "bg-cyan-500/5 opacity-0 group-hover:opacity-100")} />
              <Layers size={16} />
            </button>
         </div>
    </div>
   );
}

export default Viewport;
