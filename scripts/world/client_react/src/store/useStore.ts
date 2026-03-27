import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { sendEvent } from '../lib/socket';

export interface GameStatus {
  hp: { current: number; max: number };
  stamina: { current: number; max: number };
  balance: { current: number; max: number };
  resource?: { name: string, current: number, max: number, id: string };
  blessings: any[];
  target: { name: string, hp: { current: number, max: number }, id: string } | null;
  status_effects: any[];
  inventory: any[];
  equipment: Record<string, string | null>;
  room: { name: string, zone: string, description: string, entities: any[], traps: any[] };
  time: string;
  is_day: boolean;
  weather: string;
}

export interface MapData {
  radius: number;
  center: { x: number, y: number, z: number };
  grid: any[][];
}

interface GameLog {
  text: string;
  timestamp: string;
}

export interface UIWindow {
    id: string;
    zIndex: number;
    isVisible: boolean;
    scale: number;
    width: number;
    height: number;
    x: number;
    y: number;
    isPinned?: boolean;
}

interface AppState {
  status: GameStatus | null;
  tacticalMapData: MapData | null;
  logs: GameLog[];
  selectedTargetId: string | null;
  isConnected: boolean;
  windows: Record<string, UIWindow>;
  showInfluence: boolean;
  
  setStatus: (status: GameStatus) => void;
  setTacticalMapData: (data: MapData) => void;
  addLog: (msg: string) => void;
  setSelectedTargetId: (id: string | null) => void;
  setConnected: (status: boolean) => void;
  setShowInfluence: (showInfluence: boolean) => void;
  updateWindow: (id: string, updates: Partial<UIWindow>) => void;
  focusWindow: (id: string) => void;
  toggleWindow: (id: string) => void;
  resetLayout: () => void;
  saveLayoutToServer: () => void;
}

const DEFAULT_WINDOWS: Record<string, UIWindow> = {
    'comms': { id: 'comms', zIndex: 10, isVisible: true, scale: 1, width: 720, height: 480, x: 500, y: 150 },
    'inventory': { id: 'inventory', zIndex: 10, isVisible: true, scale: 1, width: 320, height: 240, x: 40, y: 50 },
    'tactical': { id: 'tactical', zIndex: 15, isVisible: true, scale: 0.5, width: 600, height: 600, x: 40, y: 300 },
    'vitals': { id: 'vitals', zIndex: 20, isVisible: true, scale: 1, width: 400, height: 180, x: 1260, y: 50 },
    'combat': { id: 'combat', zIndex: 20, isVisible: true, scale: 1, width: 400, height: 320, x: 1260, y: 240 },
    'encounter': { id: 'encounter', zIndex: 25, isVisible: true, scale: 1, width: 440, height: 200, x: 740, y: 650 },
    'room': { id: 'room', zIndex: 10, isVisible: true, scale: 1, width: 320, height: 280, x: 1260, y: 570 },
    'weather': { id: 'weather', zIndex: 10, isVisible: true, scale: 1, width: 320, height: 160, x: 740, y: 50 },
    'score': { id: 'score', zIndex: 10, isVisible: false, scale: 1, width: 400, height: 400, x: 400, y: 100 },
    'attributes': { id: 'attributes', zIndex: 10, isVisible: false, scale: 1, width: 400, height: 400, x: 810, y: 100 }
};

export const useStore = create<AppState>()(
  persist(
    (set, get) => ({
      status: null,
      tacticalMapData: null,
      logs: [],
      selectedTargetId: null,
      isConnected: false,
      windows: DEFAULT_WINDOWS,
      showInfluence: false,

      // --- HYDRATION ENGINE (V9.2) ---
      setStatus: (status) => {
          set({ status });
          
          // Server-Side Layout Sync: If the server has a layout, and we haven't modified ours this session
          // (Actually, server-side truth always wins for multi-device parity)
          // @ts-ignore
          const serverPrefs = status.ui_prefs;
          if (serverPrefs && Object.keys(serverPrefs).length > 0) {
              const currentWindows = get().windows;
              // Simple check to see if we need to hydrate (Avoid infinite loops)
              if (JSON.stringify(serverPrefs) !== JSON.stringify(currentWindows)) {
                  console.log("Hydrating layout from server...");
                  set({ windows: serverPrefs });
              }
          }
      },

      setTacticalMapData: (tacticalMapData) => set({ tacticalMapData }),
      setShowInfluence: (showInfluence) => set({ showInfluence }),
      addLog: (text) => set((state) => ({ 
        logs: [...state.logs.slice(-200), { text, timestamp: new Date().toLocaleTimeString() }] 
      })),
      setSelectedTargetId: (selectedTargetId) => set({ selectedTargetId }),
      setConnected: (isConnected) => set({ isConnected }),
      
      updateWindow: (id, updates) => set((state) => ({
          windows: { ...state.windows, [id]: { ...state.windows[id], ...updates } }
      })),
      
      toggleWindow: (id) => set((state) => ({
          windows: { ...state.windows, [id]: { ...state.windows[id], isVisible: !state.windows[id].isVisible } }
      })),
      
      focusWindow: (id) => set((state) => {
          const maxZ = Math.max(...Object.values(state.windows).map(w => w.zIndex));
          return { 
              windows: { ...state.windows, [id]: { ...state.windows[id], zIndex: maxZ + 1, isVisible: true } }
          };
      }),

      resetLayout: () => set({ windows: DEFAULT_WINDOWS }),

      saveLayoutToServer: () => {
          sendEvent('ui:save_layout', get().windows);
      }
    }),
    {
      name: 'godless_ui_prefs_v2',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({ windows: state.windows }), // Only persist windows
    }
  )
);
