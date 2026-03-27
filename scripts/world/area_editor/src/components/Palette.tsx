import { 
  Plus, 
  ChevronUp, 
  ChevronDown, 
  Ghost, 
  MousePointer2, 
  Eraser, 
  Square,
  Box,
  Layers,
  LayoutGrid
} from "lucide-react";
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface PaletteProps {
  activeTool: string;
  activeTemplateName: string;
  mobs: any[];
  currentZ: number;
  showGhost: boolean;
  onSelectTool: (tool: any) => void;
  onSelectTemplate: (template: any) => void;
  onUpdateZ: (delta: number) => void;
  onToggleGhost: () => void;
}

export default function Palette({
  activeTool,
  activeTemplateName,
  mobs,
  currentZ,
  showGhost,
  onSelectTool,
  onSelectTemplate,
  onUpdateZ,
  onToggleGhost,
}: PaletteProps) {
  return (
    <aside className="h-full flex flex-col bg-[#080808] border-r border-white/5 select-none overflow-hidden">
      <header className="h-10 border-b border-white/5 flex items-center justify-between px-4 bg-black/40 backdrop-blur-md">
        <div className="flex items-center gap-2">
          <LayoutGrid className="text-cyan-400" size={12} />
          <span className="font-black text-[10px] tracking-widest uppercase text-white glow-text-cyan">
            Palette Library
          </span>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto p-4 space-y-8 studio-scrollbar">
        {/* Manipulation Tools */}
        <section>
          <Header text="Tool Selection" icon={<MousePointer2 size={10} />} />
          <div className="grid grid-cols-2 gap-2">
            <ToolBtn 
                icon={<MousePointer2 size={14}/>} 
                active={activeTool === 'select'} 
                onClick={() => onSelectTool('select')} 
            />
            <ToolBtn 
                icon={<Eraser size={14}/>} 
                className="hover:text-red-500 hover:border-red-500/30" 
                active={activeTool === 'erase'} 
                onClick={() => onSelectTool('erase')} 
            />
          </div>
        </section>

        {/* Room Blueprints */}
        <section>
          <Header text="Room Blueprints" icon={<Square size={10} />} />
          <div className="grid grid-cols-2 gap-2">
            {["Void", "Temple", "Forest", "Sanctum", "Dungeon"].map(t => (
              <BlueprintBtn 
                  key={t} 
                  label={t} 
                  active={activeTemplateName.includes(t) && activeTool === 'paint'} 
                  onClick={() => {
                    onSelectTool('paint');
                    onSelectTemplate({
                        name: `Uncharted ${t}`,
                        description: `A dark, silent ${t.toLowerCase()} of unknown origin.`,
                        terrain: t.toLowerCase() === "temple" ? "holy" : (t.toLowerCase() === "forest" ? "forest" : "indoors"),
                        elevation: 0,
                        tags: []
                    });
                  }}
              />
            ))}
          </div>
        </section>

        {/* Entity Spawns */}
        <section>
          <Header text="Entity Spawns" icon={<Box size={10} />} />
          <div className="space-y-1">
            {mobs.slice(0, 10).map(m => (
              <div key={m.id} className="flex items-center justify-between p-2 rounded bg-white/3 border border-white/5 hover:bg-white/5 hover:border-cyan-500/20 cursor-pointer group transition-all">
                <span className="text-[10px] font-medium text-zinc-500 group-hover:text-zinc-300 transition-colors uppercase">{m.name}</span>
                <Plus size={10} className="text-zinc-800 group-hover:text-cyan-400" />
              </div>
            ))}
            {mobs.length === 0 && <span className="text-[9px] text-zinc-700 italic">No entities in flux.</span>}
          </div>
        </section>
      </div>

      {/* Persistence Controls */}
      <footer className="p-4 bg-black/60 border-t border-white/5 space-y-4">
        {/* Z-Plane */}
        <div>
          <div className="flex items-center justify-between mb-3">
             <span className="text-[9px] font-black text-zinc-600 uppercase tracking-widest flex items-center gap-2">
                <Layers size={10}/> Z-Plane Depth
             </span>
             <span className="text-[11px] font-mono text-cyan-400 font-bold glow-text-cyan">{currentZ}</span>
          </div>
          <div className="flex gap-1.5">
            <button 
                onClick={() => onUpdateZ(1)} 
                className="flex-1 p-2 bg-white/3 border border-white/5 rounded hover:bg-white/5 hover:border-cyan-500/20 text-zinc-600 hover:text-cyan-400 transition-all flex justify-center"
            >
                <ChevronUp size={14}/>
            </button>
            <button 
                onClick={() => onUpdateZ(-1)} 
                className="flex-1 p-2 bg-white/3 border border-white/5 rounded hover:bg-white/5 hover:border-cyan-500/20 text-zinc-600 hover:text-cyan-400 transition-all flex justify-center"
            >
                <ChevronDown size={14}/>
            </button>
          </div>
        </div>

        {/* Ghosting */}
        <button 
            onClick={onToggleGhost}
            className={cn("w-full p-2.5 rounded text-[9px] font-black uppercase tracking-tighter transition-all flex items-center justify-center gap-3 border shadow-[0_0_15px_rgba(0,0,0,0.5)]", 
                showGhost ? "bg-cyan-500/10 text-cyan-400 border-cyan-500/40 glow-border-cyan" : "bg-white/3 text-zinc-600 border-white/5")}
        >
            <Ghost size={12} className={showGhost ? "animate-pulse" : ""} /> 
            {showGhost ? "Ghosting: Visualized" : "Ghosting: Occulted"}
        </button>
      </footer>
    </aside>
  );
}

function Header({ text, icon }: { text: string, icon: React.ReactNode }) {
  return (
    <h3 className="text-[9px] font-black text-zinc-500 uppercase tracking-widest mb-4 flex items-center gap-2 border-b border-white/5 pb-1 opacity-80">
      {icon} {text}
    </h3>
  );
}

function ToolBtn({ icon, active, onClick, className }: { icon: React.ReactNode, active: boolean, onClick: () => void, className?: string }) {
  return (
    <button 
        onClick={onClick}
        className={cn(
            "p-3 rounded border transition-all flex justify-center", 
            active ? "bg-cyan-500/10 border-cyan-500/30 text-cyan-400 shadow-[0_0_15px_rgba(0,243,255,0.05)]" : "bg-white/3 border-white/5 text-zinc-600 hover:bg-white/5 hover:border-white/10",
            className
        )}
    >
        {icon}
    </button>
  );
}

function BlueprintBtn({ label, active, onClick }: { label: string, active: boolean, onClick: () => void }) {
  return (
    <button 
        onClick={onClick}
        className={cn(
            "p-2.5 rounded border text-[9px] font-black uppercase transition-all shadow-[0_0_10px_rgba(0,0,0,0.3)] text-left focus:outline-none",
            active ? "border-cyan-500/50 bg-cyan-500/10 text-cyan-400 glow-border-cyan" : "border-white/5 bg-white/3 text-zinc-500 hover:border-white/20 hover:text-zinc-300"
        )}
    >
        {label}
    </button>
  );
}
