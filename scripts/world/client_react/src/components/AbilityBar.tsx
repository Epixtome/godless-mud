import React, { useState, useEffect } from 'react';
import { useStore } from '../store/useStore';
import { sendCommand } from '../lib/ges';
import { Zap } from 'lucide-react';
import { Reorder, AnimatePresence } from 'framer-motion';
import { AbilityButton } from './AbilityButton';

export function AbilityBar() {
  const { status } = useStore();
  const blessings = status?.blessings || [];
  const [items, setItems] = useState<any[]>([]);

  // Sync with store but allow local reordering
  useEffect(() => {
      if (blessings.length > 0 && items.length === 0) {
          setItems(blessings);
      } else if (blessings.length !== items.length) {
          // If the deck changed from backend, merge or reset
          setItems(blessings);
      }
  }, [blessings]);

  const handleCast = (id: string, ready: boolean) => {
    if (!ready) return;
    sendCommand(`cast ${id}`);
  };

  if (blessings.length === 0) return (
     <div className="w-full h-full flex items-center justify-center p-8 border-2 border-dashed border-slate-900/40 rounded-xl">
        <div className="text-center">
            <Zap size={24} className="mx-auto text-slate-800 mb-2 animate-pulse" />
            <p className="text-[10px] font-black text-slate-700 uppercase tracking-[0.2em]">Kit Not Synchronized</p>
        </div>
     </div>
  );

  return (
    <Reorder.Group 
        axis="y" 
        values={items} 
        onReorder={setItems}
        className="w-full h-full p-2 grid grid-cols-[repeat(auto-fill,minmax(60px,1fr))] auto-rows-max gap-2 overflow-y-auto"
    >
      <AnimatePresence>
      {items.map((b: any) => (
        <Reorder.Item 
          value={b}
          key={b.id}
          className="relative"
        >
          <AbilityButton ability={b} onCast={handleCast} />
        </Reorder.Item>
      ))}
      </AnimatePresence>
    </Reorder.Group>
  );
}

export default AbilityBar;
