import React, { useMemo } from 'react';
import { useStore } from '../store/useStore';
import { clsx } from 'clsx';
import { Map, Users, AlertCircle, Layers } from 'lucide-react';

interface ViewportProps {
   radius: number;
   context: 'mini' | 'tactical' | 'map';
   scale?: number;
}

export function Viewport({ radius, context, scale = 1 }: ViewportProps) {
  const { isConnected, tacticalMapData, showInfluence, setShowInfluence } = useStore();
  
  const mapData = tacticalMapData;
  const isTactical = context === 'tactical';
  const tileSize = 60 * scale;

  const tiles = useMemo(() => {
     if (!mapData || !mapData.grid) return [];
     return mapData.grid.flat();
  }, [mapData]);

   if (!isConnected) {
      return (
         <div className="w-full h-full flex flex-col items-center justify-center bg-slate-900/40">
            <div className="w-12 h-12 border-2 border-dashed border-slate-700 animate-spin rounded-full" />
            <p className="mt-4 text-[10px] uppercase tracking-[0.2em] text-slate-500 animate-pulse">Establishing Divine Link...</p>
         </div>
      );
   }

   // [BUG 16 FIX] Robust tile persistence. Use coordinate keys only.
   return (
     <div className="w-full h-full overflow-hidden flex items-center justify-center p-8 bg-slate-950/20 perspective-1000">
         <div 
           className="grid gap-[2px]" 
           style={{ 
              gridTemplateColumns: `repeat(${mapData?.grid?.length || 0}, ${tileSize}px)`,
              transform: isTactical ? 'rotateX(20deg) rotateZ(-5deg)' : 'none'
           }}
         >
            {tiles.map((tile: any) => {
               const elev = tile.elevation || 0;
               const lift = isTactical ? -elev * 3 : 0; // Refined Height (Bug 01 Fix)
               const isDiscovered = tile.visible;
               const isInLos = tile.in_los;

               const monsters = tile.top_entities?.filter((e: any) => !e.is_player && !e.is_self && !e.is_ping) || [];
               const otherPlayers = tile.top_entities?.filter((e: any) => e.is_player && !e.is_self) || [];
               const pings = tile.top_entities?.filter((e: any) => e.is_ping) || [];
               const isSelf = tile.top_entities?.some((e: any) => e.is_self);

               return (
                  <div 
                     key={`${tile.x}-${tile.y}`}
                     className={clsx(
                        "relative flex items-center justify-center transition-all duration-100", // Bug 04: Snappy movement
                        isDiscovered ? "border-slate-800/10" : "opacity-0",
                        isTactical ? "rounded-sm" : ""
                     )}
                    style={{
                       width: tileSize,
                       height: tileSize,
                       backgroundColor: isDiscovered 
                         ? (isInLos ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.3)') 
                         : 'transparent',
                       transform: `translateY(${lift}px)`,
                       boxShadow: isTactical && elev > 0 && isDiscovered 
                         ? `0 ${elev * 2}px 10px rgba(0,0,0,0.5)` 
                         : 'none',
                       filter: !isInLos && isDiscovered ? 'grayscale(0.8) brightness(0.4)' : 'none'
                    }}
                 >
                    {/* 0. Influence Layer (Bug 04) */}
                    {showInfluence && tile.influence && (
                       <div 
                          className={clsx(
                             "absolute inset-0 z-10 mix-blend-screen transition-opacity pointer-events-none",
                             tile.influence.kingdom === 'light' ? 'bg-cyan-500/40' :
                             tile.influence.kingdom === 'dark' ? 'bg-purple-900/50' :
                             tile.influence.kingdom === 'instinct' ? 'bg-emerald-600/40' : 'bg-transparent'
                          )}
                          style={{ opacity: Math.min(0.9, tile.influence.strength / 30) }}
                       />
                    )}

                    {/* 1. Terrain Character */}
                    <span 
                      className={clsx(
                        "text-base font-black transition-colors duration-100",
                        !isInLos && "opacity-40"
                      )}
                      style={{ color: isDiscovered ? (isInLos ? tile.color : '#64748b') : 'transparent' }}
                    >
                       {isDiscovered ? tile.char : '?'}
                    </span>

                    {/* 2. Entity HUD Overlays */}
                    {isDiscovered && (
                        <div className="absolute inset-0 pointer-events-none z-30">
                           <div className="absolute inset-0 pointer-events-none">
                                {/* TOP-RIGHT: Monsters */}
                                {monsters.length > 0 && (
                                    <div className="absolute top-0.5 right-0.5 flex flex-col items-end">
                                        <div className={clsx(
                                            "w-2 h-2 rounded-full shadow-sm flex items-center justify-center border border-white/10",
                                            monsters[0].is_hostile ? "bg-red-500" : "bg-yellow-500"
                                        )}>
                                           <span className="text-[6px] font-black text-white">{monsters[0].symbol}</span>
                                        </div>
                                        {monsters.length > 1 && (
                                            <span className="text-[6px] font-bold text-white/40 leading-none">+{monsters.length - 1}</span>
                                        )}
                                    </div>
                                )}

                                {/* TOP-LEFT: Other Players */}
                                {otherPlayers.length > 0 && (
                                    <div className="absolute top-0.5 left-0.5">
                                        <div className="w-2 h-2 rounded-full bg-blue-500 border border-white/10 flex items-center justify-center">
                                           <span className="text-[6px] font-black text-white">{otherPlayers[0].symbol}</span>
                                        </div>
                                    </div>
                                )}

                                {/* CENTER: Self */}
                                {isSelf && (
                                    <div className="absolute inset-0 flex items-center justify-center">
                                       <div className="w-2.5 h-2.5 rounded-full border border-blue-400 bg-blue-400/40 animate-pulse" />
                                    </div>
                                )}

                                {/* BOTTOM-RIGHT: Pings */}
                                {tile.has_pings && (tile.top_entities?.length || 0) === 0 && (
                                    <div className="absolute bottom-0.5 right-0.5">
                                        <div className="w-1.5 h-1.5 rounded-full bg-yellow-500/40 animate-ping" />
                                    </div>
                                )}
                           </div>
                        </div>
                    )}

                    {/* 3. Height Shading & Peak Highlights (Bug 03: Granular Height) */}
                    {isTactical && elev > 0 && isDiscovered && (
                       <>
                          <div 
                             className="absolute left-0 right-0 -bottom-[1px] bg-black/30 z-0 rounded-b-sm pointer-events-none"
                             style={{ height: `${elev * 3}px` }}
                          />
                          <div className={clsx(
                             "absolute inset-x-0 top-0 h-[2px] z-40 pointer-events-none",
                             elev > 5 ? "bg-white/40" : "bg-white/20"
                          )} />
                       </>
                    )}
                 </div>
              );
           })}
        </div>

         {/* 4. Layer Controls (Floating) */}
         {isTactical && (
            <div className="absolute top-2 left-2 z-[60] flex gap-2">
               <button 
                  onClick={() => setShowInfluence(!showInfluence)}
                  className={clsx(
                      "p-1.5 rounded-md border backdrop-blur-sm transition-all shadow-xl",
                      showInfluence 
                        ? "bg-cyan-500/30 border-cyan-500/50 text-cyan-400" 
                        : "bg-black/60 border-white/10 text-slate-500 hover:border-white/20 hover:text-slate-300"
                  )}
                  title="Toggle Sovereignty Influence"
               >
                  <Layers size={14} />
               </button>
            </div>
         )}
    </div>
  );
}

export default Viewport;
