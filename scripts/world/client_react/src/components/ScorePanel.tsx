import React from 'react';
import { useStore } from '../store/useStore';
import { User, Shield, Zap, Target, Star, Award } from 'lucide-react';

export function ScorePanel() {
  const { status } = useStore();
  
  if (!status) return null;

  return (
    <div className="p-4 space-y-6">
       {/* Identity Header */}
       <div className="flex items-center gap-4 border-b border-white/5 pb-4">
          <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-lg border border-white/10">
             <User size={24} className="text-white" />
          </div>
          <div>
             <h2 className="text-lg font-black uppercase tracking-widest text-white leading-none">Ascendant Spirit</h2>
             <p className="text-[10px] font-bold text-slate-500 uppercase tracking-tighter mt-1">Tier 1 Initiate • Godless Realms</p>
          </div>
       </div>

       {/* Core Trophies / Stats */}
       <div className="grid grid-cols-2 gap-4">
          <div className="glass-panel p-3 rounded-lg border-white/5 flex flex-col items-center justify-center">
             <Star size={16} className="text-yellow-500 mb-1" />
             <span className="text-[10px] font-black text-slate-500 uppercase">Favor</span>
             <span className="text-lg font-mono font-black text-white">1,250</span>
          </div>
          <div className="glass-panel p-3 rounded-lg border-white/5 flex flex-col items-center justify-center">
             <Award size={16} className="text-blue-500 mb-1" />
             <span className="text-[10px] font-black text-slate-500 uppercase">Rank</span>
             <span className="text-lg font-mono font-black text-white">Seeker</span>
          </div>
       </div>

       {/* Resource Summary */}
       <div className="space-y-3">
          <div className="flex justify-between items-center px-1">
             <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Divine Resources</span>
             <Zap size={12} className="text-blue-400" />
          </div>
          
          <div className="space-y-2">
             <div className="space-y-1">
                <div className="flex justify-between text-[8px] font-black uppercase text-slate-500">
                   <span>Essence (HP)</span>
                   <span>{status.hp.current} / {status.hp.max}</span>
                </div>
                <div className="h-1.5 bg-slate-900 rounded-full overflow-hidden border border-white/5">
                   <div className="h-full bg-blue-500" style={{ width: `${(status.hp.current/status.hp.max)*100}%` }} />
                </div>
             </div>
             
             <div className="space-y-1">
                <div className="flex justify-between text-[8px] font-black uppercase text-slate-500">
                   <span>Stamina</span>
                   <span>{status.stamina.current} / {status.stamina.max}</span>
                </div>
                <div className="h-1.5 bg-slate-900 rounded-full overflow-hidden border border-white/5">
                   <div className="h-full bg-yellow-600" style={{ width: `${(status.stamina.current/status.stamina.max)*100}%` }} />
                </div>
             </div>

             <div className="space-y-1">
                <div className="flex justify-between text-[8px] font-black uppercase text-slate-500">
                   <span>Balance</span>
                   <span>{status.balance.current} / {status.balance.max}</span>
                </div>
                <div className="h-1.5 bg-slate-900 rounded-full overflow-hidden border border-white/5">
                   <div className="h-full bg-cyan-600" style={{ width: `${(status.balance.current/status.balance.max)*100}%` }} />
                </div>
             </div>
          </div>
       </div>

    </div>
  );
}

export default ScorePanel;
