"use client";

import React from "react";
import { clsx } from "clsx";

interface SculptorPaletteProps {
    activeTool: string;
    setActiveTool: (tool: string) => void;
    brushRadius: number;
    setBrushRadius: (r: number) => void;
    categories: Record<string, string[]>;
}

export const SculptorPalette: React.FC<SculptorPaletteProps> = ({
    activeTool,
    setActiveTool,
    brushRadius,
    setBrushRadius,
    categories,
}) => {
    return (
        <div className="flex flex-col gap-6 p-6 h-full bg-zinc-950 border-r border-white/5 shadow-2xl overflow-y-auto w-64 scrollbar-hide">
            <h2 className="text-[10px] font-black tracking-[0.3em] text-[#00bcd4] uppercase italic">--- Palette ---</h2>

            <div className="space-y-6">
                {Object.entries(categories).map(([category, tools]) => (
                    <div key={category} className="space-y-3">
                        <h3 className="text-[9px] font-black text-zinc-600 uppercase tracking-widest leading-none">{category}</h3>
                        <div className="grid grid-cols-2 gap-1.5">
                            {tools.map((tool) => (
                                <button
                                    key={tool}
                                    onClick={() => setActiveTool(tool)}
                                    className={clsx(
                                        "px-2 py-2 text-[9px] font-black uppercase transition-all rounded-lg border",
                                        activeTool === tool
                                            ? "bg-[#00bcd4] text-white border-[#00bcd4] shadow-[0_0_15px_rgba(0,188,212,0.3)]"
                                            : "bg-white/5 border-transparent text-zinc-500 hover:bg-white/10 hover:text-white"
                                    )}
                                >
                                    {tool.slice(0, 8)}
                                </button>
                            ))}
                        </div>
                    </div>
                ))}
            </div>

            <div className="mt-auto pt-8 border-t border-white/5 space-y-3">
                <div className="flex justify-between items-center">
                    <label className="text-[9px] font-black text-zinc-600 uppercase tracking-widest">Brush Radius</label>
                    <span className="text-[10px] font-mono font-bold text-[#00bcd4]">{brushRadius}px</span>
                </div>
                <input
                    type="range"
                    min="1"
                    max={20}
                    value={brushRadius}
                    onChange={(e) => setBrushRadius(parseInt(e.target.value))}
                    className="w-full accent-[#00bcd4] bg-zinc-800 h-1 rounded-lg appearance-none cursor-pointer"
                />
            </div>

            <div className="p-4 bg-black rounded-2xl border border-white/5 text-center mt-4">
                <span className="text-[8px] text-zinc-600 block mb-1 uppercase font-black tracking-widest italic">Active Intent</span>
                <span className="text-xs font-mono font-bold text-[#ffeb3b]">{activeTool.toUpperCase()}</span>
            </div>
        </div>
    );
};
