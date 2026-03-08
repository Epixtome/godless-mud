import math

def visualize_blueprint():
    print("\n--- World Blueprint Visualization ---\n")
    
    # Configuration
    width = 80
    height = 40
    
    # World Bounds (Calculated to fit all anchors with padding)
    min_x, max_x = -300, 300
    min_y, max_y = -300, 350
    
    grid = [[' ' for _ in range(width)] for _ in range(height)]
    
    def world_to_grid(wx, wy):
        # Normalize to 0..1
        nx = (wx - min_x) / (max_x - min_x)
        ny = (wy - min_y) / (max_y - min_y)
        
        # Scale to grid (Min Y is North/Top, so no inversion needed for 0-indexed terminal)
        gx = int(nx * (width - 1))
        gy = int(ny * (height - 1))
        return gx, gy

    def draw_line(p1, p2, char='.'):
        x1, y1 = world_to_grid(*p1)
        x2, y2 = world_to_grid(*p2)
        
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy
        
        while True:
            if 0 <= x1 < width and 0 <= y1 < height:
                if grid[y1][x1] == ' ':
                    grid[y1][x1] = char
            if x1 == x2 and y1 == y2:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x1 += sx
            if e2 < dx:
                err += dx
                y1 += sy

    def draw_point(wx, wy, char, label=None):
        gx, gy = world_to_grid(wx, wy)
        if 0 <= gx < width and 0 <= gy < height:
            grid[gy][gx] = char
            # Simple label placement (right of point)
            if label and gx + 2 < width:
                l_str = label[:width - (gx + 3)]
                for i, c in enumerate(l_str):
                    if gx + 2 + i < width:
                        grid[gy][gx + 2 + i] = c

    # --- Data Definition ---
    center = (0, 0)
    light_cap = (0, -220)
    shadow_cap = (190, 110)
    instinct_cap = (-190, 110)
    
    # Draw Roads (Vectors)
    draw_line(center, light_cap, '.')
    draw_line(center, shadow_cap, '.')
    draw_line(center, instinct_cap, '.')
    
    # Draw Web Connections
    draw_line((100, -100), (50, -180), ',') # Ashlands -> Light
    draw_line((100, -100), (240, 80), ',')  # Ashlands -> Shadow
    
    # Draw Anchors & Outposts
    draw_point(0, 0, 'O', "Shard Crater (0,0)")
    
    draw_point(0, -220, 'L', "Light Kingdom")
    draw_point(-50, -180, 'x', "L-Farm")
    draw_point(50, -180, '!', "L-Mine")
    
    draw_point(190, 110, 'S', "Shadow Kingdom")
    draw_point(140, 80, 'x', "S-Swamp")
    draw_point(240, 80, '!', "S-Ruins")
    
    draw_point(-190, 110, 'I', "Instinct Kingdom")
    draw_point(-140, 80, 'x', "I-Jungle")
    draw_point(-240, 80, '!', "I-Canyon")

    # Render
    print("-" * width)
    for row in grid:
        print("".join(row))
    print("-" * width)

if __name__ == "__main__":
    visualize_blueprint()
