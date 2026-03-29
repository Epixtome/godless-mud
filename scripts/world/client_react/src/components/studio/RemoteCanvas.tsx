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
  onHover?: (x: number, y: number) => void;
  onRightClick?: (x: number, y: number) => void;
  onSelectionChange?: (bounds: { x1: number, y1: number, x2: number, y2: number }) => void;
  centerPos?: { x: number, y: number } | null;
}

import { useStore } from '../../store/useStore';

const COLOR_MAP: Record<string, string> = {
  ocean: "#030617",
  water: "#0c1e33",
  lake: "#0a2a47",
  plains: "#06290d",
  grass: "#0a3d14",
  meadow: "#145c1f",
  mountain: "#1e1e24",
  high_mountain: "#2b2b36",
  peak: "#f8fafc",
  forest: "#062410",
  dense_forest: "#041409",
  swamp: "#111717",
  desert: "#2b2218",
  wasteland: "#1a0f0a",
  city: "#1e1b4b",
  shrine: "#4c1d95",
  docks: "#292524",
  road: "#0f172a",
  cobblestone: "#1e293b",
  bridge: "#334155",
  beach: "#3b3425",
  dirt_road: "#2d1b0d",
  ruins: "#0f1718",
  barrows: "#1a1c1d",
  monument: "#164e63",
  tower: "#450a0a",
  snow: "#f1f5f9",
  tundra: "#334155",
  cliffs: "#1e1e1e",
  glacier: "#0c4a6e",
  market_ward: "#1e1b4b",
  residential_ward: "#111827"
};

