import React from 'react';
import { clsx } from 'clsx';
import { Zap, Swords, Shield, Info, Target, Fingerprint } from 'lucide-react';

interface AbilityButtonProps {
  ability: any;
  onCast: (id: string, ready: boolean) => void;
}

export const AbilityButton = ({ ability, onCast }: AbilityButtonProps) => {
  const b = ability;
  
  return (
    <button 
      onClick={() => onCast(b.id, b.ready)}
      className={clsx(
        "group relative flex flex-col items-center justify-center w-full aspect-square rounded-lg border transition-all active:scale-95 shadow-lg overflow-hidden",
        b.ready 
          ? "bg-slate-900/80 border-white/10 hover:border-blue-500/60 hover:shadow-blue-500/20" 
          : "bg-black/60 border-white/5 grayscale-[0.3] cursor-not-allowed",
        b.setup_ready && b.ready && "ring-2 ring-red-500 ring-inset shadow-[0_0_20px_rgba(239,68,68,0.6)] animate-pulse"
      )}
      title={`${b.name}: ${b.description || 'GCA Ability'}`}
    >
       {/* 1. Readiness Glow (Pulse when ready) */}
       {b.ready && (
          <div className={clsx(
              "absolute inset-0 animate-pulse pointer-events-none opacity-20",
              b.type === 'damage' ? "bg-red-500" :
              b.type === 'defense' ? "bg-green-500" :
              b.type === 'utility' ? "bg-purple-500" :
              "bg-blue-500"
          )} />
       )}

       {/* 2. Top-Left: Type Indicator */}
       <div className="absolute top-1.5 left-1.5 z-10">
          {b.type === 'damage' ? <Swords size={12} className="text-red-400 drop-shadow-md" /> : 
           b.type === 'defense' ? <Shield size={12} className="text-green-400 drop-shadow-md" /> : 
           b.type === 'utility' ? <Info size={12} className="text-purple-400 drop-shadow-md" /> : 
           <Zap size={12} className="text-yellow-400 drop-shadow-md" />}
       </div>

       {/* 3. Top-Right: Resource Cost */}
       <div className="absolute top-1.5 right-1.5 text-[10px] font-black font-mono text-white tracking-widest bg-black/60 px-1.5 py-0.5 rounded border border-white/5 shadow-xl z-10">
         {b.cost > 0 ? b.cost : '0'}
       </div>

       {/* 4. Icon (Centered & Styled) */}
       <div className={clsx(
           "text-2xl transition-all duration-300",
           b.ready ? "filter drop-shadow-[0_0_12px_currentColor] scale-110 opacity-100" : "scale-90 opacity-40 grayscale",
           b.type === 'damage' ? "text-red-500" :
           b.type === 'utility' ? "text-purple-400" :
           b.type === 'defense' ? "text-green-500" :
           "text-blue-400"
       )}>
          {b.icon === 'bolt' ? <Zap size={28} /> : 
           b.type === 'damage' ? <Swords size={28} /> : 
           b.type === 'defense' ? <Shield size={28} /> : 
           b.type === 'utility' ? <Fingerprint size={28} /> : 
           <Target size={28} />}
       </div>

       {/* 5. Label (Bottom Anchor) */}
       <div className="absolute bottom-1 inset-x-0 px-1 text-center truncate pointer-events-none">
          <span className={clsx(
              "text-[8px] font-black uppercase tracking-tighter transition-colors",
              b.ready ? "text-white" : "text-slate-400"
          )}>
            {b.name}
          </span>
       </div>

       {/* 6. Cooldown Overlay */}
       {!b.ready && (
          <div className="absolute inset-0 bg-black/60 flex items-center justify-center pointer-events-none">
             <span className="text-xs font-black text-white/40">{Math.ceil(b.cooldown/5)}s</span>
          </div>
       )}
    </button>
  );
};
