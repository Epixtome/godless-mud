"use client";

import React from "react";

interface TuningDeckProps {
  weights: Record<string, number>;
  onWeightChange: (key: string, val: number) => void;
  telemetry: string;
}

export const TuningDeck: React.FC<TuningDeckProps> = ({
  weights,
  onWeightChange,
  telemetry,
}) => {
  const weightLabels: Record<string, string> = {
    sea_level: "Sea Level",
    aridity: "Aridity",
    peak_intensity: "Peak Inten",
    mtn_clusters: "Mtn Clust",
    mtn_scale: "Mtn Scale",
    moisture_level: "Rainfall",
    land_density: "Land Mass",
    biome_isolation: "Bio Isolat",
    designer_authority: "Designer Auth",
    erosion_scale: "Erosion",
    fertility_rate: "Fertility",
    blossom_speed: "Blossom",
    melting_point: "Melting",
    seed: "World Seed",
  };

  const weightTooltips: Record<string, string> = {
    sea_level: "Determines the base land-to-water ratio. Lower for more land.",
    aridity: "Global dryness. Higher values convert forests to deserts.",
    peak_intensity: "Sharpness of ridges. Higher = taller mountains.",
    mtn_clusters: "Grouping of mountain ranges.",
    mtn_scale: "Horizontal span of tectonic plates.",
    moisture_level: "Baseline rainfall for biomes.",
    land_density: "Proximity of continental mass blocks.",
    biome_isolation: "Clumping factor for nature regions.",
    designer_authority: "Global multiplier for your paint stencils.",
    erosion_scale: "Rain-shaving intensity on peaks.",
    fertility_rate: "Forest growth density.",
    blossom_speed: "Procedural expansion rate of biomes.",
    melting_point: "Snowline altitude.",
    seed: "Primary hash for world uniqueness.",
  };

  return (
    <div className="flex flex-col gap-6 p-4 h-full bg-zinc-900 border-l border-zinc-800 shadow-xl overflow-y-auto w-72 scrollbar-thin scrollbar-thumb-zinc-800 scrollbar-track-zinc-900">
      <h2 className="text-sm font-bold tracking-widest text-[#00bcd4] uppercase">--- Tuning Deck ---</h2>
      
      <div className="space-y-4">
        {Object.entries(weightLabels).map(([key, label]) => (
          <div key={key} className="flex flex-col gap-1.5 group" title={weightTooltips[key]}>
            <div className="flex justify-between items-center">
              <label className="text-[10px] font-bold text-zinc-500 group-hover:text-zinc-300 transition-colors uppercase tracking-widest">{label}</label>
              <div className="flex items-center gap-2">
                {key === "seed" && (
                  <button 
                    onClick={() => onWeightChange(key, Math.floor(Math.random() * 1000000))}
                    className="p-1 px-1.5 bg-zinc-800 hover:bg-[#00bcd4] hover:text-white text-zinc-400 rounded transition-all text-[8px] font-black uppercase tracking-tighter"
                  >
                    Rand
                  </button>
                )}
                <input
                  type={key === "seed" ? "number" : "number"}
                  min={key === "seed" ? "0" : "0.0"}
                  max={key === "seed" ? "9999999" : "1.0"}
                  step={key === "seed" ? "1" : "0.1"}
                  value={weights[key] !== undefined ? weights[key] : (key === "seed" ? 42 : 0.5)}
                  onChange={(e) => onWeightChange(key, key === "seed" ? parseInt(e.target.value) : parseFloat(e.target.value))}
                  className="bg-black text-[#00bcd4] border border-zinc-800 px-2 py-1 text-xs font-mono font-bold w-20 text-right focus:outline-none focus:border-[#00bcd4]/50 focus:ring-1 focus:ring-[#00bcd4]/20 rounded transition-all"
                />
              </div>
            </div>
            {key !== "seed" && (
              <input 
                type="range"
                min="0"
                max="1"
                step="0.01"
                value={weights[key] || 0.5}
                onChange={(e) => onWeightChange(key, parseFloat(e.target.value))}
                className="w-full h-1 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-[#00bcd4]"
              />
            )}
          </div>
        ))}
      </div>

      <div className="mt-auto pt-6 border-t border-zinc-800 space-y-3">
        <h3 className="text-xs font-bold text-zinc-500 uppercase tracking-widest">--- Telemetry ---</h3>
        <div className="p-4 bg-black rounded border border-zinc-800 font-mono text-[10px] text-zinc-400 whitespace-pre shadow-inner">
          {telemetry}
        </div>
      </div>
    </div>
  );
};