const RemoteCanvas: React.FC<CanvasProps> = ({
  rooms,
  selectedRoom,
  onRoomSelect,
  brushSize,
  activeTerrain,
  elevations,
  onCellClick,
  onHover,
  onRightClick,
  onSelectionChange,
  centerPos
}) => {
  const { terrainRegistry } = useStore();
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(25);
  const [isDragging, setIsDragging] = useState(false);
  const [isPainting, setIsPainting] = useState(false);
  const [lastPainted, setLastPainted] = useState<{ x: number, y: number } | null>(null);
  const [lastMouse, setLastMouse] = useState({ x: 0, y: 0 });
  const [hoverPos, setHoverPos] = useState<{ x: number, y: number } | null>(null);
  const [dragStart, setDragStart] = useState<{ x: number, y: number } | null>(null);

  // Initial centering
  useEffect(() => {
    if (centerPos) {
      const canvas = canvasRef.current;
      if (!canvas) return;
      setOffset({
        x: canvas.width / 2 - centerPos.x * zoom,
        y: canvas.height / 2 - centerPos.y * zoom
      });
    }
  }, [centerPos]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const resize = () => {
      canvas.width = canvas.parentElement?.clientWidth || 800;
      canvas.height = canvas.parentElement?.clientHeight || 600;
    };
    resize();
    window.addEventListener('resize', resize);

    let animationFrame: number;
    const render = () => {
      ctx.fillStyle = '#020617';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Grid
      ctx.strokeStyle = 'rgba(255,255,255,0.03)';
      ctx.lineWidth = 1;
      const startX = offset.x % zoom;
      const startY = offset.y % zoom;
      for (let x = startX; x < canvas.width; x += zoom) {
        ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, canvas.height); ctx.stroke();
      }
      for (let y = startY; y < canvas.height; y += zoom) {
        ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(canvas.width, y); ctx.stroke();
      }

      // Rooms
      rooms.forEach(room => {
        const x = room.x * zoom + offset.x;
        const y = room.y * zoom + offset.y;

        if (x + zoom < 0 || x > canvas.width || y + zoom < 0 || y > canvas.height) return;


        let color = COLOR_MAP[room.terrain] || '#333';
        if (terrainRegistry?.terrains?.[room.terrain]) {
          color = terrainRegistry.terrains[room.terrain].studio_hex;
        }
        ctx.fillStyle = color;
        ctx.fillRect(x, y, zoom - 1, zoom - 1);

        if (selectedRoom?.x === room.x && selectedRoom?.y === room.y) {
          ctx.strokeStyle = '#00bcd4';
          ctx.lineWidth = 2;
          ctx.strokeRect(x - 1, y - 1, zoom + 1, zoom + 1);
        }
      });

      // Drag Selection Box
      if (dragStart && isDragging && !isPainting) {
        const rect = canvas.getBoundingClientRect();
        const mouseX = (lastMouse.x - rect.left - offset.x) / zoom;
        const mouseY = (lastMouse.y - rect.top - offset.y) / zoom;

        const x1 = Math.min(dragStart.x, mouseX) * zoom + offset.x;
        const y1 = Math.min(dragStart.y, mouseY) * zoom + offset.y;
        const w = Math.abs(dragStart.x - mouseX) * zoom;
        const h = Math.abs(dragStart.y - mouseY) * zoom;

        ctx.fillStyle = 'rgba(0, 188, 212, 0.1)';
        ctx.fillRect(x1, y1, w, h);
        ctx.strokeStyle = '#00bcd4';
        ctx.setLineDash([5, 5]);
        ctx.strokeRect(x1, y1, w, h);
        ctx.setLineDash([]);
      }

      animationFrame = requestAnimationFrame(render);
    };
    render();

    return () => {
      window.removeEventListener('resize', resize);
      cancelAnimationFrame(animationFrame);
    };
  }, [rooms, offset, zoom, selectedRoom, dragStart, isDragging, isPainting, lastMouse]);

  const handleMouseDown = (e: React.MouseEvent) => {
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;
    const x = Math.floor((e.clientX - rect.left - offset.x) / zoom);
    const y = Math.floor((e.clientY - rect.top - offset.y) / zoom);

    if (e.button === 1 || e.shiftKey) {
      setIsDragging(true);
      setLastMouse({ x: e.clientX, y: e.clientY });
    } else {
      if (activeTerrain) {
        setIsPainting(true);
        onCellClick(x, y);
        setLastPainted({ x, y });
      } else {
        setIsDragging(true);
        setDragStart({ x, y });
        onRoomSelect(rooms.find(r => x === r.x && y === r.y) || null);
        onCellClick(x, y);
      }
    }
    setLastMouse({ x: e.clientX, y: e.clientY });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;
    const x = Math.floor((e.clientX - rect.left - offset.x) / zoom);
    const y = Math.floor((e.clientY - rect.top - offset.y) / zoom);

    setHoverPos({ x, y });
    if (onHover) onHover(x, y);

    if (isDragging) {
      if (e.button === 1 || e.shiftKey) {
        const dx = e.clientX - lastMouse.x;
        const dy = e.clientY - lastMouse.y;
        setOffset(prev => ({ x: prev.x + dx, y: prev.y + dy }));
      }
    } else if (isPainting && activeTerrain) {
      if (lastPainted?.x !== x || lastPainted?.y !== y) {
        onCellClick(x, y);
        setLastPainted({ x, y });
      }
    }
    setLastMouse({ x: e.clientX, y: e.clientY });
  };

  const handleMouseUp = (e: React.MouseEvent) => {
    if (dragStart && onSelectionChange && !isPainting) {
      const rect = canvasRef.current?.getBoundingClientRect();
      if (!rect) return;
      const x = Math.floor((e.clientX - rect.left - offset.x) / zoom);
      const y = Math.floor((e.clientY - rect.top - offset.y) / zoom);

      onSelectionChange({
        x1: Math.min(dragStart.x, x),
        y1: Math.min(dragStart.y, y),
        x2: Math.max(dragStart.x, x),
        y2: Math.max(dragStart.y, y)
      });
    }

    setIsDragging(false);
    setIsPainting(false);
    setLastPainted(null);
    setDragStart(null);
  };

  const handleWheel = (e: React.WheelEvent) => {
    const delta = e.deltaY > 0 ? 0.9 : 1.1;
    const newZoom = Math.max(0.01, Math.min(300, zoom * delta));
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;
    const wx = (mx - offset.x) / zoom;
    const wy = (my - offset.y) / zoom;
    setZoom(newZoom);
    setOffset({ x: mx - wx * newZoom, y: my - wy * newZoom });
  };

  const handleContextMenu = (e: React.MouseEvent) => {
    e.preventDefault();
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;
    const x = Math.floor((e.clientX - rect.left - offset.x) / zoom);
    const y = Math.floor((e.clientY - rect.top - offset.y) / zoom);
    if (onRightClick) onRightClick(x, y);
  };

  return (
    <canvas
      ref={canvasRef}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onWheel={handleWheel}
      onContextMenu={handleContextMenu}
      className="absolute inset-0 cursor-crosshair"
    />
  );
};

export default RemoteCanvas;
