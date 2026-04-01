import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import axios from 'axios';
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
  is_admin?: boolean;
  ui_prefs?: Record<string, any>;
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
  combatNotifications: any[];
  isLoggedByServer: boolean;
  isAdmin: boolean;
  adminCatalog: {
    mobs: string[];
    items: string[];
    classes: string[];
  };
  savedCharacters: { name: string, lastUsed: number }[];
  lastWindowChange: number;
  activeWorkspace: 'game' | 'studio' | 'editor' | 'nexus';
  terrainRegistry: any;
  addCombatNotification: (notif: any) => void;

  setLoggedByServer: (status: boolean) => void;
  setAdmin: (admin: boolean) => void;
  setAdminCatalog: (catalog: any) => void;
  saveCharacter: (name: string) => void;
  removeCharacter: (name: string) => void;
  fetchTerrainRegistry: () => Promise<void>;

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
  setWorkspace: (workspace: 'game' | 'studio' | 'editor' | 'nexus') => void;
  toggleWorkspace: () => void;
}

const DEFAULT_WINDOWS: Record<string, UIWindow> = {
  'comms': { id: 'comms', zIndex: 10, isVisible: true, scale: 1, width: 720, height: 480, x: 500, y: 150 },
  'inventory': { id: 'inventory', zIndex: 10, isVisible: false, scale: 1, width: 320, height: 240, x: 40, y: 50 },
  'tactical': { id: 'tactical', zIndex: 15, isVisible: true, scale: 0.5, width: 600, height: 600, x: 40, y: 300 },
  'mini': { id: 'mini', zIndex: 12, isVisible: false, scale: 0.35, width: 440, height: 440, x: 40, y: 50 },
  'vitals': { id: 'vitals', zIndex: 20, isVisible: true, scale: 1, width: 400, height: 180, x: 1260, y: 50 },
  'combat': { id: 'combat', zIndex: 20, isVisible: true, scale: 1, width: 400, height: 320, x: 1260, y: 240 },
  'encounter': { id: 'encounter', zIndex: 25, isVisible: false, scale: 1, width: 440, height: 200, x: 740, y: 650 },
  'room': { id: 'room', zIndex: 10, isVisible: false, scale: 1, width: 320, height: 280, x: 1260, y: 570 },
  'weather': { id: 'weather', zIndex: 10, isVisible: false, scale: 1, width: 320, height: 160, x: 740, y: 50 },
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
      combatNotifications: [],
      isLoggedByServer: false,
      isAdmin: true,
      adminCatalog: { mobs: [], items: [], classes: [] },
      savedCharacters: [],
      activeWorkspace: 'nexus',
      terrainRegistry: null,

      lastWindowChange: 0,
      addCombatNotification: (notif) => set((state) => {
        const id = Math.random().toString(36).substring(7);
        const offsetX = Math.random() * 40 - 20;
        const offsetY = Math.random() * 20 - 10;
        const newNotif = { ...notif, id, offsetX, offsetY };
        // Auto-remove after 2s
        setTimeout(() => {
          const currentStore = useStore.getState();
          set({
            combatNotifications: currentStore.combatNotifications.filter(n => n.id !== id)
          });
        }, 2000);
        return { combatNotifications: [...state.combatNotifications, newNotif] };
      }),

      // --- HYDRATION ENGINE (V9.2) ---
      setLoggedByServer: (isLoggedByServer) => set({ isLoggedByServer }),
      setAdmin: (isAdmin) => set({ isAdmin }),
      setAdminCatalog: (adminCatalog) => set({ adminCatalog }),

      saveCharacter: (name) => set((state) => {
        const others = state.savedCharacters.filter(c => c.name.toLowerCase() !== name.toLowerCase());
        return { savedCharacters: [{ name, lastUsed: Date.now() }, ...others].slice(0, 5) };
      }),

      removeCharacter: (name) => set((state) => ({
        savedCharacters: state.savedCharacters.filter(c => c.name !== name)
      })),

      fetchTerrainRegistry: async () => {
        try {
          const resp = await axios.get('/api/world/terrain-registry');
          set({ terrainRegistry: resp.data });
        } catch (e) {
          console.error("Registry fetch failed", e);
        }
      },

      setStatus: (status) => {
        // [V12.1] Sync Authority from server pulse
        console.log(`[AUTH] Pulse: is_admin=${status.is_admin}, user=${status.room?.name}`);
        if (status.is_admin !== undefined && status.is_admin !== get().isAdmin) {
          console.group(`[AUTH] Transition: ${status.is_admin ? "ASCENSION" : "FALL"}`);
          console.log(`Setting isAdmin to ${status.is_admin}`);
          console.groupEnd();
          set({ isAdmin: status.is_admin });
        }
        
        set({ status });

        // Server-Side Layout Sync: [V9.5 BRIDGING GUARD]
        const serverPrefs = status.ui_prefs;
        if (serverPrefs && Object.keys(serverPrefs).length >= 5) {
          const { windows, lastWindowChange } = get();
          if (Date.now() - lastWindowChange > 3000) {
            // Only sync if significant mismatch (prevents jitter)
            const serverCount = Object.keys(serverPrefs).length;
            const localCount = Object.keys(windows).length;

            if (serverCount !== localCount || JSON.stringify(serverPrefs) !== JSON.stringify(windows)) {
              console.log("[SYNC] Hydrating robust layout from server...");
              set({ windows: serverPrefs });
            }
          }
        }
      },

      setTacticalMapData: (tacticalMapData) => set({ tacticalMapData }),
      setShowInfluence: (showInfluence) => set({ showInfluence }),
      addLog: (text) => set((state) => ({
        logs: [...state.logs.slice(-200), { text, timestamp: new Date().toLocaleTimeString() }]
      })),
      setSelectedTargetId: (selectedTargetId) => set({ selectedTargetId }),
      setConnected: (isConnected) => {
        set({ isConnected });
        if (!isConnected) set({ isLoggedByServer: false });
      },

      updateWindow: (id, updates) => set((state) => ({
        windows: { ...state.windows, [id]: { ...state.windows[id], ...updates } },
        lastWindowChange: Date.now()
      })),

      toggleWindow: (id) => set((state) => ({
        windows: { ...state.windows, [id]: { ...state.windows[id], isVisible: !state.windows[id].isVisible } },
        lastWindowChange: Date.now()
      })),

      focusWindow: (id) => set((state) => {
        const maxZ = Math.max(...Object.values(state.windows).map(w => w.zIndex));
        return {
          windows: { ...state.windows, [id]: { ...state.windows[id], zIndex: maxZ + 1, isVisible: true } },
          lastWindowChange: Date.now()
        };
      }),

      resetLayout: () => set({ windows: DEFAULT_WINDOWS, lastWindowChange: Date.now() }),

      saveLayoutToServer: () => {
        sendEvent('ui:save_layout', get().windows);
      },

      setWorkspace: (activeWorkspace) => set({ activeWorkspace }),
      toggleWorkspace: () => set((state) => ({
        activeWorkspace: state.activeWorkspace === 'game' ? 'studio' : 'game'
      })),

    }),
    {
      name: 'godless_ui_prefs_v2',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        windows: state.windows,
        savedCharacters: state.savedCharacters,
        activeWorkspace: state.activeWorkspace
      }), // Persist UI, Characters, and last active Workspace
    }
  )
);
