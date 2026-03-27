import React, { useEffect, useRef, useCallback } from 'react';
import { useStore } from '../store/useStore';
import { MessageSquareText } from 'lucide-react';
import AnsiText from './AnsiText';

export function CommLog() {
  const { logs } = useStore();
  const listRef = useRef<HTMLDivElement>(null);

  // Auto-Scroll to Bottom
  useEffect(() => {
     if (listRef.current) {
        listRef.current.scrollTop = listRef.current.scrollHeight;
     }
  }, [logs]);

  // Page Navigation Listeners (v8.7)
  const handlePageScroll = useCallback((e: KeyboardEvent) => {
    if (!listRef.current) return;
    
    const scrollAmount = listRef.current.clientHeight * 0.8;
    if (e.key === 'PageUp') {
        listRef.current.scrollTop -= scrollAmount;
    } else if (e.key === 'PageDown') {
        listRef.current.scrollTop += scrollAmount;
    }
  }, []);

  useEffect(() => {
    window.addEventListener('keydown', handlePageScroll);
    return () => window.removeEventListener('keydown', handlePageScroll);
  }, [handlePageScroll]);

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden bg-slate-950/40 relative">
       {/* Scrolling Container */}
       <div 
          ref={listRef} 
          className="flex-1 overflow-y-auto p-6 pt-12 space-y-1 font-mono text-[13px] leading-relaxed scroll-smooth"
       >
          {logs.map((log, idx) => (
             <div key={idx} className="flex gap-4 group">
                <span className="text-white/10 select-none group-hover:text-white/20 transition-colors w-18 text-[9px] mt-1 shrink-0 font-bold">[{log.timestamp}]</span>
                <AnsiText text={log.text} />
             </div>
          ))}
          <div className="h-6 shrink-0" />
       </div>

       {/* Floating Title (Glass Overlay) */}
       <div className="absolute top-0 left-0 right-0 bg-slate-900/60 backdrop-blur-md px-4 py-2 border-b border-white/5 flex gap-2 items-center z-10">
          <MessageSquareText size={12} className="text-purple-400" />
          <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Divine Command History</span>
       </div>
    </div>
  );
}

export default CommLog;
