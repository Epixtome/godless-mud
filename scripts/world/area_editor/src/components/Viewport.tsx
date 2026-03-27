import { 
  useRef, 
  useEffect, 
  useState 
} from "react";
import { 
  Square, 
  MousePointer2, 
  RefreshCw, 
  Compass, 
  Eraser, 
  Plus, 
  Box,
  Monitor,
  Maximize2
} from "lucide-react";
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface ViewportProps {
  canvasRef: React.RefObject<HTMLCanvasElement | null>;
  selectedPos: { x: number, y: number } | null;
  hoverPos: { x: number, y: number } | null;
  currentZ: number;
  activeTool: string;
  pan: { x: number, y: number };
  zoom: number;
  onMouseDown: (e: React.MouseEvent) => void;
  onMouseMove: (e: React.MouseEvent) => void;
  onMouseUp: () => void;
  onWheel: (e: React.WheelEvent) => void;
  onResetView: () => void;
  onSelectTool: (tool: string) => void;
}

export default function Viewport({
  canvasRef,
  selectedPos,
  hoverPos,
  currentZ,
  activeTool,
  pan,
  zoom,
  onMouseDown,
  onMouseMove,
  onMouseUp,
  onWheel,
  onResetView,
  onSelectTool
}: ViewportProps) {
  return (
    <main className="flex-1 relative flex flex-col bg-[#050505] overflow-hidden select-none cursor-crosshair">
      {/* Viewport Header */}
      <header className="h-10 border-b border-white/5 px-4 flex items-center justify-between bg-black/60 backdrop-blur-xl z-20">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <span className="text-cyan-400 font-black tracking-tighter text-[11px] glow-text-cyan">VISUAL_ENGINE_V1.1</span>
            <div className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse-cyan shadow-[0_0_10px_rgba(0,243,255,1)]" />
          </div>
          <div className="h-4 w-px bg-white/5" />
          <div className="text-[10px] font-mono text-zinc-500 flex items-center gap-3">
             <div className="flex items-center gap-1.5 border-r border-white/5 pr-3">
               <Compass size={11} className="text-zinc-600"/> 
               <span className="text-white/40 uppercase">LOC:</span> 
               {selectedPos ? (
                 <span className="text-cyan-400 font-bold">{selectedPos.x}, {selectedPos.y}, {currentZ}</span>
               ) : (
                 <span className="text-zinc-600 italic">{hoverPos ? `${hoverPos.x}, ${hoverPos.y}, ${currentZ}` : `---`}</span>
               )}
             </div>
             <div className="flex items-center gap-1.5 border-r border-white/5 pr-3"><span className="text-white/40 uppercase">ZOOM:</span> {Math.round(zoom * 100)}%</div>
             <div className="flex items-center gap-1.5"><span className="text-white/40 uppercase">OFFSET:</span> {Math.round(pan.x)}, {Math.round(pan.y)}</div>
          </div>
        </div>

        <div className="flex items-center gap-1.5 text-zinc-600">
           <button 
                onClick={onResetView} 
                className="p-1.5 hover:bg-white/5 rounded hover:text-white transition-all border border-transparent hover:border-white/5" 
                title="Synchronize View"
            >
                <RefreshCw size={12}/>
            </button>
            <button className="p-1.5 hover:bg-white/5 rounded hover:text-white transition-all border border-transparent hover:border-white/5"><Monitor size={12}/></button>
            <button className="p-1.5 hover:bg-white/5 rounded hover:text-white transition-all border border-transparent hover:border-white/5"><Maximize2 size={12}/></button>
        </div>
      </header>

      {/* Main Canvas Context */}
      <canvas 
        ref={canvasRef}
        onMouseDown={onMouseDown}
        onMouseMove={onMouseMove}
        onMouseUp={onMouseUp}
        onMouseLeave={onMouseUp}
        onWheel={onWheel}
        onContextMenu={(e) => e.preventDefault()}
        className="flex-1 w-full h-full bg-[#030303]"
      />

      {/* Floating Tactical Switcher (Snapping Control) */}
      <div className="absolute bottom-6 left-1/2 -translate-x-1/2 flex items-center p-1.5 glass-panel rounded-full border-white/10 shadow-[0_15px_35px_rgba(0,0,0,0.8)] z-30 glow-border-cyan backdrop-blur-2xl">
        <OverlayBtn 
            icon={<MousePointer2 size={16} />} 
            active={activeTool === 'select'} 
            onClick={() => onSelectTool('select')} 
            glow="cyan"
        />
        <OverlayBtn 
            icon={<Square size={16} />} 
            active={activeTool === 'paint'} 
            onClick={() => onSelectTool('paint')} 
             glow="cyan"
        />
        <OverlayBtn 
            icon={<Eraser size={16} />} 
            active={activeTool === 'erase'} 
            onClick={() => onSelectTool('erase')} 
            glow="red"
        />
        <div className="w-px h-6 bg-white/5 mx-2" />
        <OverlayBtn icon={<Plus size={16} />} active={false} onClick={() => {}} />
        <OverlayBtn icon={<Box size={16} />} active={false} onClick={() => {}} />
      </div>

      {/* Ambient Grid Vignet */}
      <div className="absolute inset-0 pointer-events-none border border-white/5 pointer-events-none shadow-[inset_0_0_100px_rgba(0,0,0,0.5)] z-10" />
    </main>
  );
}

function OverlayBtn({ icon, active, onClick, glow = "cyan" }: { icon: React.ReactNode, active: boolean, onClick: () => void, glow?: "cyan" | "red" }) {
  const glowStyles = {
    cyan: "bg-cyan-500 text-black shadow-[0_0_15px_rgba(0,243,255,0.4)]",
    red: "bg-red-500 text-white shadow-[0_0_15px_rgba(255,0,0,0.4)]"
  };

  return (
    <button 
        onClick={onClick}
        className={cn(
            "p-2.5 rounded-full transition-all duration-300 transform font-bold mx-0.5",
            active ? glowStyles[glow] + " scale-110" : "text-zinc-500 hover:text-white hover:bg-white/5"
        )}
    >
        {icon}
    </button>
  );
}
