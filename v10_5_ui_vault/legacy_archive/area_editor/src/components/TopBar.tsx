import { 
  Menu, 
  Save, 
  FolderOpen, 
  Settings, 
  Layout, 
  Maximize2, 
  Monitor, 
  Zap, 
  Info,
  ChevronDown
} from "lucide-react";

interface TopBarProps {
  onSave: () => void;
  onOpen: () => void;
  onToggleView: (view: string) => void;
  activeViews: Record<string, boolean>;
}

export default function TopBar({ onSave, onOpen, onToggleView, activeViews }: TopBarProps) {
  return (
    <header className="h-10 border-b border-white/5 bg-[#0a0a0a] flex items-center justify-between px-3 select-none z-50">
      <div className="flex items-center gap-6">
        {/* Brand */}
        <div className="flex items-center gap-2 pr-4 border-r border-white/5">
          <div className="w-5 h-5 bg-cyan-500 rounded flex items-center justify-center text-black font-black text-[10px] shadow-[0_0_10px_rgba(0,243,255,0.4)]">
            GA
          </div>
          <span className="text-[11px] font-black tracking-widest text-white glow-text-cyan">
            GODLESS_STUDIO
          </span>
        </div>

        {/* Menus */}
        <nav className="flex items-center gap-4">
          <MenuButton label="File">
            <MenuItem icon={<FolderOpen size={12}/>} label="Open Manifest..." shortcut="Ctrl+O" onClick={onOpen} />
            <MenuItem icon={<Save size={12}/>} label="Sync to Server" shortcut="Ctrl+S" onClick={onSave} />
          </MenuButton>
          
          <MenuButton label="View">
            <ToggleMenuItem 
                label="Palette Library" 
                active={activeViews.palette} 
                onClick={() => onToggleView('palette')} 
            />
            <ToggleMenuItem 
                label="Inspector Node" 
                active={activeViews.inspector} 
                onClick={() => onToggleView('inspector')} 
            />
             <div className="h-px bg-white/5 my-1" />
             <MenuItem icon={<Layout size={12}/>} label="Reset Layout" onClick={() => {}} />
          </MenuButton>

          <MenuButton label="Systems">
            <MenuItem icon={<Settings size={12}/>} label="Preferences" onClick={() => {}} />
            <MenuItem icon={<Monitor size={12}/>} label="Server Status" onClick={() => {}} />
          </MenuButton>
        </nav>
      </div>

      <div className="flex items-center gap-4">
         {/* Live Indicator */}
         <div className="flex items-center gap-2 px-2 py-1 bg-cyan-500/5 border border-cyan-500/20 rounded-full">
            <div className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse-cyan" />
            <span className="text-[9px] font-black text-cyan-400/80 uppercase">Biotically Synchronized</span>
         </div>

         {/* Utility Icons */}
         <div className="flex items-center gap-1 text-zinc-500">
            <button className="p-1.5 hover:text-white transition-colors"><Zap size={14}/></button>
            <button className="p-1.5 hover:text-white transition-colors"><Maximize2 size={14}/></button>
            <button className="p-1.5 hover:text-white transition-colors"><Info size={14}/></button>
         </div>
      </div>
    </header>
  );
}

function MenuButton({ label, children }: { label: string, children: React.ReactNode }) {
  return (
    <div className="relative group px-2 py-1 cursor-pointer">
      <div className="flex items-center gap-1 text-[10px] font-bold text-zinc-400 group-hover:text-white transition-colors uppercase tracking-wider">
        {label} <ChevronDown size={10} className="text-zinc-600"/>
      </div>
      <div className="absolute top-full left-0 mt-1 w-48 bg-[#121212] border border-white/10 rounded-lg shadow-2xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all py-1 z-[100] backdrop-blur-xl">
        {children}
      </div>
    </div>
  );
}

function MenuItem({ icon, label, shortcut, onClick }: { icon: React.ReactNode, label: string, shortcut?: string, onClick?: () => void }) {
  return (
    <button 
      onClick={onClick}
      className="w-full flex items-center justify-between px-3 py-1.5 hover:bg-cyan-500/10 text-zinc-400 hover:text-white transition-all text-left"
    >
      <div className="flex items-center gap-3">
         <span className="text-cyan-400">{icon}</span>
         <span className="text-[10px] font-bold tracking-tight">{label}</span>
      </div>
      {shortcut && <span className="text-[9px] text-zinc-600 font-mono">{shortcut}</span>}
    </button>
  );
}

function ToggleMenuItem({ label, active, onClick }: { label: string, active: boolean, onClick: () => void }) {
  return (
    <button 
      onClick={onClick}
      className="w-full flex items-center justify-between px-3 py-1.5 hover:bg-white/5 text-zinc-400 hover:text-white transition-all text-left"
    >
      <span className="text-[10px] font-bold tracking-tight">{label}</span>
      <div className={`w-3 h-3 rounded-full border border-white/10 flex items-center justify-center ${active ? 'bg-cyan-500 border-transparent shadow-[0_0_5px_rgba(0,243,255,0.3)]' : ''}`}>
        {active && <div className="w-1 h-1 bg-black rounded-full" />}
      </div>
    </button>
  );
}
