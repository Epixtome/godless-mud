import tkinter as tk
from tkinter import ttk, messagebox
import math, os, time
import sys

# Ensure parent directory is searchable for legacy engines
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Core Bridge
from toa_core import TOAState
import toa_logic
import architect_data

class TOAUI:
    """[TOA V20.0] The Omnipresent Architect Interface. Professional & High-Performance."""
    def __init__(self, state):
        self.state = state
        self.root = None
        self.canvas = None
        self.zoom = 1.0
        self.cell_sz = 6
        
        # Performance Cache
        self.tile_ids = {}
        self.tile_colors = {} # Color caching to prevent flicker
        self.last_live = 0
        
        # Tooling
        self.tool = "peak"
        self.brush_r = 4
        self.show_live = True

    def boot(self):
        self.root = tk.Tk()
        self.root.title("GODLESS ARCHITECT: OMNIPRESENT STUDIO - V20.0")
        self.root.geometry("1400x950")
        self.root.configure(bg="#0a0a0a")
        
        self.build_toolbar()
        
        # PRO 3-COLUMN LAYOUT
        self.main = tk.Frame(self.root, bg="#0a0a0a")
        self.main.pack(fill="both", expand=True)
        
        # 1. LEFT SIDEBAR (The Palette)
        self.sidebar_left = tk.Frame(self.main, bg="#111", width=160, padx=10, pady=10)
        self.sidebar_left.pack(side="left", fill="y", padx=1)
        self.build_palette(self.sidebar_left)
        
        # 2. CENTER PILLAR (The Viewport)
        self.center = tk.Frame(self.main, bg="black")
        self.center.pack(side="left", fill="both", expand=True)
        self.build_viewport(self.center)
        
        # 3. RIGHT SIDEBAR (The Tuning Deck)
        self.sidebar_right = tk.Frame(self.main, bg="#111", width=240, padx=10, pady=10)
        self.sidebar_right.pack(side="right", fill="y", padx=1)
        self.build_tuning_deck(self.sidebar_right)
        
        self.build_status_bar()
        self.bind_keys()
        
        # Initial Draw
        self.root.after(100, self.draw_map)
        self.root.mainloop()

    def build_toolbar(self):
        bar = tk.Frame(self.root, bg="#181818", pady=5)
        bar.pack(side="top", fill="x")
        
        tk.Button(bar, text="FORCE GENERATE", command=self.on_force_gen, 
                  bg="#00bcd4", fg="white", font=("Arial", 9, "bold"), padx=15).pack(side="left", padx=10)
        
        # Seed Entry
        tk.Label(bar, text="SEED:", bg="#181818", fg="#555", font=("Arial", 8, "bold")).pack(side="left", padx=2)
        self.seed_var = tk.StringVar(value=self.state.weights.get("seed", ""))
        self.seed_entry = tk.Entry(bar, textvariable=self.seed_var, bg="#000", fg="#fff", width=15, bd=0)
        self.seed_entry.pack(side="left", padx=5)

    def build_palette(self, parent):
        tk.Label(parent, text="--- PALETTE ---", bg="#111", fg="#00bcd4", font=("Arial", 9, "bold")).pack(pady=(0, 15))
        
        # Hardcoded categories based on Studio Standard
        cats = {
            "Sculpt": ["peak", "water", "rise", "sink", "valley"],
            "Climate": ["dry", "moist", "plains", "forest", "desert"],
            "Infrastructure": ["road", "bridge", "erase"],
            "Interaction": ["cr", "mob"]
        }
        
        for name, tools in cats.items():
            tk.Label(parent, text=name.upper(), bg="#111", fg="#444", font=("Arial", 7, "bold")).pack(anchor="w", pady=(10, 2))
            grid = tk.Frame(parent, bg="#111")
            grid.pack(fill="x")
            for i, t in enumerate(tools):
                def st(m=t): return lambda: self.set_tool(m)
                btn = tk.Button(grid, text=t[:4].upper(), command=st(),
                                bg="#181818", fg="#888", font=("Arial", 7), width=7, relief="flat")
                btn.grid(row=i//2, column=i%2, padx=1, pady=1)

        tk.Label(parent, text="RADIUS", bg="#111", fg="#444", font=("Arial", 7, "bold")).pack(anchor="w", pady=(25, 2))
        self.r_scale = tk.Scale(parent, from_=1, to=20, orient="horizontal", bg="#111", fg="#fff", highlightthickness=0)
        self.r_scale.set(self.brush_r); self.r_scale.pack(fill="x")
        self.r_scale.bind("<ButtonRelease-1>", lambda e: self.set_radius(self.r_scale.get()))

        self.lbl_active = tk.Label(parent, text="PEAK", bg="#000", fg="#ffeb3b", font=("Courier", 10, "bold"), pady=10)
        self.lbl_active.pack(fill="x", pady=20)

    def build_tuning_deck(self, parent):
        tk.Label(parent, text="--- TUNING DECK ---", bg="#111", fg="#00bcd4", font=("Arial", 9, "bold")).pack(pady=(0, 15))
        
        scroll = tk.Canvas(parent, bg="#111", highlightthickness=0)
        scr_bar = tk.Scrollbar(parent, orient="vertical", command=scroll.yview)
        frame = tk.Frame(scroll, bg="#111")
        scroll.create_window((0,0), window=frame, anchor="nw")
        scroll.configure(yscrollcommand=scr_bar.set); scroll.pack(side="left", fill="both", expand=True); scr_bar.pack(side="right", fill="y")

        params = [
            ("Sea Level", "sea_level"), ("Aridity", "aridity"), ("Peak Intensity", "peak_intensity"),
            ("Mtn Clusters", "mtn_clusters"), ("Mtn Scale", "mtn_scale"), ("Rainfall", "moisture_level"),
            ("Land Density", "land_density")
        ]
        for name, key in params:
            row = tk.Frame(frame, bg="#111", pady=4)
            row.pack(fill="x")
            tk.Label(row, text=name, bg="#111", fg="#666", font=("Arial", 8)).pack(side="left")
            var = tk.DoubleVar(value=self.state.weights.get(key, 0.5))
            def _upd(k=key, v=var): self.state.weights[k] = v.get(); self._negotiate()
            spin = tk.Spinbox(row, from_=0.0, to=1.0, increment=0.1, format="%.1f", width=5,
                              textvariable=var, command=_upd, bg="#000", fg="#00bcd4", bd=0)
            spin.pack(side="right")

    def build_viewport(self, parent):
        self.canvas = tk.Canvas(parent, bg="#000", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Button-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<Motion>", self.on_move)

    def build_status_bar(self):
        sb = tk.Frame(self.root, bg="#111", pady=2)
        sb.pack(side="bottom", fill="x")
        self.lbl_status = tk.Label(sb, text="TOA ACTIVE", bg="#111", fg="#00bcd4", font=("Arial", 8, "bold"), padx=10)
        self.lbl_status.pack(side="left")

    def bind_keys(self):
        self.root.bind("<Control-z>", lambda e: self.on_undo())

    def on_undo(self):
        if self.state.undo_stack:
            last = self.state.undo_stack.pop()
            self.state.bias_elev = last["elev"]
            self.state.bias_moist = last["moist"]
            self.state.bias_volume = last["volume"]
            self.state.bias_biomes = last["biomes"]
            self.state.bias_roads = last["roads"]
            self._negotiate()
            self.draw_map()

    def set_tool(self, mode):
        self.tool = mode
        self.lbl_active.config(text=mode.upper())

    def set_radius(self, r): self.brush_r = int(r)

    def on_move(self, event):
        self.canvas.delete("ghost")
        r = self.brush_r * self.cell_sz
        cx, cy = event.x, event.y
        self.canvas.create_oval(cx-r, cy-r, cx+r, cy+r, outline="#00bcd4", dash=(2,2), tags="ghost")

    def on_press(self, event):
        self.state.push_undo_snap()
        self._paint(event)

    def on_drag(self, event):
        self._paint(event)

    def _paint(self, event):
        gx, gy = int(event.x / self.cell_sz), int(event.y / self.cell_sz)
        R = self.brush_r
        touched = []
        for dy in range(-R, R+1):
            for dx in range(-R, R+1):
                nx, ny = gx+dx, gy+dy
                if 0 <= nx < self.state.width and 0 <= ny < self.state.height:
                    if math.sqrt(dx*dx+dy*dy) <= R:
                        self.state.apply_brush(nx, ny, self.tool)
                        touched.append((nx, ny))
        
        # Performance Throttled Negotiation
        now = time.time()
        if now - self.last_live > 0.05: # 20fps Live Update
            self._negotiate(roi=touched)
            self.draw_map(roi=touched)
            self.last_live = now

    def _negotiate(self, roi=None):
        """Bridges UI to the high-speed negotiation engine."""
        import toa_logic
        toa_logic.synchronize_negotiation(self.state, roi=roi)

    def on_force_gen(self):
        """Full re-simulation with all phases."""
        self._negotiate() # Full ROI
        self.draw_map()

    def draw_map(self, roi=None):
        """High-Performance ROI Refresh."""
        scale = self.cell_sz
        if not self.tile_ids:
            # Full allocation
            for y in range(self.state.height):
                for x in range(self.state.width):
                    tid = self.canvas.create_rectangle(x*scale, y*scale, (x+1)*scale, (y+1)*scale, outline="")
                    self.tile_ids[(x, y)] = tid
        
        from architect_data import COLOR_MAP
        coords = roi if roi else [(x, y) for y in range(self.state.height) for x in range(self.state.width)]
        
        for x, y in coords:
            biome = self.state.grid[y][x]
            clr = COLOR_MAP.get(biome, "#000")
            
            # [V20.0] Delta Check
            if self.tile_colors.get((x,y)) == clr: continue
            
            self.canvas.itemconfig(self.tile_ids[(x,y)], fill=clr)
            self.tile_colors[(x,y)] = clr
