import React from 'react';
import { useStore } from '../store/useStore';
import { Heart, Zap, Shield, Flame } from 'lucide-react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

const VitalBar = ({ icon: Icon, color, value, max, label }: { icon: any, color: string, value: number, max: number, label: string }) => {
  const pct = Math.min(100, Math.max(0, (value / max) * 100));
  
  return (
    <div className="bar-bg h-8 relative group">
       <div 
         className={twMerge("bar-fill h-full bg-gradient-to-r", color)} 
         style={{ width: `${pct}%` }} 
       />
       <div className="absolute inset-0 flex items-center px-3 justify-between pointer-events-none">
          <div className="flex items-center gap-2">
             <Icon size={14} className="text-white shadow-sm" />
             <span className="text-[10px] font-black text-white/80 uppercase tracking-widest">{label}</span>
          </div>
          <span className="text-[10px] font-mono text-white/90">
            {value}<span className="text-white/40">/{max}</span>
          </span>
       </div>
    </div>
  );
};

export function VitalsStack() {
  const { status } = useStore();
  if (!status) return null;

  const effects = status.status_effects || [];

  return (
    <div className="flex flex-col h-full overflow-hidden p-1">
      {/* 1. Core Adaptive Resource Stack */}
      <div className="flex-1 flex flex-col gap-1 min-h-0">
        <VitalBar 
          icon={Heart} 
          color="from-red-950 via-red-800 to-red-600" 
          value={status.hp.current} 
          max={status.hp.max} 
          label="Vitality" 
        />
        <VitalBar 
          icon={Zap} 
          color="from-yellow-950 via-yellow-700 to-yellow-500" 
          value={status.stamina.current} 
          max={status.stamina.max} 
          label="Stamina" 
        />
        <VitalBar 
          icon={Shield} 
          color="from-blue-950 via-blue-700 to-blue-500" 
          value={status.balance.current} 
          max={status.balance.max} 
          label="Posture" 
        />
        
        {status.resource && (
           <VitalBar 
             icon={Flame} 
             color="from-purple-950 via-purple-700 to-purple-500" 
             value={status.resource.current} 
             max={status.resource.max} 
             label={status.resource.name} 
           />
        )}
      </div>

      {/* 2. Manifestations & Afflictions (Bug 11 Recovery) */}
      {effects.length > 0 && (
         <div className="mt-3 pt-3 border-t border-white/5">
            <h3 className="text-[9px] font-black text-slate-500 uppercase tracking-widest mb-2 flex items-center justify-between">
               Manifestations
               <span className="text-white/20 font-mono">{effects.length} Active</span>
            </h3>
            <div className="flex flex-wrap gap-2">
               {effects.map((fx: any) => (
                  <div 
                    key={fx.id} 
                    className="flex items-center gap-2 bg-slate-900/60 border border-white/5 rounded-md px-2 py-1 pr-3 shadow-md hover:border-white/10 transition-colors"
                  >
                     <div className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />
                     <span className="text-[9px] font-bold text-slate-300 uppercase truncate max-w-[80px]">
                        {fx.name}
                     </span>
                     <span className="text-[8px] font-mono text-slate-500">
                        {Math.ceil(fx.duration/2)}s
                     </span>
                  </div>
               ))}
            </div>
         </div>
      )}
    </div>
  );
}

export default VitalsStack;
