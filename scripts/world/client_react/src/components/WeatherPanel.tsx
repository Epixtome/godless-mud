import React from 'react';
import { useStore } from '../store/useStore';
import { sendCommand } from '../lib/ges';
import { Cloud, Sun, Moon, Sunrise, Sunset, Wind, Droplets, CloudRain, CloudLightning, Snowflake } from 'lucide-react';
import { clsx } from 'clsx';

const WEATHER_ICONS: Record<string, any> = {
    "clear": Sun,
    "cloudy": Cloud,
    "windy": Wind,
    "rainy": CloudRain,
    "stormy": CloudLightning,
    "snowing": Snowflake,
    "foggy": Droplets
};

export function WeatherPanel() {
  const { status } = useStore();
  
  const weather = status?.weather || "clear";
  const time = status?.time || "Morning";
  const isDay = status?.is_day ?? true;
  
  const WeatherIcon = WEATHER_ICONS[weather.toLowerCase()] || Sun;

  return (
    <div className="glass-panel rounded-lg overflow-hidden flex flex-col h-full">
        <div className="bg-slate-900/50 px-3 py-2 border-b border-white/5 flex items-center justify-between">
           <div className="flex items-center gap-2">
              <Sun size={14} className="text-yellow-400" />
              <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest leading-none">Aetheric Conditions</span>
           </div>
        </div>
        
        <div className="flex-1 p-4 flex items-center justify-around gap-4 bg-gradient-to-br from-slate-900/40 to-black/20">
            {/* Time Indicator Button */}
            <button 
                onClick={() => sendCommand("@time")}
                className="flex flex-col items-center gap-2 group outline-none"
            >
                <div className={clsx(
                    "w-12 h-12 rounded-full flex items-center justify-center border-2 transition-all shadow-lg active:scale-95",
                    isDay 
                        ? "bg-amber-500/10 border-amber-500/30 text-amber-400 group-hover:bg-amber-500/20 group-hover:border-amber-400 group-hover:shadow-amber-500/20" 
                        : "bg-indigo-500/10 border-indigo-500/30 text-indigo-400 group-hover:bg-indigo-500/20 group-hover:border-indigo-400 group-hover:shadow-indigo-500/20"
                )}>
                    {time === "Morning" && <Sunrise size={24} />}
                    {time === "Day" && <Sun size={24} />}
                    {time === "Evening" && <Sunset size={24} />}
                    {time === "Night" && <Moon size={24} />}
                </div>
                <span className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500 group-hover:text-slate-300 transition-colors">
                    {time}
                </span>
            </button>

            <div className="w-[1px] h-12 bg-white/5" />

            {/* Weather Indicator Button */}
            <button 
                onClick={() => sendCommand("@weather")}
                className="flex flex-col items-center gap-2 group outline-none"
            >
                <div className="w-12 h-12 rounded-full bg-blue-500/10 border-2 border-blue-500/30 text-blue-400 flex items-center justify-center shadow-lg active:scale-95 group-hover:bg-blue-500/20 group-hover:border-blue-400 group-hover:shadow-blue-500/20">
                    <WeatherIcon size={24} />
                </div>
                <span className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500 group-hover:text-slate-300 transition-colors">
                    {weather.replace('_', ' ')}
                </span>
            </button>
        </div>
    </div>
  );
}

export default WeatherPanel;
