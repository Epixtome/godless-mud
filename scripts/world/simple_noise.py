import random

class SimpleNoise:
    def __init__(self, width, height, seed=None):
        self.width = width
        self.height = height
        if seed: random.seed(seed)
        self.grid = [[random.random() for _ in range(height)] for _ in range(width)]

    def fade(self, t):
        # Smootherstep function: 6t^5 - 15t^4 + 10t^3
        return t * t * t * (t * (t * 6 - 15) + 10)

    def get(self, x, y):
        x0 = int(x) % self.width
        x1 = (x0 + 1) % self.width
        y0 = int(y) % self.height
        y1 = (y0 + 1) % self.height
        sx = x - int(x)
        sy = y - int(y)
        n00 = self.grid[x0][y0]
        n10 = self.grid[x1][y0]
        n01 = self.grid[x0][y1]
        n11 = self.grid[x1][y1]
        
        # Apply smoothing to interpolation weights
        u = self.fade(sx)
        v = self.fade(sy)
        
        ix0 = n00 + u * (n10 - n00)
        ix1 = n01 + u * (n11 - n01)
        return ix0 + v * (ix1 - ix0)

    def fbm(self, x, y, octaves=4, persistence=0.5, lacunarity=2.0):
        total = 0
        frequency = 1
        amplitude = 1
        max_value = 0
        for _ in range(octaves):
            total += self.get(x * frequency, y * frequency) * amplitude
            max_value += amplitude
            amplitude *= persistence
            frequency *= lacunarity
        return total / max_value
