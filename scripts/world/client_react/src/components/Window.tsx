import React, { useEffect, useRef, useState } from 'react';
import { motion, useDragControls } from 'framer-motion';
import { useStore } from '../store/useStore';
import { Maximize2, Minimize2, ZoomIn, ZoomOut, Pin, PinOff } from 'lucide-react';
import { clsx } from 'clsx';

interface WindowProps {
  id: string;
  title: string;
  icon?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

export const Window = ({ id, title, icon, children, className }: WindowProps) => {
  const { windows, focusWindow, updateWindow, saveLayoutToServer } = useStore();
  const config = windows[id];
  const windowRef = useRef<HTMLDivElement>(null);
  const controls = useDragControls();
  const [isResizing, setIsResizing] = useState(false);

  if (!config || !config.isVisible) return null;

  const handleZoom = (delta: number) => {
    updateWindow(id, { scale: Math.max(0.5, Math.min(2, config.scale + delta)) });
  };

  const togglePin = () => {
      updateWindow(id, { isPinned: !config.isPinned });
  };

  const snapValue = 12;
  const magneticThreshold = 20;

  // Custom Resize Logic (Bug 14 Resolution)
  const onResizeStart = (e: React.MouseEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsResizing(true);
      
      const startX = e.clientX;
      const startY = e.clientY;
      const startW = config.width;
      const startH = config.height;

      const onMouseMove = (moveEvent: MouseEvent) => {
          const deltaX = moveEvent.clientX - startX;
          const deltaY = moveEvent.clientY - startY;
          
          updateWindow(id, {
              width: Math.max(200, startW + deltaX),
              height: Math.max(120, startH + deltaY)
          });
      };

      const onMouseUp = () => {
          setIsResizing(false);
          saveLayoutToServer();
          document.removeEventListener('mousemove', onMouseMove);
          document.removeEventListener('mouseup', onMouseUp);
      };

      document.addEventListener('mousemove', onMouseMove);
      document.addEventListener('mouseup', onMouseUp);
  };

  return (
    <motion.div
      ref={windowRef}
      drag={!config.isPinned && !isResizing}
      dragListener={false}
      dragControls={controls}
      dragElastic={0}
      dragMomentum={false}
      onDragStart={() => focusWindow(id)}
      onDragEnd={(event, info) => {
          // [BUG 17 FIX] Robust coordinate persistence
          const newX = config.x + info.offset.x;
          const newY = config.y + info.offset.y;

          // Snapping (Grid 12px)
          const snappedX = Math.round(newX / snapValue) * snapValue;
          const snappedY = Math.round(newY / snapValue) * snapValue;

          updateWindow(id, { x: snappedX, y: snappedY });
          saveLayoutToServer();
      }}
      initial={{ 
          x: config.x, 
          y: config.y,
          opacity: 0 
      }}
      animate={{ 
          x: config.x, 
          y: config.y,
          opacity: 1,
          scale: 1,
          width: config.width,
          height: config.height
      }}
      // Use Tween with very short duration ONLY for manual sync.
      // Set duration to 0 if resizing to avoid the "Floating" effect.
      transition={{ 
          type: 'tween', 
          duration: isResizing ? 0 : 0.1, 
          ease: 'easeOut'
      }}
      style={{ 
          zIndex: config.zIndex,
          position: 'absolute',
          left: 0,
          top: 0,
          overflow: 'hidden',
          cursor: isResizing ? 'nwse-resize' : 'default'
      }}
      className={clsx(
        "glass-panel rounded-xl flex flex-col shadow-2xl border-white/5",
        "transition-shadow active:shadow-purple-500/20 active:border-purple-500/30",
        config.isPinned && "border-blue-500/30 shadow-blue-500/5",
        className
      )}
    >
      {/* Header / Drag Handle */}
      <div 
        className={clsx(
            "bg-slate-900/60 px-4 py-3 border-b border-white/5 flex justify-between items-center select-none shrink-0",
            !config.isPinned ? "cursor-grab active:cursor-grabbing" : "cursor-default"
        )}
        onPointerDown={(e) => {
            focusWindow(id);
            if (!config.isPinned) controls.start(e);
        }}
      >
        <div className="flex items-center gap-3">
          {icon && <div className={clsx("transition-colors", config.isPinned ? "text-blue-400" : "text-purple-400")}>{icon}</div>}
          <span className="text-[11px] font-black text-slate-200 uppercase tracking-[0.2em]">{title}</span>
        </div>
        
        <div className="flex items-center gap-2">
          {/* Zoom Controls (Contextual) */}
          {(id === 'tactical' || id === 'mini') && (
            <div className="flex items-center gap-1 mr-2 px-2 py-1 bg-black/30 rounded-md border border-white/5">
              <button 
                onClick={(e) => { e.stopPropagation(); handleZoom(-0.1); }} 
                className="text-slate-500 hover:text-white transition-colors"
              >
                <ZoomOut size={12} />
              </button>
              <span className="text-[9px] font-mono text-slate-400 w-8 text-center">{Math.round(config.scale * 100)}%</span>
              <button 
                onClick={(e) => { e.stopPropagation(); handleZoom(0.1); }} 
                className="text-slate-500 hover:text-white transition-colors"
              >
                <ZoomIn size={12} />
              </button>
            </div>
          )}

          <button 
            onClick={(e) => { e.stopPropagation(); togglePin(); }}
            className={clsx(
                "p-1 rounded transition-colors",
                config.isPinned ? "text-blue-400 bg-blue-500/10" : "text-slate-500 hover:text-white"
            )}
          >
            {config.isPinned ? <Pin size={14} /> : <PinOff size={14} />}
          </button>
        </div>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-auto bg-slate-950/20">
        {React.Children.map(children, child => {
            if (React.isValidElement(child) && (id === 'tactical' || id === 'mini')) {
                return React.cloneElement(child as React.ReactElement<any>, { scale: config.scale });
            }
            return child;
        })}
      </div>

      {/* Manual Resize Handle (Bug 14 Resolution) */}
      {!config.isPinned && (
          <div 
            onMouseDown={onResizeStart}
            className="absolute bottom-0 right-0 w-6 h-6 cursor-nwse-resize group flex items-center justify-center"
          >
              <div className="w-2 h-2 border-r-2 border-b-2 border-white/20 group-hover:border-purple-500 transition-colors" />
          </div>
      )}
    </motion.div>
  );
};

export default Window;
