import React from 'react';
import { clsx } from 'clsx';
import { Zap, Swords, Shield, Info, Target, Fingerprint } from 'lucide-react';

interface AbilityButtonProps {
  ability: any;
  onCast: (ability: any) => void;
  index: number;
}


export const AbilityButton = ({ ability, onCast, index }: AbilityButtonProps) => {
  const b = ability;
  
  // [V7.2 Standard] GCA Ability Mapping
  const type_color = 
    b.type === 'payoff' ? "border-red-500/50 hover:border-red-500 shadow-red-500/10" :
    b.type === 'setup' ? "border-blue-500/50 hover:border-blue-500 shadow-blue-500/10" :
    b.type === 'defense' ? "border-green-500/50 hover:border-green-500 shadow-green-500/10" :
    b.type === 'utility' ? "border-purple-500/50 hover:border-purple-500 shadow-purple-500/10" :
    "border-white/10 hover:border-blue-400";

  return (
    <button 
      onClick={() => onCast(b)}
      className={clsx(
        "group relative flex flex-col items-center justify-center w-full aspect-square rounded-lg border transition-all active:scale-95 shadow-lg overflow-hidden",
        b.ready ? `bg-slate-900/80 ${type_color}` : "bg-black/60 border-white/5 grayscale-[0.3] cursor-not-allowed",
        b.setup_ready && b.ready && "ring-2 ring-red-500 ring-inset shadow-[0_0_20px_rgba(239,68,68,0.6)] animate-pulse"
      )}
      title={`${b.name}: ${b.description || 'GCA Ability'}`}
    >
       {/* 1. Readiness Glow (Pulse when ready) */}
       {b.ready && (
          <div className={clsx(
              "absolute inset-0 animate-pulse pointer-events-none opacity-10",
              b.type === 'payoff' ? "bg-red-500" :
              b.type === 'defense' ? "bg-green-500" :
              b.type === 'utility' ? "bg-purple-500" :
              "bg-blue-500"
          )} />
       )}

       {/* 2. Top-Left: Type Indicator */}
       <div className="absolute top-1 left-1 z-10 opacity-60">
          {b.type === 'payoff' ? <Swords size={10} className="text-red-400" /> : 
           b.type === 'defense' ? <Shield size={10} className="text-green-400" /> : 
           b.type === 'utility' ? <Info size={10} className="text-purple-400" /> : 
           <Zap size={10} className="text-blue-400" />}
       </div>

       {/* 3. Top-Right: Resource Cost */}
       <div className="absolute top-1 right-1 text-[8px] font-black font-mono text-white/50 tracking-tighter z-10">
         {b.cost > 0 ? b.cost : ''}
       </div>

       {/* 4. Icon (Centered & Styled) */}
       <div className={clsx(
           "text-2xl transition-all duration-300",
           b.ready ? "filter drop-shadow-[0_0_12px_currentColor] scale-100 opacity-100" : "scale-75 opacity-20 grayscale",
           b.type === 'payoff' ? "text-red-500" :
           b.type === 'utility' ? "text-purple-400" :
           b.type === 'defense' ? "text-green-500" :
           "text-blue-400"
       )}>
          {b.icon === 'bolt' ? <Zap size={24} /> : 
           b.type === 'payoff' ? <Swords size={24} /> : 
           b.type === 'defense' ? <Shield size={24} /> : 
           b.type === 'utility' ? <Fingerprint size={24} /> : 
           <Target size={24} />}
       </div>

       {/* 5. Hotkey Indicator (Bottom Right) */}
       <div className="absolute bottom-1 right-1 px-1 rounded bg-black/40 border border-white/5 pointer-events-none">
          <span className="text-[7px] font-black font-mono text-slate-500 group-hover:text-yellow-500 transition-colors">
            {index + 1}
          </span>
       </div>

       {/* 6. Label (Bottom Anchor) */}
       <div className="absolute bottom-1 left-2 max-w-[70%] truncate pointer-events-none">
          <span className={clsx(
              "text-[7px] font-black uppercase tracking-tighter transition-colors",
              b.ready ? "text-slate-400 group-hover:text-white" : "text-slate-600"
          )}>
            {b.name}
          </span>
       </div>

       {/* 7. Cooldown Overlay */}
       {!b.ready && (
          <div className="absolute inset-0 bg-black/60 flex items-center justify-center pointer-events-none">
             <span className="text-xs font-black text-white/40">{Math.ceil(b.cooldown/5)}s</span>
          </div>
       )}
    </button>
  );
};
