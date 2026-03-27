import React, { useRef, useEffect, useState, useMemo } from 'react';

interface Room {
  x: number;
  y: number;
  z: number;
  terrain: string;
  name: string;
}

interface CanvasProps {
  rooms: Room[];
  selectedRoom: Room | null;
  onRoomSelect: (room: Room | null) => void;
  brushSize: number;
  activeTerrain: string;
  elevations: Record<string, number>;
  onCellClick: (x: number, y: number) => void;
}

const COLOR_MAP: Record<string, string> = {
  ocean: "#000033",
  water: "#0066cc",
  lake: "#004499",
  plains: "#228B22",
  grass: "#32CD32",
  meadow: "#7CFC00",
  mountain: "#808080",
  high_mountain: "#A9A9A9",
  peak: "#FFFFFF",
  forest: "#006400",
  dense_forest: "#004d00",
  swamp: "#2f4f4f",
  desert: "#edc9af",
  wasteland: "#3e2723",
  city: "#ffd700",
  shrine: "#ff00ff",
  docks: "#795548",
  road: "#555555",
  cobblestone: "#777777",
  bridge: "#9e9e9e",
  beach: "#f5deb3",
  dirt_road: "#8b4513",
  ruins: "#424242",
  barrows: "#37474f",
  monument: "#00bcd4",
  tower: "#d32f2f",
  snow: "#f0f0f0",
  tundra: "#8d99ae",
  cliffs: "#4a4a4a",
  glacier: "#afeeee",
  market_ward: "#ffd700",
  residential_ward: "#80deea"
};

