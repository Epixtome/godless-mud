"use client";

import React from "react";

interface PaletteProps {
  activeTool: string;
  setActiveTool: (tool: string) => void;
  brushRadius: number;
  setBrushRadius: (r: number) => void;
  categories: Record<string, string[]>;
}

export const Palette: React.FC<PaletteProps> = ({
  activeTool,
  setActiveTool,
  brushRadius,
  setBrushRadius,
  categories,
}) => {
  return (
    <div className="flex flex-col gap-6 p-4 h-full bg-zinc-900 border-r border-zinc-800 shadow-xl overflow-y-auto w-64">
      <h2 className="text-sm font-bold tracking-widest text-[#00bcd4] uppercase">--- Palette ---</h2>
      
      {Object.entries(categories).map(([category, tools]) => (
        <div key={category} className="space-y-2">
          <h3 className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider">{category}</h3>
          <div className="grid grid-cols-2 gap-1">
            {tools.map((tool) => (
              <button
                key={tool}
                onClick={() => setActiveTool(tool)}
                className={`px-2 py-1.5 text-[10px] font-bold uppercase transition-all rounded ${
                  activeTool === tool
                    ? "bg-[#00bcd4] text-white shadow-lg shadow-[#00bcd4]/20"
                    : "bg-zinc-800 text-zinc-400 hover:bg-zinc-700 hover:text-white"
                }`}
              >
                {tool.slice(0, 6)}
              </button>
            ))}
          </div>
        </div>
      ))}

      <div className="mt-auto pt-6 border-t border-zinc-800">
        <label className="text-[10px] font-bold text-zinc-500 uppercase block mb-2">Brush Radius</label>
        <input
          type="range"
          min="1"
          max="20"
          value={brushRadius}
          onChange={(e) => setBrushRadius(parseInt(e.target.value))}
          className="w-full accent-[#00bcd4] bg-zinc-800 h-1.5 rounded-lg appearance-none cursor-pointer"
        />
        <div className="flex justify-between text-[10px] text-zinc-600 font-bold mt-1">
          <span>1</span>
          <span>{brushRadius}</span>
          <span>20</span>
        </div>
      </div>

      <div className="p-3 bg-black rounded border border-zinc-800 text-center">
        <span className="text-[10px] text-zinc-500 block mb-1 uppercase font-bold tracking-tight">Active Tool</span>
        <span className="text-xs font-mono font-bold text-[#ffeb3b]">{activeTool.toUpperCase()}</span>
      </div>
    </div>
  );
};
