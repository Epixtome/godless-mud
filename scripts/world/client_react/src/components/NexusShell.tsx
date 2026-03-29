import React, { useState, useRef } from 'react';
import { useStore } from '../store/useStore';
import { clsx } from 'clsx';
import { motion, AnimatePresence } from 'framer-motion';
import { sendCommand } from '../lib/ges';
import { 
  Shield, 
  Map as MapIcon, 
  MessageSquareText, 
  Activity, 
  Database, 
  Info,
  Settings,
  Send,
  Sun
} from 'lucide-react';

// Unified Components
import Viewport from './Viewport';
import CommLog from './CommLog';
import VitalsStack from './VitalsStack';
import RoomPanel from './RoomPanel';
import InventoryPanel from './InventoryPanel';
import ScorePanel from './ScorePanel';
import AttributesPanel from './AttributesPanel';
import CombatPanel from './CombatPanel';
import MenuBar from './MenuBar';

/**
 * [V10.9] Godless Nexus: The Command-First Interface
 * Narrow Sidebar Intelligence & Full-Height Vertical History.
 */
export const NexusShell = () => {
  const { status, setWorkspace } = useStore();
  const [activeTab, setActiveTab] = useState<'inventory' | 'score' | 'attributes'>('inventory');
  const [inputCmd, setInputCmd] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputCmd.trim()) return;
    sendCommand(inputCmd);
    setInputCmd('');
  };

  return (
    <div className="fixed inset-0 bg-[#020617] text-white flex flex-col font-sans overflow-hidden select-none pt-10">
      
      {/* 1. MASTER HEADER REMOVED - Using Global MenuBar */}

      {/* 2. THE THREE-PILLAR LAYOUT (Command-First) */}
      <main className="flex-1 flex overflow-hidden p-3 gap-3 relative bg-[#010309] items-stretch">
        
        {/* PILLAR 1: TACTICAL SIDEBAR (Narrow & Informative) */}
        <aside className="w-[320px] flex flex-col gap-3 shrink-0 h-full overflow-hidden">
            {/* The Compact Tactical Map (Zoomed for Side-View) */}
            <div className="h-[320px] rounded-3xl glass-panel relative overflow-hidden border border-white/10 bg-slate-950/40 shadow-2xl flex-none">
                <div className="absolute top-4 left-4 z-40 bg-black/80 px-2 py-1 rounded border border-white/10 shadow-lg pointer-events-none">
                  <span className="text-[8px] font-black uppercase tracking-[0.2em] text-cyan-500 italic">Tactical</span>
                </div>
                
                {/* Time/Weather Integrations */}
                <div className="absolute bottom-4 right-4 z-40 flex flex-col gap-1 items-end pointer-events-none">
                  <div className="bg-black/60 px-2 py-0.5 rounded border border-white/5 backdrop-blur-sm flex items-center gap-2">
                     <Sun size={8} className="text-cyan-400" />
                     <span className="text-[7px] font-black text-slate-400 uppercase tracking-widest">{status?.time || "N/A"}</span>
                  </div>
                </div>

                <div className="w-full h-full scale-[0.95] translate-y-3">
                   <Viewport radius={10} context="tactical" scale={1.1} />
                </div>
            </div>

            {/* Local Environment Awareness */}
            <div className="flex-1 rounded-3xl glass-panel relative overflow-hidden border border-white/5 bg-slate-950/20 shadow-xl flex flex-col min-h-0">
               <div className="p-4 border-b border-white/5 flex items-center justify-between bg-white/2">
                  <span className="text-[9px] font-black uppercase tracking-[0.2em] text-cyan-500/60 flex items-center gap-2">
                    <Info size={12} /> Local Intel
                  </span>
               </div>
               <div className="flex-1 overflow-auto custom-scrollbar">
                  <RoomPanel />
               </div>
            </div>
        </aside>

        {/* PILLAR 2: COMMAND HUB (Full-Height Terminal Focus) */}
        <section className="flex-1 flex flex-col min-w-[500px] h-full rounded-3xl overflow-hidden border border-white/10 bg-black/40 shadow-inner">
            <div className="flex-1 overflow-hidden relative">
               <CommLog />
            </div>
            
            {/* The Spiritual Input Bar */}
            <form onSubmit={handleSend} className="h-14 bg-slate-900/60 backdrop-blur-2xl border-t border-white/10 flex items-center px-6 gap-4 shrink-0 shadow-2xl">
               <span className="text-cyan-500 font-black text-sm animate-pulse">{'>'}</span>
               <input 
                  ref={inputRef}
                  type="text"
                  value={inputCmd}
                  onChange={(e) => setInputCmd(e.target.value)}
                  className="flex-1 bg-transparent border-none outline-none text-base text-slate-100 placeholder:text-slate-700 placeholder:uppercase placeholder:tracking-[0.3em] font-mono"
                  placeholder="Dispatch Spiritual Command..."
               />
               <button type="submit" className="w-10 h-10 rounded-xl bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-400 transition-all border border-cyan-500/20 flex items-center justify-center">
                  <Send size={16} />
               </button>
            </form>
        </section>

        {/* PILLAR 3: ENTITY HUB (Resource Monitoring) */}
        <aside className="w-[360px] flex flex-col gap-3 shrink-0 h-full overflow-hidden">
            {/* Scrollable Entity Intelligence */}
            <div className="flex-1 flex flex-col gap-3 overflow-y-auto custom-scrollbar pr-1 pb-4">
               {/* Ascendant Vitals */}
               <div className="flex-none rounded-3xl glass-panel relative overflow-hidden border border-white/5 bg-slate-950/40 shadow-xl p-5">
                  <div className="flex items-center justify-between mb-4">
                     <span className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 italic">Core Status</span>
                     <Activity size={12} className="text-cyan-500" />
                  </div>
                  <VitalsStack />
               </div>

               {/* Combat awareness (Manifestations) */}
               <div className="flex-none min-h-[160px] rounded-3xl glass-panel relative overflow-hidden border border-white/10 bg-red-950/10 shadow-xl p-1">
                  <CombatPanel />
               </div>

               {/* Inventory / Stats Tabs */}
               <div className="flex-none min-h-[460px] rounded-3xl glass-panel relative overflow-hidden border border-white/5 bg-slate-950/40 shadow-xl flex flex-col">
                  <div className="flex border-b border-white/5 bg-black/20">
                     <button 
                        onClick={() => setActiveTab('inventory')}
                        className={clsx("flex-1 py-4 text-[9px] font-black uppercase tracking-widest transition-all", activeTab === 'inventory' ? "text-cyan-400 border-b-2 border-cyan-500 bg-white/5" : "text-slate-500 hover:text-white")}
                     >Items</button>
                     <button 
                        onClick={() => setActiveTab('score')}
                        className={clsx("flex-1 py-4 text-[9px] font-black uppercase tracking-widest transition-all", activeTab === 'score' ? "text-cyan-400 border-b-2 border-cyan-500 bg-white/5" : "text-slate-500 hover:text-white")}
                     >Ancestry</button>
                     <button 
                        onClick={() => setActiveTab('attributes')}
                        className={clsx("flex-1 py-4 text-[9px] font-black uppercase tracking-widest transition-all", activeTab === 'attributes' ? "text-cyan-400 border-b-2 border-cyan-500 bg-white/5" : "text-slate-500 hover:text-white")}
                     >Attributes</button>
                  </div>
                  <div className="flex-1 p-1 overflow-hidden">
                     <AnimatePresence mode="wait">
                        {activeTab === 'inventory' && (
                           <motion.div key="inv" initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0 }} className="h-full">
                              <InventoryPanel />
                           </motion.div>
                        )}
                        {activeTab === 'score' && (
                           <motion.div key="score" initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0 }} className="h-full">
                              <AttributesPanel />
                           </motion.div>
                        )}
                        {activeTab === 'attributes' && (
                           <motion.div key="attrs" initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0 }} className="h-full">
                              <ScorePanel />
                           </motion.div>
                        )}
                     </AnimatePresence>
                  </div>
               </div>
            </div>
        </aside>

      </main>

      {/* FOOTER SUB-STATION */}
      <footer className="h-4 bg-slate-950 border-t border-white/5 flex items-center px-6 shrink-0 z-50">
          <div className="flex items-center gap-2 opacity-30 grayscale hover:grayscale-0 transition-all">
             <div className="w-1 h-1 rounded-full bg-cyan-500" />
             <span className="text-[7px] font-black text-slate-500 uppercase tracking-widest">Protocol V10.9 Active</span>
          </div>
      </footer>
    </div>
  );
};
