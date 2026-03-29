import React from 'react';
import { useStore } from '../store/useStore';
import {
  Map, Zap, Shield,
  Users, MessageSquareText,
  Settings, Briefcase, Sun, Award, Fingerprint, Swords,
  Heart, Info, RefreshCw
} from 'lucide-react';
import { clsx } from 'clsx';

/**
 * [V11.6] Godless Master Menu: Consolidated Intelligence
 * Nexus (Game) & Master Studio (Design)
 */
const MenuBar = () => {
  const {
    windows, toggleWindow, isConnected,
    isAdmin, activeWorkspace, setWorkspace
  } = useStore();

  const menuItems = [
    { id: 'tactical', label: 'Tactical', icon: Map },
    { id: 'mini', label: 'Scanner', icon: Map },
    { id: 'room', label: 'Local', icon: Users },
    { id: 'comms', label: 'Logs', icon: MessageSquareText },
    { id: 'vitals', label: 'Vitality', icon: Shield },
    { id: 'combat', label: 'Abilities', icon: Zap },
    { id: 'inventory', label: 'Bags', icon: Briefcase },
    { id: 'encounter', label: 'Target', icon: Swords },
    { id: 'weather', label: 'Sky', icon: Sun },
    { id: 'score', label: 'Legacy', icon: Award },
    { id: 'attributes', label: 'Soul', icon: Fingerprint }
  ];

  return (
    <div className="absolute top-0 left-0 right-0 h-10 bg-slate-900/80 backdrop-blur-xl border-b border-white/5 flex items-center justify-between px-6 z-[10000] shadow-2xl">
      <div className="flex items-center gap-6">
        
        {/* Workspace Switcher (Unified Consistently) */}
        <div className="flex items-center bg-black/40 rounded-lg p-0.5 border border-white/10">
          <button
            onClick={() => setWorkspace('nexus')}
            className={clsx(
              "px-4 py-1.5 rounded text-[9px] font-black uppercase tracking-widest transition-all",
              activeWorkspace === 'nexus' ? "bg-cyan-600 text-white shadow-lg shadow-cyan-500/20" : "text-slate-500 hover:text-slate-300"
            )}
          >
            Nexus Interface
          </button>
          
          {isAdmin && (
            <button
               onClick={() => setWorkspace('studio')}
               className={clsx(
                  "px-4 py-1.5 rounded text-[9px] font-black uppercase tracking-widest transition-all flex items-center gap-2",
                  (activeWorkspace === 'studio' || activeWorkspace === 'editor') ? "bg-purple-600 text-white shadow-lg shadow-purple-500/20" : "text-slate-500 hover:text-slate-300"
               )}
            >
               Master Studio
            </button>
          )}
        </div>

        {/* Floating View Toggles (Only visible when Nexus is OFF) */}
        {activeWorkspace !== 'nexus' && activeWorkspace !== 'studio' && activeWorkspace !== 'editor' && (
          <div className="flex items-center gap-1 border-l border-white/10 pl-4">
            {menuItems.map(item => (
              <button
                key={item.id}
                onClick={() => toggleWindow(item.id)}
                className={clsx(
                  "p-2 rounded hover:bg-white/5 transition-all text-slate-500",
                  windows[item.id]?.isVisible ? "text-cyan-400" : ""
                )}
                title={item.label}
              >
                <item.icon size={14} />
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 px-3 py-1 bg-black/40 border border-white/5 rounded-full">
          <div className={clsx("w-1.5 h-1.5 rounded-full", isConnected ? "bg-green-500 animate-pulse shadow-[0_0_5px_#22c55e]" : "bg-red-500")} />
          <span className="text-[8px] font-black text-slate-400 uppercase tracking-widest">
            {isConnected ? "Engine Active" : "Disconnected"}
          </span>
        </div>
        
        <div className="flex items-center gap-1 border-l border-white/5 pl-4">
          <button className="p-2 text-slate-500 hover:text-cyan-400" title="Manual Sync"><RefreshCw size={14}/></button>
          <button className="p-2 text-slate-600 hover:text-red-500" title="Power Down"><Heart size={14}/></button>
        </div>
      </div>
    </div>
  );
};

export default MenuBar;
