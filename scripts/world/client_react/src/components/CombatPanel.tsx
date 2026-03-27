import React from 'react';
import { useStore } from '../store/useStore';
import { Swords, Heart, AlertCircle, ShieldAlert } from 'lucide-react';
import { clsx } from 'clsx';
import ProgressBar from './atoms/ProgressBar';

export function CombatPanel() {
  const { status } = useStore();
  
  const target = status?.target;
  const effects = status?.status_effects || [];

  return (
    <div className="glass-panel rounded-lg overflow-hidden flex flex-col min-h-[160px]">
       <div className="bg-slate-900/50 px-3 py-2 border-b border-white/5 flex items-center justify-between">
          <div className="flex items-center gap-2">
             <Swords size={14} className="text-red-400" />
             <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest leading-none">Combat Awareness</span>
          </div>
       </div>
       <div className="flex-1 p-3 space-y-4">
          <div className="grid grid-cols-2 gap-4">
             {/* Left Side: You */}
             <div className="space-y-2">
                <ProgressBar 
                   current={status?.hp.current || 0}
                   max={status?.hp.max || 1}
                   label="Divine Vessel (You)"
                   showValues
                   colorClassName="bg-gradient-to-r from-blue-900 to-blue-500"
                   size="md"
                />
                <ProgressBar 
                   current={status?.stamina.current || 0}
                   max={status?.stamina.max || 1}
                   colorClassName="bg-yellow-600"
                   size="sm"
                />
             </div>

             {/* Right Side: Target */}
             <div className="space-y-2">
                {target ? (
                   <ProgressBar 
                      current={target.hp.current}
                      max={target.hp.max}
                      label={target.name}
                      showValues
                      colorClassName="bg-gradient-to-l from-red-900 to-red-600"
                      size="md"
                   />
                ) : (
                   <div className="h-full flex items-center justify-center border border-dashed border-white/5 rounded text-[8px] text-slate-700 font-bold uppercase tracking-widest text-center">
                      No Combat Focus
                   </div>
                )}
             </div>
          </div>

          {/* Afflictions & Effects */}
          <div className="space-y-2 border-t border-white/5 pt-3">
             <div className="flex items-center gap-2">
                <ShieldAlert size={10} className="text-purple-400" />
                <div className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Active Manifestations</div>
             </div>
             <div className="flex flex-wrap gap-1.5">
                {effects.length > 0 ? (
                   effects.map((eff, idx) => (
                      <div 
                        key={eff.id || idx}
                        className={clsx(
                            "px-2 py-0.5 rounded border flex items-center gap-1.5 transition-all text-[8px] font-black uppercase tracking-tighter",
                            eff.type === 'buff' ? "bg-blue-500/10 border-blue-500/30 text-blue-200" : "bg-red-500/10 border-red-500/30 text-red-200"
                        )}
                        title={eff.id}
                      >
                         <span>{eff.name}</span>
                         <span className="opacity-50 font-mono">[{Math.ceil(eff.duration/5)}s]</span>
                      </div>
                   ))
                ) : (
                   <span className="text-[8px] text-slate-700 font-bold uppercase tracking-[0.2em] py-1">Equilibrium Maintained</span>
                )}
             </div>
          </div>
       </div>
    </div>
  );
}

export default CombatPanel;
