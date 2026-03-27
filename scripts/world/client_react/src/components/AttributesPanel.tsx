import React from 'react';
import { useStore } from '../store/useStore';
import { Shield, Zap, Swords, Target, Settings, Brain, Activity, Droplets } from 'lucide-react';

export function AttributesPanel() {
  const { status } = useStore();
  
  if (!status) return null;

  return (
    <div className="p-4 space-y-6">
       
       {/* Core Attributes Header */}
       <div className="flex items-center gap-2 border-b border-white/5 pb-2">
          <Settings size={14} className="text-slate-400" />
          <h2 className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500">Core Attributes</h2>
       </div>

       {/* Attributes Grid */}
       <div className="grid grid-cols-2 gap-4">
          <div className="space-y-4">
             <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-red-500/10 flex items-center justify-center border border-red-500/50">
                   <Swords size={16} className="text-red-500" />
                </div>
                <div>
                   <div className="text-[10px] font-black text-slate-500 uppercase tracking-tighter">Strength</div>
                   <div className="text-lg font-mono font-black text-white">18</div>
                </div>
             </div>

             <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-blue-500/10 flex items-center justify-center border border-blue-500/50">
                   <Droplets size={16} className="text-blue-500" />
                </div>
                <div>
                   <div className="text-[10px] font-black text-slate-500 uppercase tracking-tighter">Dexterity</div>
                   <div className="text-lg font-mono font-black text-white">22</div>
                </div>
             </div>
          </div>

          <div className="space-y-4">
             <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-purple-500/10 flex items-center justify-center border border-purple-500/50">
                   <Brain size={16} className="text-purple-500" />
                </div>
                <div>
                   <div className="text-[10px] font-black text-slate-500 uppercase tracking-tighter">Wisdom</div>
                   <div className="text-lg font-mono font-black text-white">14</div>
                </div>
             </div>

             <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-green-500/10 flex items-center justify-center border border-green-500/50">
                   <Activity size={16} className="text-green-500" />
                </div>
                <div>
                   <div className="text-[10px] font-black text-slate-500 uppercase tracking-tighter">Vitality</div>
                   <div className="text-lg font-mono font-black text-white">20</div>
                </div>
             </div>
          </div>
       </div>

       {/* Secondary Stats */}
       <div className="space-y-3 pt-2">
          <div className="flex items-center gap-2 border-b border-white/5 pb-2">
             <Shield size={14} className="text-slate-400" />
             <h2 className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500">Secondary Stats</h2>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
             <div className="bg-slate-900/40 p-3 rounded-lg border border-white/5">
                <span className="text-[8px] font-black text-slate-600 uppercase tracking-widest block mb-1">Armor Class</span>
                <span className="text-base font-mono font-black text-white">45</span>
             </div>
             <div className="bg-slate-900/40 p-3 rounded-lg border border-white/5">
                <span className="text-[8px] font-black text-slate-600 uppercase tracking-widest block mb-1">Spell Power</span>
                <span className="text-base font-mono font-black text-white">12</span>
             </div>
          </div>
       </div>

    </div>
  );
}

export default AttributesPanel;
