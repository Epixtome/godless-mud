"use client";

import React, { useEffect, useRef, useState, useCallback } from "react";

interface StudioCanvasProps {
  grid: string[][];
  onPaint: (x: number, y: number) => void;
  onPaintEnd: () => void;
  onHover: (x: number, y: number) => void;
  onRightClick: (x: number, y: number) => void;
  onSurvey: (start: {x: number, y: number}, end: {x: number, y: number}) => void;
  brushRadius: number;
  tileSize: number;
  zoom: number;
  viewMode: "terrain" | "elev" | "moist";
  elevMap?: number[][];
  moistMap?: number[][];
  colorMap: Record<string, string>;
  // V46.0 INTENT PROPS
  biasBiomes?: (string|null)[][];
  biasRoads?: number[][];
  biasVolume?: number[][];
}

export const StudioCanvas: React.FC<StudioCanvasProps> = ({
  grid,
  onPaint,
  onPaintEnd,
  onHover,
  onRightClick,
  onSurvey,
  brushRadius,
  tileSize,
  zoom,
  viewMode,
  elevMap,
  moistMap,
  colorMap,
  biasBiomes,
  biasRoads,
  biasVolume
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const cursorRef = useRef<HTMLDivElement>(null);
  const [isPainting, setIsPainting] = useState(false);
  const [selectionStart, setSelectionStart] = useState<{x: number, y: number} | null>(null);
  const [selectionEnd, setSelectionEnd] = useState<{x: number, y: number} | null>(null);
  const [mousePos, setMousePos] = useState<{x: number, y: number} | null>(null);

  // [V47.0] SNAPPING PERFORMANCE CURSOR
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const handleMouseMove = (e: MouseEvent) => {
      if (!cursorRef.current) return;
      const rect = canvas.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      
      // Calculate scaled grid coordinates
      const gx = Math.floor(x / (tileSize * zoom));
      const gy = Math.floor(y / (tileSize * zoom));
      
      // Target position in the unscaled coordinate system of the parent container
      const snappedX = (gx + 0.5) * tileSize;
      const snappedY = (gy + 0.5) * tileSize;

      cursorRef.current.style.transform = `translate(${snappedX}px, ${snappedY}px) translate(-50%, -50%)`;
      
      if (x < 0 || y < 0 || x > rect.width || y > rect.height) {
        cursorRef.current.style.display = "none";
      } else {
        cursorRef.current.style.display = "flex";
      }
    };

    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, [tileSize, zoom]);

  const drawGrid = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // 1. TERRAIN PASS
    for (let y = 0; y < grid.length; y++) {
      for (let x = 0; x < grid[y].length; x++) {
        let color = "#000000";
        if (viewMode === "terrain") {
          color = colorMap[grid[y][x]] || "#000000";
        } else if (viewMode === "elev" && elevMap) {
          const e = elevMap[y][x];
          const val = Math.floor(e * 255);
          color = `rgb(${val}, ${val}, ${val})`;
        } else if (viewMode === "moist" && moistMap) {
          const m = moistMap[y][x];
          const val = Math.floor(m * 255);
          color = `rgb(0, 0, ${val})`;
        }
        ctx.fillStyle = color;
        ctx.fillRect(x * tileSize, y * tileSize, tileSize, tileSize);
      }
    }

    // 2. [V46.0] VELLUM INTENT PASS
    if (biasBiomes && biasVolume) {
      for (let y = 0; y < grid.length; y++) {
        for (let x = 0; x < grid[y].length; x++) {
          const pBiome = biasBiomes[y][x];
          const vol = biasVolume[y][x];
          const pRoad = biasRoads ? biasRoads[y][x] : 0;

          if (pBiome || pRoad === 1) {
            let intentColor = "#ffffff";
            if (pRoad === 1) intentColor = "#ffffff";
            else if (pBiome === "ocean") intentColor = "#00ffff"; // ELECTRIC CYAN
            else if (pBiome === "grass") intentColor = "#44ff44";
            else intentColor = colorMap[pBiome!] || "#ffffff";

            ctx.globalAlpha = 0.3 + (Math.min(vol, 1.0) * 0.4);
            ctx.fillStyle = intentColor;
            ctx.fillRect(x * tileSize, y * tileSize, tileSize, tileSize);
            
            ctx.globalAlpha = 0.6;
            ctx.strokeStyle = intentColor;
            ctx.lineWidth = 0.5;
            ctx.strokeRect(x * tileSize, y * tileSize, tileSize, tileSize);
          }
        }
      }
      ctx.globalAlpha = 1.0;
    }
  }, [grid, viewMode, elevMap, moistMap, colorMap, tileSize, biasBiomes, biasRoads, biasVolume]);

  useEffect(() => {
    drawGrid();
  }, [drawGrid]);

  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.button === 0) { // Left Click
      setIsPainting(true);
    } else if (e.button === 2) { // Right Click
      const rect = canvasRef.current!.getBoundingClientRect();
      const x = Math.floor((e.clientX - rect.left) / (tileSize * zoom));
      const y = Math.floor((e.clientY - rect.top) / (tileSize * zoom));
      onRightClick(x, y);
    } else if (e.button === 1) { // Middle Click / Survey
      const rect = canvasRef.current!.getBoundingClientRect();
      const x = Math.floor((e.clientX - rect.left) / (tileSize * zoom));
      const y = Math.floor((e.clientY - rect.top) / (tileSize * zoom));
      setSelectionStart({x, y});
      setSelectionEnd({x, y});
    }
  };

  const handleMouseMoveInternal = (e: React.MouseEvent) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const x = Math.floor((e.clientX - rect.left) / (tileSize * zoom));
    const y = Math.floor((e.clientY - rect.top) / (tileSize * zoom));

    setMousePos({ x, y });

    if (isPainting) {
      if (x >= 0 && x < grid[0]?.length && y >= 0 && y < grid.length) {
        onPaint(x, y);
      }
    } else if (selectionStart) {
      setSelectionEnd({x, y});
    }
    onHover(x, y);
  };

  const handleMouseUp = (e: React.MouseEvent) => {
    if (e.button === 0) {
      setIsPainting(false);
      onPaintEnd();
    } else if (e.button === 1 && selectionStart && selectionEnd) {
      onSurvey(selectionStart, selectionEnd);
      setSelectionStart(null);
      setSelectionEnd(null);
    }
  };

  const R = Math.max(0, brushRadius - 1);
  const brushPx = (2 * R + 1) * tileSize;

  return (
    <div className="relative border-4 border-zinc-900 bg-black shadow-2xl overflow-hidden rounded-lg">
      <canvas
        ref={canvasRef}
        width={grid[0]?.length * tileSize}
        height={grid.length * tileSize}
        onMouseDown={handleMouseDown}
        onMouseUp={handleMouseUp}
        onMouseLeave={() => { setIsPainting(false); setSelectionStart(null); setMousePos(null); }}
        onMouseMove={handleMouseMoveInternal}
        onContextMenu={(e) => e.preventDefault()}
        className="cursor-none"
      />
      {/* V47.0 SNAPPING BRUSH CURSOR */}
      <div 
        ref={cursorRef}
        className="absolute top-0 left-0 pointer-events-none mix-blend-difference z-50 flex items-center justify-center"
        style={{
          width: brushPx,
          height: brushPx,
        }}
      >
        {/* OUTER DESIGNER RING */}
        <div className="absolute inset-0 border border-white/30 rounded-full bg-white/5" />
        
        {/* FOCUS SQUARE: THE 'ACTUAL' PIXEL */}
        <div 
          className="border border-[#00bcd4] bg-[#00bcd4]/20 shadow-[0_0_5px_rgba(0,188,212,0.5)]"
          style={{ width: tileSize, height: tileSize }}
        />
      </div>
      {/* SELECTION OVERLAY */}
      {selectionStart && selectionEnd && (
        <div 
          className="absolute border-2 border-[#00bcd4] bg-[#00bcd4]/10 pointer-events-none"
          style={{
            left: Math.min(selectionStart.x, selectionEnd.x) * tileSize,
            top: Math.min(selectionStart.y, selectionEnd.y) * tileSize,
            width: (Math.abs(selectionEnd.x - selectionStart.x) + 1) * tileSize,
            height: (Math.abs(selectionEnd.y - selectionStart.y) + 1) * tileSize,
          }}
        />
      )}
    </div>
  );
};
