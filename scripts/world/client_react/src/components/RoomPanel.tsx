import React from 'react';
import { useStore } from '../store/useStore';
import { sendCommand } from '../lib/ges';
import { Users, BookOpen, AlertCircle, ShieldAlert, Zap } from 'lucide-react';
import { clsx } from 'clsx';

export function RoomPanel() {
  const { status, selectedTargetId, setSelectedTargetId } = useStore();
  
  const entities = status?.room?.entities || [];
  const traps = status?.room?.traps || [];

  return (
    <div className="glass-panel rounded-lg overflow-hidden flex flex-col h-[300px]">
       <div className="bg-slate-900/50 px-3 py-2 border-b border-white/5 flex items-center justify-between">
          <div className="flex items-center gap-2">
             <BookOpen size={14} className="text-emerald-400" />
             <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest leading-none">Intelligence</span>
          </div>
       </div>
       <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {/* Room Description */}
          <div className="text-[12px] text-slate-400 font-serif leading-relaxed italic border-l-2 border-emerald-900/30 pl-3">
             {status?.room?.description || 'The void gazes back with indifference...'}
          </div>

          {/* Entities List */}
          <div className="space-y-1">
             <div className="text-[10px] font-black text-slate-600 uppercase tracking-tighter mb-2">Entities Detected</div>
             {entities.length > 0 ? (
                entities.map((ent, idx) => {
                   const isSelected = selectedTargetId === ent.id;
                   const colorClass = ent.is_player ? "text-blue-400" : (ent.is_hostile ? "text-red-400" : "text-yellow-400");
                   
                   return (
                      <div 
                        key={ent.id || idx}
                        onClick={() => setSelectedTargetId(isSelected ? null : ent.id)}
                        onDoubleClick={(e) => {
                           e.stopPropagation();
                           sendCommand(`kill ${ent.name}`); // Bug 07: Kill on double-click
                        }}
                        className={clsx(
                           "flex items-center justify-between p-2 rounded cursor-pointer transition-all",
                           isSelected ? "bg-emerald-950/40 border border-emerald-500/50 ring-1 ring-emerald-500/10" : "hover:bg-white/5 border border-transparent"
                        )}
                      >
                         <div className="flex items-center gap-3">
                            <span className={clsx("font-black text-lg drop-shadow-md", colorClass)}>{ent.symbol}</span>
                            <span className="font-black text-lg drop-shadow-md" style={{ color: colorClass }}>{ent.symbol}</span>
                            <span className="text-xs font-bold text-slate-300">{ent.name}</span>
                         </div>
                         {isSelected && <div className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)]" />}
                      </div>
                   );
                })
             ) : (
                <div className="h-20 flex items-center justify-center border border-dashed border-white/5 rounded text-[10px] text-slate-700 font-bold uppercase tracking-widest">
                   No life signs detected
                </div>
             )}
          </div>

           {/* Traps Section (Bug 06) */}
           {traps.length > 0 && (
              <div className="space-y-1 border-t border-white/5 pt-3">
                 <div className="text-[10px] font-black text-slate-600 uppercase tracking-tighter mb-2 flex items-center gap-1.5">
                    <ShieldAlert size={10} className="text-blue-400" />
                    <span>Mechanisms Detected</span>
                 </div>
                 <div className="space-y-1">
                    {traps.map((trap: any, idx: number) => (
                       <div 
                         key={trap.id || idx}
                         className="flex items-center gap-3 p-1.5 rounded bg-blue-500/5 border border-blue-500/10 group hover:bg-blue-500/10 transition-colors"
                       >
                          <div className="w-5 h-5 rounded border border-blue-500/30 bg-blue-500/10 flex items-center justify-center">
                             <Zap size={10} className={trap.is_mine ? "text-cyan-400" : "text-amber-400"} />
                          </div>
                          <div className="flex flex-col">
                             <span className={clsx("text-[10px] font-black uppercase tracking-widest", trap.is_mine ? "text-cyan-400" : "text-amber-400")}>
                                {trap.type} TRAP
                             </span>
                             <span className="text-[8px] text-slate-500 font-bold uppercase">Owner: {trap.owner}</span>
                          </div>
                       </div>
                    ))}
                 </div>
              </div>
           )}
        </div>
     </div>
   );
}

export default RoomPanel;
