import React from 'react';
import { clsx } from 'clsx';

interface ProgressBarProps {
  current: number;
  max: number;
  colorClassName?: string;
  label?: string;
  size?: 'sm' | 'md' | 'lg';
  showValues?: boolean;
}

export const ProgressBar = ({ 
  current, 
  max, 
  colorClassName = "bg-blue-500", 
  label, 
  size = 'md',
  showValues = false
}: ProgressBarProps) => {
  const percentage = Math.min(100, Math.max(0, (current / (max || 1)) * 100));
  
  const heightMap = {
    sm: 'h-1',
    md: 'h-2.5',
    lg: 'h-4'
  };

  return (
    <div className="w-full space-y-1">
      {(label || showValues) && (
        <div className="flex justify-between items-end">
          {label && <div className="text-[9px] font-black text-slate-500 uppercase tracking-tighter">{label}</div>}
          {showValues && <div className="text-[10px] font-bold text-white shadow-sm">{current}/{max}</div>}
        </div>
      )}
      <div className={clsx(
        "bg-slate-900/40 rounded-full overflow-hidden border border-white/5",
        heightMap[size]
      )}>
        <div 
          className={clsx("h-full transition-all duration-300", colorClassName)}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};

export default ProgressBar;