const RemoteCanvas: React.FC<CanvasProps> = ({ 
  rooms, 
  selectedRoom, 
  onRoomSelect, 
  brushSize, 
  activeTerrain,
  elevations,
  onCellClick
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(20);
  const [isDragging, setIsDragging] = useState(false);
  const [lastMouse, setLastMouse] = useState({ x: 0, y: 0 });
  const [hoverPos, setHoverPos] = useState<{ x: number, y: number } | null>(null);

  // Boundary calculations
  const bounds = useMemo(() => {
    if (rooms.length === 0) return { minX: 0, minY: 0, maxX: 0, maxY: 0 };
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    rooms.forEach(r => {
      if (r.x < minX) minX = r.x;
      if (r.y < minY) minY = r.y;
      if (r.x > maxX) maxX = r.x;
      if (r.y > maxY) maxY = r.y;
    });
    // Add some padding
    return { minX: minX - 5, minY: minY - 5, maxX: maxX + 5, maxY: maxY + 5 };
  }, [rooms]);

  // Initial centering
  useEffect(() => {
    if (rooms.length > 0 && offset.x === 0 && offset.y === 0) {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const width = canvas.width;
      const height = canvas.height;
      const midX = (bounds.minX + bounds.maxX) / 2;
      const midY = (bounds.minY + bounds.maxY) / 2;
      setOffset({
        x: width / 2 - (midX - bounds.minX) * zoom,
        y: height / 2 - (midY - bounds.minY) * zoom
      });
    }
  }, [rooms.length > 0]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Handle Resize
    const resize = () => {
      canvas.width = canvas.parentElement?.clientWidth || 800;
      canvas.height = canvas.parentElement?.clientHeight || 600;
    };
    resize();
    window.addEventListener('resize', resize);

    // Render Function
    const render = () => {
      ctx.fillStyle = '#0a0a0c';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Draw Grid Lines
      if (zoom > 8) {
        ctx.beginPath();
        ctx.strokeStyle = '#1a1a1e';
        ctx.lineWidth = 1;

        // Calculate visible range
        const startX = Math.floor(-offset.x / zoom) + bounds.minX;
        const endX = Math.ceil((canvas.width - offset.x) / zoom) + bounds.minX;
        const startY = Math.floor(-offset.y / zoom) + bounds.minY;
        const endY = Math.ceil((canvas.height - offset.y) / zoom) + bounds.minY;

        for (let x = startX; x <= endX; x++) {
          const sx = (x - bounds.minX) * zoom + offset.x;
          ctx.moveTo(sx, 0);
          ctx.lineTo(sx, canvas.height);
        }
        for (let y = startY; y <= endY; y++) {
          const sy = (y - bounds.minY) * zoom + offset.y;
          ctx.moveTo(0, sy);
          ctx.lineTo(canvas.width, sy);
        }
        ctx.stroke();
      }

      // Draw Rooms
      rooms.forEach(room => {
        const screenX = (room.x - bounds.minX) * zoom + offset.x;
        const screenY = (room.y - bounds.minY) * zoom + offset.y;
        
        // Culling
        if (screenX + zoom < 0 || screenX > canvas.width || screenY + zoom < 0 || screenY > canvas.height) return;

        const baseColor = COLOR_MAP[room.terrain] || '#fff';
        const elevation = elevations[room.terrain] || 0;
        
        // Dynamic shading based on elevation
        ctx.fillStyle = baseColor;
        ctx.fillRect(screenX, screenY, zoom, zoom);
        
        if (elevation > 0) {
            ctx.fillStyle = `rgba(255, 255, 255, ${elevation * 0.05})`;
            ctx.fillRect(screenX, screenY, zoom, zoom);
        } else if (elevation < 0) {
            ctx.fillStyle = `rgba(0, 0, 0, ${Math.abs(elevation) * 0.1})`;
            ctx.fillRect(screenX, screenY, zoom, zoom);
        }

        // Grid shadow for depth
        ctx.strokeStyle = 'rgba(0,0,0,0.3)';
        ctx.lineWidth = 1;
        ctx.strokeRect(screenX, screenY, zoom, zoom);

        // Highlight Selected
        if (selectedRoom && selectedRoom.x === room.x && selectedRoom.y === room.y) {
          ctx.strokeStyle = '#00bcd4';
          ctx.lineWidth = 3;
          ctx.strokeRect(screenX, screenY, zoom, zoom);
          
          ctx.shadowBlur = 15;
          ctx.shadowColor = '#00bcd4';
          ctx.strokeRect(screenX, screenY, zoom, zoom);
          ctx.shadowBlur = 0;
        }
      });

      // Hover Preview
      if (hoverPos) {
        const hx = (hoverPos.x - bounds.minX) * zoom + offset.x;
        const hy = (hoverPos.y - bounds.minY) * zoom + offset.y;
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.4)';
        ctx.setLineDash([4, 4]);
        ctx.strokeRect(hx, hy, zoom, zoom);
        ctx.setLineDash([]);
        
        if (brushSize > 1) {
            // Visualize brush radius if we add it
        }
      }
    };

    render();
    return () => window.removeEventListener('resize', resize);
  }, [rooms, offset, zoom, selectedRoom, bounds, hoverPos, elevations]);

  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.button === 1 || e.shiftKey) { // Middle click or shift drag to pan
      setIsDragging(true);
      setLastMouse({ x: e.clientX, y: e.clientY });
    } else {
      // Primary click to select/paint
      const rect = canvasRef.current?.getBoundingClientRect();
      if (!rect) return;
      const x = Math.floor((e.clientX - rect.left - offset.x) / zoom + bounds.minX);
      const y = Math.floor((e.clientY - rect.top - offset.y) / zoom + bounds.minY);
      onRoomSelect(rooms.find(r => x === r.x && y === r.y) || null);
      onCellClick(x, y);
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;
    
    const x = Math.floor((e.clientX - rect.left - offset.x) / zoom + bounds.minX);
    const y = Math.floor((e.clientY - rect.top - offset.y) / zoom + bounds.minY);
    setHoverPos({ x, y });

    if (isDragging) {
      const dx = e.clientX - lastMouse.x;
      const dy = e.clientY - lastMouse.y;
      setOffset(prev => ({ x: prev.x + dx, y: prev.y + dy }));
      setLastMouse({ x: e.clientX, y: e.clientY });
    }
  };

  const handleMouseUp = () => setIsDragging(false);

  const handleWheel = (e: React.WheelEvent) => {
    const delta = e.deltaY > 0 ? 0.9 : 1.1;
    const newZoom = Math.max(2, Math.min(100, zoom * delta));
    
    // Zoom towards mouse
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    
    const worldX = (mouseX - offset.x) / zoom;
    const worldY = (mouseY - offset.y) / zoom;
    
    setZoom(newZoom);
    setOffset({
        x: mouseX - worldX * newZoom,
        y: mouseY - worldY * newZoom
      });
  };

  return (
    <canvas
      ref={canvasRef}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onWheel={handleWheel}
      onMouseLeave={() => setHoverPos(null)}
      className="w-full h-full cursor-crosshair"
    />
  );

};

export default RemoteCanvas;
