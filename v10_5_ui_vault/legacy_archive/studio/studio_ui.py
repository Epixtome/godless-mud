import tkinter as tk
from tkinter import messagebox, scrolledtext
import math
import os, time
import studio_config
import architect_data as data

class StudioUI:
    def __init__(self, state):
        self.state = state
        self.root = None
        self.canvas = None
        self.zoom_factor = 1.0
        self.cell_size = studio_config.CELL_SIZE
        self.tile_ids = {}
        self.tile_colors = {} # [V17.8] Color Cache to prevent redraw lag
        self.stencil_ids = {}
        
        # UI State
        self.view_mode = "terrain" 
        self.view_phase = "Final"
        self.brush_mode = "none"
        self.brush_radius = 4
        
        # Toggles & Indicators
        self.lbl_status = None
        self.lbl_probe = None
        self.lbl_telemetry = None
        self.lbl_active_tool = None
        self.seed_entry = None
        
        # Overlay Bools (Menu-bound)
        self.show_stencil = None
        self.show_cr_overlay = None
        self.show_mob_overlay = None

    def boot(self):
        self.root = tk.Tk()
        self.root.title(f"{studio_config.STUDIO_TITLE} - V17.0 PRO")
        self.root.geometry("1400x900")
        self.root.configure(bg="#111")
        
        self.show_stencil = tk.BooleanVar(value=True)
        self.show_cr_overlay = tk.BooleanVar(value=False)
        self.show_mob_overlay = tk.BooleanVar(value=False)
        
        self._build_menus()
        self._build_toolbar()
        
        # [V17.0] 3-COLUMN PRO LAYOUT
        self.main_container = tk.Frame(self.root, bg="#111")
        self.main_container.pack(fill="both", expand=True)
        
        # 1. LEFT SIDEBAR (Palette)
        self.sidebar_left = tk.Frame(self.main_container, bg="#181818", width=140, padx=10, pady=10)
        self.sidebar_left.pack(side="left", fill="y", padx=2)
        self._build_brush_sidebar(self.sidebar_left)
        
        # 2. CENTER PILLAR (Vision)
        self.center_frame = tk.Frame(self.main_container, bg="black")
        self.center_frame.pack(side="left", fill="both", expand=True)
        self._build_canvas(self.center_frame)
        
        # 3. RIGHT SIDEBAR (Control Deck)
        self.sidebar_right = tk.Frame(self.main_container, bg="#181818", width=240, padx=10, pady=10)
        self.sidebar_right.pack(side="right", fill="y", padx=2)
        self._build_tuning_deck(self.sidebar_right)

        self._build_status_bar()
        self._bind_keys()
        self.draw_map()
        self.root.mainloop()

    def _build_menus(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Project", command=self.on_new)
        file_menu.add_command(label="Open Stencil", command=self.on_load)
        file_menu.add_command(label="Save Stencil", command=self.on_save)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        for mode in ["terrain", "elev", "moist", "cr", "mob"]:
            def mv(m=mode): return lambda: self.set_view_mode(m)
            view_menu.add_command(label=f"Heatmap: {mode.upper()}", command=mv())
        
        view_menu.add_separator()
        view_menu.add_checkbutton(label="Show Stencils", variable=self.show_stencil, command=self.draw_map)
        view_menu.add_checkbutton(label="Show Difficulty", variable=self.show_cr_overlay, command=self.draw_map)
        view_menu.add_checkbutton(label="Show Spawns", variable=self.show_mob_overlay, command=self.draw_map)

    def _build_toolbar(self):
        toolbar = tk.Frame(self.root, bg="#222", pady=5)
        toolbar.pack(side="top", fill="x")

        tk.Button(toolbar, text="SIMULATE WORLD", command=self.on_regen, bg="#00bcd4", fg="white", font=("Arial", 9, "bold"), padx=15).pack(side="left", padx=10)
        
        tk.Label(toolbar, text="SEED:", bg="#222", fg="#888", font=("Arial", 8, "bold")).pack(side="left", padx=2)
        self.seed_entry = tk.Entry(toolbar, bg="#111", fg="#fff", width=12, bd=0)
        self.seed_entry.pack(side="left", padx=5)

        phase_frame = tk.Frame(toolbar, bg="#222")
        phase_frame.pack(side="right", padx=10)
        tk.Label(phase_frame, text="CHRONOS:", bg="#222", fg="#00bcd4", font=("Arial", 7, "bold")).pack(side="left", padx=5)
        for p in ["Baseline", "Tectonics", "Hydrology", "Civ", "Final"]:
            def sp(phase=p): return lambda: self.set_view_phase(phase)
            btn = tk.Button(phase_frame, text=p[0], command=sp(), 
                            bg="#333", fg="#aaa", font=("Arial", 7), padx=8, relief="flat")
            btn.pack(side="left", padx=1)

    def _build_brush_sidebar(self, parent):
        tk.Label(parent, text="--- PALETTE ---", bg="#181818", fg="#00bcd4", font=("Arial", 9, "bold")).pack(pady=(0, 10))
        
        for cat, modes in studio_config.BIOME_CATEGORIES.items():
            tk.Label(parent, text=cat.upper(), bg="#181818", fg="#555", font=("Arial", 7, "bold")).pack(anchor="w", pady=(5, 2))
            grid_f = tk.Frame(parent, bg="#181818")
            grid_f.pack(fill="x")
            for i, m in enumerate(modes):
                def sm(mode=m): return lambda: self.set_brush_mode(mode)
                btn = tk.Button(grid_f, text=m[:4].upper(), command=sm(),
                                bg="#222", fg="#999", font=("Arial", 7), width=6, relief="flat")
                btn.grid(row=i//2, column=i%2, padx=1, pady=1)

        tk.Label(parent, text="ACTIVE TOOL", bg="#181818", fg="#555", font=("Arial", 7, "bold")).pack(anchor="w", pady=(20, 2))
        self.lbl_active_tool = tk.Label(parent, text="NONE", bg="#000", fg="#ffeb3b", font=("Courier", 10, "bold"), pady=5)
        self.lbl_active_tool.pack(fill="x")

        tk.Label(parent, text="RADIUS", bg="#181818", fg="#555", font=("Arial", 7, "bold")).pack(anchor="w", pady=(10, 2))
        bsize = tk.Scale(parent, from_=1, to=studio_config.BRUSH_MAX_RADIUS, orient="horizontal", bg="#181818", fg="#fff", troughcolor="#333", showvalue=True, command=self.update_brush_size)
        bsize.set(self.brush_radius); bsize.pack(fill="x")

        # [V17.7] LIVE TOGGLE
        self.live_show = tk.BooleanVar(value=False)
        cb = tk.Checkbutton(parent, text="LIVE CHRONOS", variable=self.live_show, 
                            bg="#181818", fg="#00bcd4", selectcolor="#000", 
                            activebackground="#181818", font=("Arial", 7, "bold"),
                            command=self.on_live_toggle)
        cb.pack(anchor="w", pady=10)

    def _build_tuning_deck(self, parent):
        tk.Label(parent, text="--- TUNING DECK ---", bg="#181818", fg="#00bcd4", font=("Arial", 9, "bold")).pack(pady=(0, 10))
        
        t_canvas = tk.Canvas(parent, bg="#181818", width=220, highlightthickness=0)
        t_scroll = tk.Scrollbar(parent, orient="vertical", command=t_canvas.yview)
        t_frame = tk.Frame(t_canvas, bg="#181818"); t_canvas.create_window((0,0), window=t_frame, anchor="nw")
        t_canvas.configure(yscrollcommand=t_scroll.set); t_canvas.pack(side="left", fill="both", expand=True); t_scroll.pack(side="right", fill="y")

        weights = [
            ("Sea Level", "sea_level"), ("Aridity", "aridity"), ("Peak Inten", "peak_intensity"), 
            ("Mtn Clust", "mtn_clusters"), ("Mtn Scale", "mtn_scale"), ("Rainfall", "moisture_level"), 
            ("Land Mass", "land_density"), ("Bio Isolat", "biome_isolation"), ("Designer Auth", "designer_authority"),
            ("Erosion", "erosion_scale"), ("Fertility", "fertility_rate"), ("Blossom", "blossom_speed"), ("Melting", "melting_point")
        ]
        for label, key in weights:
            row = tk.Frame(t_frame, bg="#181818", pady=3)
            row.pack(fill="x")
            tk.Label(row, text=label, bg="#181818", fg="#888", font=("Arial", 8)).pack(side="left")
            var = tk.DoubleVar(value=self.state.weights.get(key, 0.5))
            def _upd(k=key, v=var): self.update_weight(k, v.get())
            spin = tk.Spinbox(row, from_=0.0, to=1.0, increment=0.1, format="%.1f", width=5, 
                              textvariable=var, command=_upd, bg="#111", fg="#00bcd4", bd=0)
            spin.pack(side="right")

        tk.Label(t_frame, text="--- TELEMETRY ---", bg="#181818", fg="#555", font=("Arial", 8, "bold")).pack(pady=(25, 5))
        self.lbl_telemetry = tk.Label(t_frame, text="[ NO DATA ]", bg="#000", fg="#ccc", font=("Courier", 8), justify="left", wraplength=190, padx=5, pady=5)
        self.lbl_telemetry.pack(fill="x")

        t_frame.update_idletasks(); t_canvas.configure(scrollregion=t_canvas.bbox("all"))

    def _build_canvas(self, parent):
        canvas_f = tk.Frame(parent, bg="black")
        canvas_f.pack(fill="both", expand=True, padx=5, pady=5)
        h_s = tk.Scrollbar(canvas_f, orient="horizontal"); v_s = tk.Scrollbar(canvas_f, orient="vertical")
        self.canvas = tk.Canvas(canvas_f, bg="black", highlightthickness=0, xscrollcommand=h_s.set, yscrollcommand=v_s.set)
        h_s.config(command=self.canvas.xview); v_s.config(command=self.canvas.yview)
        h_s.pack(side="bottom", fill="x"); v_s.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.bind("<Button-1>", self.on_press); self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<Button-3>", self.on_right_click) # [V17.3] Right Click Copy
        self.canvas.bind("<Motion>", self.on_move); self.canvas.bind("<MouseWheel>", self.on_zoom)

    def _build_status_bar(self):
        sb = tk.Frame(self.root, bg="#222")
        sb.pack(side="bottom", fill="x")
        self.lbl_status = tk.Label(sb, text="STUDIO READY", bg="#222", fg="#00bcd4", font=("Arial", 8, "bold"), padx=10)
        self.lbl_status.pack(side="left")
        self.lbl_probe = tk.Label(sb, text="", bg="#222", fg="#888", font=("Arial", 8))
        self.lbl_probe.pack(side="right", padx=10)

    def on_move(self, event):
        if not self.canvas: return
        cx, cy = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        zf = (self.cell_size * self.zoom_factor)
        gx, gy = int(cx / zf), int(cy / zf)
        
        if 0 <= gx < self.state.width and 0 <= gy < self.state.height:
            active_grid = self.state.phase_grids.get(self.view_phase, self.state.grid)
            terr = active_grid[gy][gx]
            
            # Use Debug Stats (Generated) if available, else fallback to Bias (Intent)
            e = self.state.debug_stats.get("elev", self.state.bias_elev)[gy][gx] if self.state.debug_stats.get("elev") else self.state.bias_elev[gy][gx]
            m = self.state.debug_stats.get("moist", self.state.bias_moist)[gy][gx] if self.state.debug_stats.get("moist") else self.state.bias_moist[gy][gx]
            
            ox, oy = studio_config.OFFSET_X, studio_config.OFFSET_Y
            msg = f"POS: {gx+ox}, {gy+oy}\nBIO: {terr.upper()}\nE: {e:.2f} M: {m:.2f}\nPH: {self.view_phase.upper()}"
            if self.lbl_telemetry: self.lbl_telemetry.config(text=msg)
            if self.lbl_probe: self.lbl_probe.config(text=f"GRID: {gx},{gy}")
        
        self.canvas.delete("brush_ghost")
        if self.brush_mode != "none":
            R = self.brush_radius * zf
            self.canvas.create_oval(cx-R, cy-R, cx+R, cy+R, outline="#00bcd4", dash=(2,2), tags="brush_ghost")

    def _paint(self, event):
        cx, cy = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        zf = (self.cell_size * self.zoom_factor)
        gx, gy = int(cx / zf), int(cy / zf)
        R = self.brush_radius
        for dy in range(-R, R+1):
            for dx in range(-R, R+1):
                nx, ny = gx+dx, gy+dy
                if 0 <= nx < self.state.width and 0 <= ny < self.state.height:
                    if math.sqrt(dx*dx+dy*dy) <= R: 
                        self.state.apply_brush(nx, ny, self.brush_mode)
                        self.update_tile(nx, ny) # SMOOTH UPDATE
        
        # [V17.9] LIVE SURGICAL NEGOTIATION (ROI Throttled)
        if hasattr(self, 'live_show') and self.live_show.get():
            now = time.time()
            if now - getattr(self, '_last_live', 0) > 0.05: # 50fps target
                # Collect ROIs from last stroke
                touched = []
                for dy in range(-R, R+1):
                    for dx in range(-R, R+1):
                        nx, ny = gx+dx, gy+dy
                        if 0 <= nx < self.state.width and 0 <= ny < self.state.height:
                            if math.sqrt(dx*dx+dy*dy) <= R:
                                touched.append((nx, ny))
                
                self.state.live_negotiation(roi=touched)
                # Force refresh only touched tiles
                for tx, ty in touched:
                    self.update_tile(tx, ty)
                self._last_live = now

    def on_press(self, event):
        if self.brush_mode != "none": 
            self.state.push_undo()
            self._paint(event)
    def on_drag(self, event):
        if self.brush_mode != "none": self._paint(event)

    def on_undo(self, event=None):
        if self.state.pop_undo():
            self.update_status("UNDO PERFORMED")
            self.draw_map()
            
    def _bind_keys(self):
        self.root.bind("<Control-z>", self.on_undo)
        self.root.bind("<Control-Z>", self.on_undo)


    def on_right_click(self, event):
        """[V17.3] Surgical Metadata Copy: (X, Y) | Biome"""
        cx, cy = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        zf = (self.cell_size * self.zoom_factor)
        gx, gy = int(cx / zf), int(cy / zf)
        
        if 0 <= gx < self.state.width and 0 <= gy < self.state.height:
            active_grid = self.state.phase_grids.get(self.view_phase, self.state.grid)
            terr = active_grid[gy][gx]
            ox, oy = studio_config.OFFSET_X, studio_config.OFFSET_Y
            abs_str = f"({gx+ox}, {gy+oy}) | {terr.upper()}"
            
            self.root.clipboard_clear()
            self.root.clipboard_append(abs_str)
            self.set_brush_mode(terr) # [EYEDROPPER] Set active tool
            self.update_status(f"COPIED & SET: {abs_str}")

    def _get_tile_color(self, x, y):
        """Standardizes color lookup for partial and full redraws."""
        active_grid = self.state.phase_grids.get(self.view_phase, self.state.grid)
        clr = "#000"
        
        if self.view_mode == "terrain": 
            clr = data.COLOR_MAP.get(active_grid[y][x], "#000")
            # Apply Interaction Overlays (Heat blending)
            if self.show_cr_overlay and self.show_cr_overlay.get():
                cr = self.state.bias_cr[y][x]
                if cr > 0.1: clr = self._blend_hex(clr, "#ff0000", cr*0.6)
            if self.show_mob_overlay and self.show_mob_overlay.get():
                ms = self.state.bias_spawn[y][x]
                if ms > 0.1: clr = self._blend_hex(clr, "#ffffff", ms*0.6)
        elif self.view_mode == "elev":
            e_val = self.state.debug_stats.get("elev", self.state.bias_elev)[y][x]
            v = int(127 + e_val * 127)
            clr = f"#{v:02x}{v:02x}{v:02x}"
        elif self.view_mode == "moist":
            m_val = self.state.debug_stats.get("moist", self.state.bias_moist)[y][x]
            v = int(127 + m_val * 127)
            clr = f"#0000{v:02x}"
            
        return clr

    def update_tile(self, x, y):
        """Incremental update: Only touches one rectangle ID. High performance."""
        tid = self.tile_ids[(x, y)]
        clr = self._get_tile_color(x, y)
        
        # [V17.8] STENCIL REFRESH (Must run even if color is static)
        if hasattr(self, 'stencil_ids') and (x, y) in self.stencil_ids:
            sid = self.stencil_ids[(x, y)]
            if self.show_stencil.get() and self.state.bias_biomes[y][x]:
                self.canvas.itemconfig(sid, state="normal")
            else:
                self.canvas.itemconfig(sid, state="hidden")

        # [V17.8] DELTA CHECK: Skip color update if results are identical
        if self.tile_colors.get((x, y)) == clr: return
        
        self.canvas.itemconfig(tid, fill=clr)
        self.tile_colors[(x, y)] = clr

    def draw_map(self):
        """[V17.2] COPA Engine: Pre-allocates objects or updates in place."""
        if not self.canvas: return
        
        # 1. Purge check (Zoom or Grid Size changes)
        if not hasattr(self, 'tile_ids') or len(self.tile_ids) != (self.state.width * self.state.height):
            self.canvas.delete("all")
            self.tile_ids = {}
            self.tile_colors = {}
            self.stencil_ids = {}
        
        scale = self.cell_size * self.zoom_factor
        for y in range(self.state.height):
            for x in range(self.state.width):
                clr = self._get_tile_color(x, y)
                
                if (x, y) not in self.tile_ids:
                    # CREATE (Only happens on first run or zoom)
                    tid = self.canvas.create_rectangle(x*scale, y*scale, (x+1)*scale, (y+1)*scale, fill=clr, outline="")
                    self.tile_ids[(x, y)] = tid
                    
                    # Create Stencil Ghost (hidden by default)
                    sid = self.canvas.create_rectangle(x*scale+1, y*scale+1, (x+1)*scale-1, (y+1)*scale-1, 
                                                       outline="#00bcd4", dash=(1,1), state="hidden")
                    self.stencil_ids[(x, y)] = sid
                else:
                    # UPDATE (Super fast)
                    self.update_tile(x, y)
                    
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _blend_hex(self, h1, h2, a):
        r1,g1,b1 = int(h1[1:3],16), int(h1[3:5],16), int(h1[5:7],16)
        r2,g2,b2 = int(h2[1:3],16), int(h2[3:5],16), int(h2[5:7],16)
        r = int(r1*(1-a)+r2*a); g = int(g1*(1-a)+g2*a); b = int(b1*(1-a)+b2*a)
        return f"#{r:02x}{g:02x}{b:02x}"

    def update_brush_size(self, val): self.brush_radius = int(val)
    def update_tool_indicator(self): self.lbl_active_tool.config(text=self.brush_mode.upper())
    def set_brush_mode(self, mode): 
        self.brush_mode = mode
        self.update_tool_indicator()
        # [V17.5] Auto-Overlay on Interaction brushes
        if mode == "cr": self.show_cr_overlay.set(True); self.draw_map()
        elif mode == "mob": self.show_mob_overlay.set(True); self.draw_map()
        
    def set_view_phase(self, phase): self.view_phase = phase; self.draw_map()
    def set_view_mode(self, mode): self.view_mode = mode; self.draw_map()
    def update_weight(self, key, val): self.state.weights[key] = float(val)
    def update_status(self, msg): self.lbl_status.config(text=msg.upper())
    def on_regen(self):
        s = self.seed_entry.get()
        if s: self.state.weights["seed"] = s
        self.state.reset_grid(); self.state.full_generation_pass(); self.draw_map()
    def on_save(self): p = self.state.save_stencil(); self.update_status(f"Saved: {p}")
    def on_load(self): 
        if self.state.load_stencil(): self.draw_map(); self.update_status("Loaded.")
    def on_new(self):
        if messagebox.askyesno("Reset", "Purge all stencils?"): 
            self.state.clear_all_buffers(); delattr(self, 'tile_ids'); self.draw_map()
    def on_zoom(self, e): 
        # Full purge on zoom
        if hasattr(self, 'tile_ids'): delattr(self, 'tile_ids')
        if e.delta > 0: self.zoom_factor *= 1.2
        else: self.zoom_factor *= 0.8
        self.draw_map()
    def on_survey_start(self, e): pass
    def on_survey_drag(self, e): pass
    def on_survey_end(self, e): pass
    def on_live_toggle(self):
        if self.live_show.get():
            self.update_status("LIVE CHRONOS ENGAGED (SURGICAL REMAP)")
            self.draw_map()
        else:
            self.update_status("LIVE CHRONOS DISENGAGED")
