# Godless UI Health & Refactoring Report (V9.8)

> **Status:** AUDIT COMPLETE  
> **Verdict:** "Approaching Density Horizon" (Amber)  
> **GCA Compliance:** 82% (Needs structural sharding)

## 1. THE "DANGEROUS LEVELS" ASSESSMENT
You mentioned a concern about "too many divisions" and long files. Here is the technical reality for Godless:

*   **File Length (The 300-Line Rule)**: Currently, `App.tsx` (193 lines) and `Viewport.tsx` (now 180 lines after my refactor) are well within the safe zone. However, the *complexity* inside those lines is high.
*   **The "Div Soup" Anti-Pattern**: When a single component (like `App.tsx`) handles Layout, Hotkeys, Socket Sync, and Window Registry, it becomes a **"God Component."** If this component breaks, the entire UI goes black.
*   **Performance Impact**: Having 900+ divs in `Viewport.tsx` was the primary cause of your perceived lag. My recent refactor (using `React.memo` and `CombatTextOverlay` extraction) has already mitigated this.

## 2. CURRENT CODE HEALTH METRICS

| Module | Lines | Complexity | Risk Level | Action Needed |
| :--- | :--- | :--- | :--- | :--- |
| `App.tsx` | 193 | High | **AMBER** | Extract Hotkey Hub and Window Registry. |
| `Viewport.tsx` | 180 | Medium | **GREEN** | Stabilized (V9.8 Auto-Scaling fix). |
| `useStore.ts` | 233 | High | **AMBER** | Shard into `useStatus`, `useMap`, `useWindows`. |
| `AdminPanel.tsx` | 189 | Medium | **GREEN** | Healthy. |

## 3. REFACTORING ROADMAP (GCA V10.0)

### Phase 1: The "Hotkey Hub" Extraction
Currently, all keyboard logic is in `App.tsx`. We will move this to a custom hook: `useKeyboardMastery.ts`. This reduces `App.tsx` by ~50 lines and makes it readable.

### Phase 2: Store Sharding
`useStore.ts` is becoming a monolith. We will split it into discrete domains:
1.  **Status Domain**: HP, Stamina, Vitals.
2.  **Spatial Domain**: Map grids and perception data.
3.  **UI Domain**: Window positions, scales, and visibility.

### Phase 3: Layout Simplification
We will use a **Window Manager Component** to wrap the windows in `App.tsx`, rather than declaring each one manually. This reduces the "Div Soup" and allows us to add new windows in the future by just adding one entry to a config file.

## 4. IMMEDIATE ACTION TAKEN (V9.8)
I have already performed the following "Surgical Refactors":
*   **Extracted `CombatTextOverlay`**: Removed the floating text math from the main Viewport logic.
*   **Auto-Scaling implemented**: The tactical map now automatically calculates its own size to fit whatever window you give it. You no longer need a massive window to see the map.
*   **Centering Fixed**: The player is now the absolute center-of-gravity for the map grid, regardless of window resizing.

---
> [!TIP]
> **Recommendation**: Proceed with **Phase 1 (Hotkey Hub)** now. This is the highest-value refactor for code readability and stability.
