import React from 'react';
import { useStore } from '../store/useStore';
import { 
  LayoutDashboard, Map, Zap, Shield, 
  Users, MessageSquareText, Power, RotateCcw
} from 'lucide-react';
import { clsx } from 'clsx';

export const MenuBar = () => {
  const { windows, toggleWindow, isConnected, resetLayout } = useStore();

  const menuItems = [
    { id: 'tactical', label: 'Tactical', icon: Map },
    { id: 'mini', label: 'Scanner', icon: Map },
    { id: 'room', label: 'Local', icon: Users },
    { id: 'comms', label: 'Logs', icon: MessageSquareText },
    { id: 'vitals', label: 'Vitality', icon: Shield },
    { id: 'combat', label: 'Abilities', icon: Zap },
  ];

  return (
    <div className="absolute top-0 left-0 right-0 h-10 bg-slate-900/60 backdrop-blur-md border-b border-white/5 flex items-center justify-between px-6 z-[10000]">
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2 mr-4">
           <LayoutDashboard size={14} className="text-blue-500" />
           <span className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400">Divine Workspace</span>
        </div>

        <div className="flex items-center gap-1">
          {menuItems.map((item) => {
            const win = windows[item.id];
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                onClick={() => toggleWindow(item.id)}
                className={clsx(
                  "px-3 h-7 flex items-center gap-2 rounded-md transition-all text-[9px] font-bold uppercase tracking-wider border",
                  win?.isVisible 
                    ? "bg-blue-500/10 border-blue-500/30 text-blue-100" 
                    : "bg-transparent border-transparent text-slate-500 hover:text-slate-300 hover:bg-white/5"
                )}
              >
                <Icon size={12} className={win?.isVisible ? "text-blue-400" : "text-current"} />
                {item.label}
              </button>
            );
          })}
        </div>
      </div>

      <div className="flex items-center gap-4">
         <div className="flex items-center gap-2 px-3 py-1 bg-black/40 rounded-full border border-white/5">
            <div className={clsx("w-1.5 h-1.5 rounded-full", isConnected ? "bg-green-500 animate-pulse" : "bg-red-500")} />
            <span className="text-[8px] font-mono text-slate-400 uppercase">
               {isConnected ? "Linked: Soul-Bound" : "Awaiting Connection"}
            </span>
         </div>
         <button 
           onClick={() => resetLayout()}
           className="text-slate-500 hover:text-cyan-400 transition-colors"
           title="Refresh Workspace Matrix"
         >
            <RotateCcw size={14} />
         </button>
         <button className="text-slate-500 hover:text-white transition-colors">
            <Power size={14} />
         </button>
      </div>
    </div>
  );
};

export default MenuBar;
