import React from "react";
import { clsx } from "clsx";
import { Settings, Globe, Map as MapIcon, Home as City, Flag as Castle, Zap, RefreshCw } from "lucide-react";

interface SculptorTuningDeckProps {
    weights: Record<string, number>;
    onWeightChange: (key: string, val: number) => void;
    intents: Record<string, number>;
    onIntentChange: (key: string, val: number) => void;
    telemetry: string;
}

export const SculptorTuningDeck: React.FC<SculptorTuningDeckProps> = ({
    weights,
    onWeightChange,
    intents,
    onIntentChange,
    telemetry,
}) => {
    const [activeTab, setActiveTab] = React.useState<"civil" | "biomes" | "climate">("civil");
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
        sea_level: "Base land-to-water ratio. Lower = more land.",
        aridity: "Global dryness factor.",
        peak_intensity: "Sharpness of ridges.",
        mtn_clusters: "Grouping of mountain ranges.",
        mtn_scale: "Horizontal span of tectonic plates.",
        moisture_level: "Baseline rainfall.",
        land_density: "Continental mass aggregation.",
        biome_isolation: "Clumping factor for nature.",
        designer_authority: "Sovereign multiplier for intent layers.",
        erosion_scale: "Rain-shaving on peaks.",
        fertility_rate: "Growth density of life.",
        blossom_speed: "Procedural expansion rate.",
        melting_point: "Snowline altitude.",
        seed: "Deterministic hash for uniqueness.",
    };

    return (
        <div className="flex flex-col gap-6 p-8 h-full bg-zinc-950 border-l border-white/5 shadow-2xl overflow-y-auto w-80 scrollbar-hide">
            {/* Tab Navigation */}
            <div className="flex items-center gap-2 bg-black/40 p-1 rounded-xl border border-white/5">
                {[
                    { id: "civil", icon: <Castle size={14} />, label: "Civil" },
                    { id: "biomes", icon: <Globe size={14} />, label: "Bio" },
                    { id: "climate", icon: <Settings size={14} />, label: "Noise" }
                ].map(t => (
                    <button
                        key={t.id}
                        onClick={() => setActiveTab(t.id as any)}
                        className={clsx(
                            "flex-1 flex items-center justify-center gap-2 py-2 rounded-lg text-[9px] font-black uppercase transition-all",
                            activeTab === t.id ? "bg-[#00bcd4] text-black shadow-lg" : "text-zinc-600 hover:text-white"
                        )}
                    >
                        {t.icon}
                        {t.label}
                    </button>
                ))}
            </div>

            <h2 className="text-[10px] font-black tracking-[0.3em] text-[#00bcd4] uppercase italic">--- {activeTab.toUpperCase()} ---</h2>

            <div className="space-y-5">
                {activeTab === "civil" && (
                    <>
                        {[
                            { id: "cities", label: "Cities", type: "number", min: 0, max: 20 },
                            { id: "shrines", label: "Shrines", type: "number", min: 0, max: 50 },
                            { id: "ruins", label: "Ancient Ruins", type: "number", min: 0, max: 100 },
                            { id: "road_density", label: "Road Network", type: "range", min: 1, max: 10 }
                        ].map(item => (
                            <div key={item.id} className="flex flex-col gap-2">
                                <div className="flex justify-between text-[9px] font-black text-zinc-500 uppercase tracking-widest">
                                    <label>{item.label}</label>
                                    <span className="text-[#00bcd4]">{intents[item.id]}</span>
                                </div>
                                <input
                                    type={item.type}
                                    min={item.min}
                                    max={item.max}
                                    value={intents[item.id]}
                                    onChange={(e) => onIntentChange(item.id, parseFloat(e.target.value))}
                                    className={clsx(
                                        "w-full rounded-lg outline-none",
                                        item.type === "range" ? "h-1 bg-zinc-900 border-none appearance-none accent-[#00bcd4]" : "bg-black text-[#00bcd4] border border-white/5 px-2 py-1 text-[10px]"
                                    )}
                                />
                            </div>
                        ))}
                    </>
                )}

                {activeTab === "biomes" && (
                    <>
                        {[
                            { id: "mountain_density", label: "Mountain Peaks", min: 1, max: 10 },
                            { id: "forest_density", label: "Forest Coverage", min: 1, max: 10 },
                            { id: "swamp_density", label: "Wetland / Swamp", min: 1, max: 10 },
                            { id: "water_density", label: "Water Level", min: 1, max: 10 }
                        ].map(item => (
                            <div key={item.id} className="flex flex-col gap-2">
                                <div className="flex justify-between text-[9px] font-black text-zinc-500 uppercase tracking-widest">
                                    <label>{item.label}</label>
                                    <span className="text-[#00bcd4]">{intents[item.id]} / 10</span>
                                </div>
                                <input
                                    type="range"
                                    min={item.min}
                                    max={item.max}
                                    value={intents[item.id]}
                                    onChange={(e) => onIntentChange(item.id, parseInt(e.target.value))}
                                    className="w-full h-1 bg-zinc-900 rounded-lg appearance-none cursor-pointer accent-[#00bcd4]"
                                />
                            </div>
                        ))}
                    </>
                )}

                {activeTab === "climate" && (
                    Object.entries(weightLabels).map(([key, label]) => (
                        <div key={key} className="flex flex-col gap-2 group" title={weightTooltips[key]}>
                            <div className="flex justify-between items-center text-[9px] font-black text-zinc-600 uppercase tracking-widest leading-none">
                                <label className="group-hover:text-zinc-300 transition-colors">{label}</label>
                                <div className="flex items-center gap-2">
                                    {key === "seed" && (
                                        <button
                                            onClick={() => onWeightChange(key, Math.floor(Math.random() * 1000000))}
                                            className="px-2 py-1 rounded bg-white/5 hover:bg-white/10 text-zinc-500 hover:text-white transition-all text-[8px] tracking-widest"
                                        >
                                            RAND
                                        </button>
                                    )}
                                    <input
                                        type="number"
                                        min="0"
                                        max={key === "seed" ? "9999999" : "1.0"}
                                        step={key === "seed" ? "1" : "0.1"}
                                        value={weights[key] !== undefined ? weights[key] : (key === "seed" ? 42 : 0.5)}
                                        onChange={(e) => onWeightChange(key, key === "seed" ? parseInt(e.target.value) : parseFloat(e.target.value))}
                                        className="bg-black text-[#00bcd4] border border-white/5 px-2 py-1 text-[10px] font-mono font-bold w-16 text-right focus:outline-none focus:border-cyan-500/50 rounded-lg"
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
                                    className="w-full h-1 bg-zinc-900 rounded-lg appearance-none cursor-pointer accent-[#00bcd4]"
                                />
                            )}
                        </div>
                    ))
                )}
            </div>

            <div className="mt-auto pt-8 border-t border-white/5 space-y-4">
                <h3 className="text-[10px] font-black text-zinc-600 uppercase tracking-widest italic">--- Telemetry ---</h3>
                <div className="p-4 bg-black rounded-2xl border border-white/5 font-mono text-[9px] text-[#00bcd4] whitespace-pre shadow-inner leading-relaxed">
                    {telemetry}
                </div>
            </div>
        </div>
    );
};
