import { 
  Info, 
  X, 
  Type, 
  Type as DescriptionIcon, 
  Layers, 
  Hash, 
  Trash2, 
  Plus, 
  Box,
  ChevronDown
} from "lucide-react";
import type { Room, ZoneMetadata } from "../types";

interface InspectorProps {
  selectedRoom: Room | null;
  metadata: ZoneMetadata;
  terrain: any;
  onUpdateRoom: (room: Partial<Room>) => void;
  onClose: () => void;
}

export default function Inspector({ selectedRoom, metadata, terrain, onUpdateRoom, onClose }: InspectorProps) {
  return (
    <aside className="h-full flex flex-col bg-[#080808] border-l border-white/5 select-none overflow-hidden">
      <header className="h-10 border-b border-white/5 flex items-center justify-between px-4 bg-black/40 backdrop-blur-md">
        <div className="flex items-center gap-2">
          <Info className="text-cyan-400" size={12} />
          <span className="font-black text-[10px] tracking-widest uppercase text-white glow-text-cyan">
            Inspector Node
          </span>
        </div>
        <button 
          onClick={onClose}
          className="p-1.5 hover:bg-white/5 rounded-full text-zinc-600 hover:text-white transition-all"
        >
          <X size={12} />
        </button>
      </header>

      {selectedRoom ? (
        <div className="flex-1 overflow-y-auto p-5 space-y-8 studio-scrollbar">
          {/* Room Name */}
          <section>
            <Label icon={<Type size={10} />} text="Room Identity" />
            <Input 
                value={selectedRoom.name} 
                onChange={(v) => onUpdateRoom({ name: v })} 
            />
          </section>

          {/* Room Description */}
          <section>
            <Label icon={<DescriptionIcon size={10} />} text="Visonic Flux Description" />
            <Textarea 
                value={selectedRoom.description} 
                onChange={(v) => onUpdateRoom({ description: v })} 
            />
          </section>

          {/* Attributes */}
          <section className="grid grid-cols-2 gap-4">
            <div>
              <Label text="Sector Plane" />
              <Select 
                  value={selectedRoom.terrain} 
                  options={Object.keys(terrain.multipliers || {})} 
                  onChange={(v) => onUpdateRoom({ terrain: v })} 
              />
            </div>
            <div>
              <Label text="Elevation" />
              <NumberInput 
                  value={selectedRoom.elevation} 
                  onChange={(v) => onUpdateRoom({ elevation: v })} 
              />
            </div>
          </section>

          {/* Trigger Tags */}
          <section>
            <div className="flex items-center justify-between mb-3 border-b border-white/5 pb-1">
                <Label icon={<Hash size={10} />} text="Triggers & Tags" />
                <Plus size={10} className="text-zinc-600 hover:text-cyan-400 cursor-pointer" />
            </div>
            <div className="space-y-2">
                {selectedRoom.tags.map((tag, i) => (
                    <div key={i} className="flex items-center gap-2 text-[10px] bg-white/3 p-2 rounded border border-white/5 group hover:border-cyan-500/20 transition-all">
                        <span className="flex-1 font-mono text-zinc-500 group-hover:text-zinc-300">{tag}</span>
                        <Trash2 size={10} className="text-zinc-800 opacity-0 group-hover:opacity-100 hover:text-red-500 cursor-pointer transition-all" />
                    </div>
                ))}
                {selectedRoom.tags.length === 0 && <span className="text-[9px] text-zinc-700 italic">No divine pings active.</span>}
            </div>
          </section>

          {/* Entities Inspector Snippet */}
          <section>
            <Label icon={<Layers size={10} />} text="Entity Occupants" />
            <div className="p-3 bg-white/2 border border-dashed border-white/10 rounded-lg flex flex-col items-center gap-2">
                <Box size={24} className="text-zinc-800" />
                <span className="text-[9px] text-zinc-600 uppercase font-bold">No Entities in Flux</span>
            </div>
          </section>
        </div>
      ) : (
        <div className="flex-1 flex flex-col items-center justify-center p-12 opacity-10 select-none bg-black/40">
           <Layers size={64} className="mb-4 text-cyan-400" />
           <p className="text-[10px] font-black uppercase tracking-widest text-center text-white">No Sector Node Latched</p>
           <p className="text-[9px] text-center mt-2 max-w-[180px] leading-relaxed">Select a coordinate on the map to interact with its machine spirit.</p>
        </div>
      )}

      {/* Persistence Footer */}
      <footer className="p-4 bg-black/60 border-t border-white/5 mt-auto">
         <div className="flex items-center justify-between mb-3">
             <span className="text-[10px] font-black text-white/50 uppercase tracking-widest">{metadata.name} Manifest</span>
             <span className="text-[9px] font-mono text-zinc-700">COORD: {selectedRoom?.x ?? 0}, {selectedRoom?.y ?? 0}, {selectedRoom?.z ?? 0}</span>
         </div>
         <div className="grid grid-cols-2 gap-2">
             <button className="px-3 py-1.5 bg-white/3 border border-white/5 rounded text-[8px] font-bold uppercase hover:bg-white/10 text-zinc-500 hover:text-white transition-all">Export JSON</button>
             <button className="px-3 py-1.5 bg-cyan-500/20 border border-cyan-500/30 rounded text-[8px] font-bold uppercase text-cyan-400 hover:bg-cyan-500/30 shadow-[0_0_15px_rgba(0,243,255,0.05)] transition-all">Deploy Changes</button>
         </div>
      </footer>
    </aside>
  );
}

function Label({ icon, text }: { icon?: React.ReactNode, text: string }) {
  return (
    <label className="text-[9px] font-black text-zinc-600 uppercase flex items-center gap-2 mb-2 tracking-wider">
      {icon} {text}
    </label>
  );
}

function Input({ value, onChange }: { value: string, onChange: (v: string) => void }) {
  return (
    <input 
      type="text" 
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="w-full bg-white/5 border border-white/10 rounded px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500/50 transition-all font-bold placeholder-white/20"
    />
  );
}

function Textarea({ value, onChange }: { value: string, onChange: (v: string) => void }) {
  return (
    <textarea 
       rows={4}
       value={value}
       onChange={(e) => onChange(e.target.value)}
       className="w-full bg-white/5 border border-white/10 rounded px-3 py-2 text-[11px] text-zinc-400 focus:outline-none focus:border-cyan-500/50 transition-all resize-none leading-relaxed studio-scrollbar"
    />
  );
}

function Select({ value, options, onChange }: { value: string, options: string[], onChange: (v: string) => void }) {
  return (
    <div className="relative group">
        <select 
            value={value}
            onChange={(e) => onChange(e.target.value)}
            className="w-full appearance-none bg-white/5 border border-white/10 rounded px-2 py-1.5 text-[9px] font-bold text-white focus:outline-none group-hover:border-cyan-500/30 transition-all"
        >
            {options.map(o => <option key={o} value={o} className="bg-[#121212]">{o.toUpperCase()}</option>)}
        </select>
        <ChevronDown size={10} className="absolute right-2 top-1/2 -translate-y-1/2 text-zinc-600 pointer-events-none" />
    </div>
  );
}

function NumberInput({ value, onChange }: { value: number, onChange: (v: number) => void }) {
  return (
    <input 
      type="number" 
      value={value}
      onChange={(e) => onChange(parseInt(e.target.value || '0'))}
      className="w-full bg-white/5 border border-white/10 rounded px-2 py-1.5 text-[10px] text-white focus:outline-none focus:border-cyan-500/50 transition-all font-mono"
    />
  );
}
