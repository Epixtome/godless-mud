# SOVEREIGN_RECONSTITUTION.md
**Date:** 2026-03-31  
**Project:** Godless V12.0  
**Status:** STABILIZED (Monitoring)

> [!IMPORTANT]
> The "Sovereign Spine" has been reconstituted. The following tasks are complete and verified on Port 3001.

## [ PROTOCOL: THE GOLDEN LOOP ]
1. **SCULPT:** Edit source in `scripts/world/client_react/src/`.
2. **TEST:** Verify live on `localhost:3001`.
3. **COMMIT:** `git add .` and `git commit -m "[STAMP] Task Name"`.
4. **BAKE:** `npm run build` to synchronize `localhost:8000`.

---

## 1. THE RECONSTITUTION BACKLOG

### STAGE 1: INTERFACE HARDENING (UX & COMMANDS) - [COMPLETED]
- [x] **Task 1.1: Quick-Focus (Tab):** Pressing Tab now focus-locks the Command Bar.
- [x] **Task 1.2: Command History (Up/Down):** Ring buffer implemented.
- [x] **Task 1.3: Command Retention:** Enter highlights for rapid repeat.
- [x] **Task 1.4: Password Persistence:** Restore `localStorage` logic in `LoginOverlay`.

### STAGE 2: TACTICAL REFINEMENT (MAP & HUD) - [COMPLETED]
- [x] **Task 2.1: Weather HUD Relocation:** Moved to top-right to clear controls.
- [x] **Task 2.2: Tactical Map Zoom:** Mouse-wheel scroll zoom integrated.
- [x] **Task 2.3: Button Collision Audit:** RELOCATED to bottom-center for occlusion rescue.

### STAGE 3: SAVES & PERFORMANCE (THE BLOAT REDUCTION) - [COMPLETED]
- [x] **Task 3.1: State Sharding:** `kip.json` sharded. World discovery moved to `.map.json`.
- [x] **Task 3.2: Domain Masking:** Pulse payloads reduced via Delta Compression.
- [x] **Task 3.3: Emergency Auth Fix:** Hardened 'is_admin' to `kip.json`.

---

## 2. SOVEREIGN RESILIENCE PROTOCOLS
To prevent "Ghost Processes," "Stale Authorization," or "Pulse Overwrites" in future development.

### A. The "Cold-Save" Hardening
- **THE CONFLICT:** Manual JSON edits (e.g., God-Status) will be **silently overwritten** by the engine's Pulse Save if the engine is running.
- **THE LAW:** Always use `taskkill /F /IM python.exe` (Windows) BEFORE manually editing a character save. The engine must be **OFFLINE** to accept manual attribute hardening.

### B. Ghost Process Termination
- **THE CONFLICT:** Starting a new engine instance does not kill stale background processes. These "Ghosts" will fight for port access and continue to write old data.
- **THE LAW:** If commands feel unrecognized or logic feels stale, perform a **Nuke Reset**: `taskkill /F /IM python.exe /T` (Windows).

### C. State Sharding Logic
- **STRUCTURE:** Character discovery memory is stored in `[name].map.json`. Stats are stored in `[name].json`. The engine merges these dynamically upon login.

---

## 3. INTEGRITY AUDIT LOG (REVIEW ITEMS)
- **Attribute Mismatch:** Character saves contain ~10 equipment slots not defined in `Player.__init__`. 
    - *Resolution:* Currently handled by dynamic assignment via `getattr` in `persistence.py`.
- **2026-03-31:** Core stabilized. Admin restored. Sharding active.

---
**[V12.2] DOCUMENTATION SEALED - MONOLITH RECONSTITUTED**
