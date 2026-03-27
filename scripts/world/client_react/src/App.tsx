import React, { useState, useCallback, useEffect, useRef } from 'react';
import { useStore } from './store/useStore';
import { sendCommand } from './lib/ges';
import { 
  Shield, Heart, Zap, Swords, Map as MapIcon, 
  Settings, Users, BookOpen, AlertCircle, Info, Send,
  MessageSquareText, Award, User, Fingerprint, Briefcase, Sun
} from 'lucide-react';

// Sub-components
import Window from './components/Window';
import Viewport from './components/Viewport';
import VitalsStack from './components/VitalsStack';
import CommLog from './components/CommLog';
import RoomPanel from './components/RoomPanel';
import CombatPanel from './components/CombatPanel';
import AbilityBar from './components/AbilityBar';
import MenuBar from './components/MenuBar';
import ScorePanel from './components/ScorePanel';
import AttributesPanel from './components/AttributesPanel';
import InventoryPanel from './components/InventoryPanel';
import WeatherPanel from './components/WeatherPanel';

export function App() {
  const { isConnected, status } = useStore();
  const [inputCmd, setInputCmd] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputCmd.trim()) return;
    sendCommand(inputCmd);
    
    // Request 1: Keep command in box and highlight for rapid repeat
    if (inputRef.current) {
        inputRef.current.select();
    }
  };

  // Keyboard Mastery Hub (V8.7)
  const handleKeyDown = useCallback((e: KeyboardEvent) => {
      // 1. Refocus Command Line (Tab)
      if (e.key === 'Tab') {
          e.preventDefault();
          if (inputRef.current) {
              inputRef.current.focus();
              inputRef.current.select(); // Bug 13: Auto-select on Tab
          }
      }
  }, []);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  return (
    <div className="flex h-screen w-screen bg-slate-950 text-slate-200 font-sans overflow-hidden">
      {/* 1. Global HUD Connection Status */}
      {!isConnected && (
         <div className="absolute inset-0 z-[99999] bg-slate-950/90 backdrop-blur-xl flex flex-col items-center justify-center">
            <div className="w-24 h-24 border-t-2 border-blue-500 rounded-full animate-spin mb-8 shadow-[0_0_30px_rgba(59,130,246,0.3)]" />
            <h1 className="text-2xl font-black uppercase tracking-[0.5em] text-white animate-pulse">Establishing Divine Link</h1>
            <p className="mt-4 text-slate-500 font-mono text-sm tracking-widest uppercase">Negotiating Soul-Bound Protocol...</p>
         </div>
      )}

      {/* 2. Unified Workspace Layer */}
      <div className="relative flex-1 w-full h-full overflow-hidden pt-10 p-6 perspective-1000">
        <MenuBar />
        
        {/* SIDEBAR: Intelligence & Maps */}
        <Window id="tactical" title="Tactical Awareness" icon={<MapIcon size={14} />}>
            <Viewport radius={5} context="tactical" />
        </Window>

        <Window id="inventory" title="Divine Vessel: Inventory" icon={<Briefcase size={14} />}>
            <InventoryPanel />
        </Window>

        <Window id="room" title="Local Intelligence" icon={<Users size={14} />}>
           <RoomPanel />
        </Window>

        {/* CORE: Communications & Log (Gold Standard Focus) */}
        <Window id="comms" title="Divine Stream: Logs" icon={<MessageSquareText size={16} className="text-purple-400" />}>
           <CommLog />
        </Window>

        {/* COMBAT & VITALS (Floating) */}
        <Window id="vitals" title="Vital Signs" icon={<Shield size={14} />}>
           <VitalsStack />
        </Window>

        <Window id="encounter" title="Active Encounter" icon={<Swords size={14} className="text-red-500" />}>
           <CombatPanel />
        </Window>

        <Window id="combat" title="GCA: Ability Deck" icon={<Zap size={16} />}>
            <AbilityBar />
        </Window>

        <Window id="weather" title="Divine Climate" icon={<Sun size={14} />}>
            <WeatherPanel />
        </Window>

        {/* IDENTITY & PROGRESSION */}
        <Window id="score" title="Divine Record (Score)" icon={<Award size={14} />}>
           <ScorePanel />
        </Window>

        <Window id="attributes" title="Soul Essence (Attributes)" icon={<Fingerprint size={14} />}>
           <AttributesPanel />
        </Window>

        {/* Command Input (Bottom Floating) */}
        <div className="absolute bottom-6 left-1/2 -translate-x-1/2 w-full max-w-2xl px-6 z-[9999]">
           <div className="glass-panel p-1 rounded-full shadow-2xl border-white/10">
              <form onSubmit={handleSend} className="flex gap-2 p-1">
                 <div className="bg-slate-900/90 rounded-full px-5 flex items-center gap-4 flex-1 border border-white/5">
                    <Send size={16} className="text-blue-500" />
                    <input 
                      ref={inputRef}
                      type="text" 
                      value={inputCmd}
                      onChange={(e) => setInputCmd(e.target.value)}
                      placeholder="ENTER DIVINE COMMAND..."
                      className="flex-1 bg-transparent border-none outline-none text-white h-12 font-mono text-base tracking-wide"
                      autoFocus
                    />
                 </div>
              </form>
           </div>
        </div>

      </div>
    </div>
  );
}

export default App;
