import React, { useState, useEffect } from 'react';
import { useStore } from '../store/useStore';
import { sendEvent } from '../lib/socket';
import { 
  ShieldCheck, 
  Terminal, 
  Plus, 
  Search, 
  ChevronRight, 
  Database, 
  UserCog, 
  Box, 
  Ghost,
  X,
  RefreshCw,
  Zap,
  Terminal as StudioIcon
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { clsx } from 'clsx';

export default function AdminPanel() {
  const { isAdmin, adminCatalog, updateWindow, setWorkspace } = useStore();
  const [isOpen, setIsOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<'mobs' | 'items' | 'classes'>('mobs');
  const [search, setSearch] = useState('');

  // Auto-fetch catalog on open
  useEffect(() => {
    if (isOpen) {
      console.log("[ADMIN] Opening Nexus, requesting catalog...");
      sendEvent('admin:get_catalog');
    }
  }, [isOpen]);

  useEffect(() => {
    console.log("[ADMIN] catalog updated:", adminCatalog);
  }, [adminCatalog]);


  if (!isAdmin) return null;

  const filteredItems = (adminCatalog[activeTab] || []).filter(id => 
    id.toLowerCase().includes(search.toLowerCase())
  );

  const handleAction = (type: string, id: string) => {
    // Spawns/Modification events are sent to the backend
    if (type === 'mobs') sendEvent('admin:action', { cmd: '@spawn', id });
    if (type === 'items') sendEvent('admin:action', { cmd: '@spawn', id });
    if (type === 'classes') sendEvent('admin:action', { cmd: '@class', id });
  };

  const handleGlobalAction = (cmd: string) => {
     sendEvent('admin:action', { cmd });
  };

  return (
    <>
      {/* Nexus Trigger Button */}
      <div className="fixed bottom-4 left-4 z-[1000]">
        <button 
          onClick={() => setIsOpen(!isOpen)}
          className={clsx(
            "p-3 rounded-full shadow-2xl transition-all group border",
            isOpen ? "bg-red-500 border-red-400 rotate-90" : "bg-slate-900 border-white/10 hover:border-yellow-500/50"
          )}
        >
          {isOpen ? <X size={20} /> : <Terminal size={20} className="text-yellow-500 group-hover:scale-110" />}
        </button>
      </div>

      <AnimatePresence>
        {isOpen && (
          <motion.div 
            initial={{ x: -400, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: -400, opacity: 0 }}
            className="fixed left-0 top-0 bottom-0 w-80 bg-slate-900/95 backdrop-blur-xl border-r border-white/10 z-[999] shadow-2xl flex flex-col pt-4"
          >
            {/* Header */}
            <div className="px-6 py-4 flex items-center justify-between border-b border-white/5">
              <div className="flex items-center gap-2">
                <ShieldCheck size={18} className="text-red-500" />
                <span className="text-xs font-black uppercase tracking-widest text-white">Administrative Nexus</span>
              </div>
              <div className="flex items-center gap-2">
                <button 
                  onClick={() => { setWorkspace('studio'); setIsOpen(false); }}
                  className="p-1.5 rounded bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 hover:bg-cyan-500/20 transition-all"
                  title="Launch Studio Workspace"
                >
                  <StudioIcon size={14} />
                </button>
                <button onClick={() => setIsOpen(false)} className="text-slate-500 hover:text-white">
                   <X size={16} />
                </button>
              </div>
            </div>

            {/* Quick Actions (Nuke/Purge/Refresh) */}
            <div className="px-6 py-4 grid grid-cols-2 gap-2">
               <button 
                 onClick={() => handleGlobalAction('@purge')}
                 className="px-3 py-2 rounded bg-red-500/10 border border-red-500/20 text-[9px] font-black uppercase text-red-400 hover:bg-red-500/20"
               >
                  @PURGE
               </button>
               <button 
                 onClick={() => handleGlobalAction('@recruit all')}
                 className="px-3 py-2 rounded bg-yellow-500/10 border border-yellow-500/20 text-[9px] font-black uppercase text-yellow-400 hover:bg-yellow-500/20"
               >
                  @RECRUIT ALL
               </button>
            </div>

            {/* Tabs */}
            <div className="flex px-4 border-b border-white/5">
                {[
                  { id: 'mobs', icon: Ghost, label: 'Spawns' },
                  { id: 'items', icon: Box, label: 'Gear' },
                  { id: 'classes', icon: UserCog, label: 'Classes' }
                ].map(tab => (
                  <button
                    key={tab.id}
                    onClick={() => { setActiveTab(tab.id as any); setSearch(''); }}
                    className={clsx(
                      "flex-1 py-3 flex flex-col items-center gap-1 transition-all border-b-2",
                      activeTab === tab.id ? "border-yellow-500 bg-white/5" : "border-transparent text-slate-500 hover:text-white"
                    )}
                  >
                    <tab.icon size={14} />
                    <span className="text-[8px] font-black uppercase tracking-tighter">{tab.label}</span>
                  </button>
                ))}
            </div>

            {/* Search */}
            <div className="p-4">
               <div className="relative">
                 <Search size={12} className="absolute left-3 top-2.5 text-slate-600" />
                 <input 
                   type="text"
                   value={search}
                   onChange={(e) => setSearch(e.target.value)}
                   placeholder={`Filter ${activeTab}...`}
                   className="w-full bg-black/40 border border-white/5 rounded pl-9 pr-4 py-2 text-[10px] text-white focus:outline-none focus:border-yellow-500/50"
                 />
               </div>
            </div>

            {/* Content List */}
            <div className="flex-1 overflow-y-auto px-4 pb-6 custom-scrollbar">
               <div className="space-y-1">
                 {filteredItems.map(id => (
                   <button
                     key={id}
                     onClick={() => handleAction(activeTab, id)}
                     className="w-full text-left p-2 rounded hover:bg-white/5 group flex items-center justify-between border border-transparent hover:border-white/5 transition-all"
                   >
                      <div className="flex flex-col">
                        <span className="text-[10px] font-bold text-slate-300 group-hover:text-yellow-400 transition-colors uppercase truncate max-w-[180px]">
                           {id.replace(/_/g, ' ')}
                        </span>
                        <span className="text-[7px] text-slate-600 font-mono tracking-tighter">{id}</span>
                      </div>
                      <Plus size={12} className="text-slate-700 group-hover:text-green-500 opacity-0 group-hover:opacity-100 transition-opacity" />
                   </button>
                 ))}
               </div>
            </div>

            {/* Footer Status */}
            <div className="p-4 bg-black/40 border-t border-white/5">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                       <Zap size={10} className="text-yellow-500 animate-pulse" />
                       <span className="text-[8px] font-bold text-slate-500 uppercase tracking-widest">Divine Link Active</span>
                    </div>
                    <span className="text-[8px] font-mono text-slate-700">STABLE</span>
                </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
