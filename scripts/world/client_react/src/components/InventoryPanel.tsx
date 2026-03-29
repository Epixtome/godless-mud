import React from 'react';
import { useStore } from '../store/useStore';
import { sendCommand } from '../lib/ges';
import { Briefcase as Package, Shield, Sword, User, Plus } from 'lucide-react';
import { clsx } from 'clsx';
import { motion, Reorder } from 'framer-motion';

export function InventoryPanel() {
  const { status } = useStore();
  
  const inventory = status?.inventory || [];
  const equipment = status?.equipment || {};

  const handleEquip = (itemName: string) => {
    sendCommand(`equip ${itemName}`);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const itemName = e.dataTransfer.getData("itemName");
    if (itemName) handleEquip(itemName);
  };

  return (
    <div className="flex flex-col h-full bg-slate-950/40 rounded-lg overflow-hidden border border-white/5">
       {/* 1. EQUIPMENT GRID (Drop Target) */}
       <div 
         onDragOver={(e) => e.preventDefault()}
         onDrop={handleDrop}
         className="p-4 border-b border-white/5 bg-slate-900/40 relative group/equip"
       >
          <div className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-3 flex items-center gap-2">
             <Shield size={12} className="text-blue-400" />
             Divine Armaments
          </div>
          
          {/* Drop Overlay Hint */}
          <div className="absolute inset-0 bg-blue-500/10 border-2 border-dashed border-blue-500/30 opacity-0 group-hover/equip:opacity-100 pointer-events-none transition-opacity flex items-center justify-center">
             <span className="text-[8px] font-black text-blue-400 uppercase tracking-widest">Drop here to Equip</span>
          </div>

          <div className="grid grid-cols-2 gap-2">
             <EquipSlot label="Weapon" value={equipment.weapon} icon={<Sword size={12} />} />
             <EquipSlot label="Offhand" value={equipment.offhand} icon={<Shield size={12} />} />
             <EquipSlot label="Armor" value={equipment.armor} icon={<User size={12} />} />
             <EquipSlot label="Head" value={equipment.head} icon={<User size={12} />} />
          </div>
       </div>

       {/* 2. BACKPACK / INVENTORY */}
       <div className="flex-1 overflow-y-auto p-4 space-y-2 custom-scrollbar">
          <div className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-3 flex items-center gap-2">
             <Package size={12} className="text-emerald-400" />
             Backpack Content
          </div>
          
          {inventory.length > 0 ? (
             <div className="space-y-1">
                {inventory.map((item: any, idx: number) => (
                   <div 
                     key={item.id || idx}
                     draggable
                     onDragStart={(e) => {
                        e.dataTransfer.setData("itemName", item.name);
                        e.dataTransfer.effectAllowed = "move";
                     }}
                     onClick={() => sendCommand(`examine ${item.name}`)}
                     className="group flex items-center justify-between p-2 rounded bg-white/5 border border-transparent hover:border-emerald-500/30 hover:bg-emerald-500/5 transition-all cursor-grab active:cursor-grabbing"
                   >
                      <div className="flex items-center gap-3">
                         <span className="text-emerald-400 font-black text-sm w-4 text-center">{item.symbol || '?'}</span>
                         <span className="text-xs font-bold text-slate-300 group-hover:text-emerald-300">{item.name}</span>
                      </div>
                      <div className="flex items-center gap-3">
                        <button 
                          onClick={(e) => { e.stopPropagation(); handleEquip(item.name); }}
                          className="p-1 rounded bg-blue-500/10 text-blue-400 opacity-0 group-hover:opacity-100 hover:bg-blue-500/20 transition-all"
                          title="Equip Item"
                        >
                           <Plus size={10} />
                        </button>
                        <span className="text-[8px] text-slate-600 font-black uppercase opacity-0 group-hover:opacity-100 transition-opacity tracking-tighter">EXAMINE</span>
                      </div>
                   </div>
                ))}
             </div>
          ) : (
             <div className="h-32 flex flex-col items-center justify-center border border-dashed border-white/5 rounded gap-2 opacity-40">
                <Package size={20} className="text-slate-700" />
                <span className="text-[10px] text-slate-700 font-bold uppercase tracking-widest">Empty Resonance</span>
             </div>
          )}
       </div>
    </div>
  );
}

function EquipSlot({ label, value, icon }: { label: string, value: string | null, icon: React.ReactNode }) {
    const isEquipped = value && value !== "Unequipped" && value !== "None";
    return (
        <div className={clsx(
            "flex items-center gap-3 p-2 rounded border transition-all",
            isEquipped ? "bg-blue-500/10 border-blue-500/30" : "bg-slate-900/60 border-white/5 opacity-50"
        )}>
            <div className={clsx(
                "w-7 h-7 rounded flex items-center justify-center",
                isEquipped ? "bg-blue-500/20 text-blue-400" : "bg-slate-800 text-slate-600"
            )}>
                {icon}
            </div>
            <div className="flex flex-col min-w-0">
                <span className="text-[8px] font-black text-slate-500 uppercase tracking-tighter leading-none mb-1">{label}</span>
                <span className="text-[10px] font-bold text-slate-300 truncate leading-tight">
                    {isEquipped ? value : "NONE"}
                </span>
            </div>
        </div>
    );
}

export default InventoryPanel;
