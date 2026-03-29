"use client";

import React, { useEffect, useRef, useState, useCallback } from "react";
import { useStore } from "../../store/useStore";

const WIDTH = 125;
const HEIGHT = 125;

interface Room {
    x: number;
    y: number;
    z: number;
    terrain: string;
    name?: string;
}

interface UniversalCanvasProps {
    mode: 'sculpt' | 'observe';
    // Sculpt Data
    grid?: string[][];
    elevMap?: number[][];
    moistMap?: number[][];
    biasLandmarks?: (string | null)[][];
    // Observe Data
    rooms?: Room[];
    // Shared Layers
    tideMap?: { kingdom: string, power: number }[][];
    secMap?: number[][];
    viewMode: "terrain" | "elev" | "moist" | "tide" | "sec";

    // Config
    tileSize?: number;
    brushRadius: number;
    zoom: number;
    onPaint: (x: number, y: number) => void;
    onPaintEnd: () => void;
    onHover: (x: number, y: number) => void;
    onRightClick: (x: number, y: number) => void;
    centerPos?: { x: number, y: number } | null;
}

export const UniversalCanvas: React.FC<UniversalCanvasProps> = ({
    mode,
    grid,
    rooms,
    elevMap,
    moistMap,
    tideMap,
    secMap,
    viewMode,
    tileSize = 20,
    brushRadius,
    zoom,
    onPaint,
    onPaintEnd,
    onHover,
    onRightClick,
    centerPos
}) => {
    const { terrainRegistry } = useStore();
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const [isPainting, setIsPainting] = useState(false);
    const [offset, setOffset] = useState({ x: 0, y: 0 });
    const [viewportZoom, setViewportZoom] = useState(zoom || 25);
    const [lastMouse, setLastMouse] = useState({ x: 0, y: 0 });
    const [isPanning, setIsPanning] = useState(false);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        if (mode === 'sculpt') {
            const size = tileSize * (viewportZoom / 10);
            setOffset({
                x: (canvas.parentElement?.clientWidth || 800) / 2 - (WIDTH * size) / 2,
                y: (canvas.parentElement?.clientHeight || 600) / 2 - (HEIGHT * size) / 2
            });
        } else if (centerPos && mode === 'observe') {
            setOffset({
                x: (canvas.parentElement?.clientWidth || 800) / 2 - centerPos.x * viewportZoom,
                y: (canvas.parentElement?.clientHeight || 600) / 2 - centerPos.y * viewportZoom
            });
        }
    }, [mode, centerPos]); // RE-CENTER ON MODE CHANGE OR PROP

    const draw = useCallback(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext("2d");
        if (!ctx) return;

        // Standard Resize
        canvas.width = canvas.parentElement?.clientWidth || 800;
        canvas.height = canvas.parentElement?.clientHeight || 600;

        ctx.fillStyle = "#020617";
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // Core Drawing Logic
        if (mode === 'sculpt' && grid) {
            // FIXED GRID SCULPTING
            const drawX = offset.x;
            const drawY = offset.y;
            const size = tileSize * (viewportZoom / 10);

            for (let y = 0; y < grid.length; y++) {
                for (let x = 0; x < grid[y].length; x++) {
                    const px = drawX + x * size;
                    const py = drawY + y * size;

                    if (px + size < 0 || px > canvas.width || py + size < 0 || py > canvas.height) continue;

                    let color = "#111111";
                    if (viewMode === "terrain") {
                        color = terrainRegistry?.terrains[grid[y][x]]?.hex || "#444";
                    } else if (viewMode === "elev" && elevMap) {
                        const e = Math.floor(elevMap[y][x] * 255);
                        color = `rgb(${e}, ${e}, ${e})`;
                    } else if (viewMode === "moist" && moistMap) {
                        const m = Math.floor(moistMap[y][x] * 255);
                        color = `rgb(0, 0, ${m})`;
                    } else if (viewMode === "tide" && tideMap) {
                        const t = tideMap[y][x];
                        const alpha = Math.min(1.0, t.power / 25.0);
                        color = t.kingdom === "light" ? `rgba(0, 188, 212, ${alpha})` : (t.kingdom === "dark" ? `rgba(156, 39, 176, ${alpha})` : "#0a0a0a");
                    } else if (viewMode === "sec" && secMap) {
                        const s = secMap[y][x];
                        color = s > 0.7 ? `rgba(34, 197, 94, ${s})` : (s > 0.3 ? `rgba(234, 179, 8, ${s})` : `rgba(239, 68, 68, ${Math.max(0.1, s)})`);
                    }

                    ctx.fillStyle = color;
                    ctx.fillRect(px, py, size - 0.5, size - 0.5);
                }
            }
        } else if (mode === 'observe' && rooms) {
            // DYNAMIC SPARSE OBSERVATION
            rooms.forEach(room => {
                const px = offset.x + room.x * viewportZoom;
                const py = offset.y + room.y * viewportZoom;

                if (px + viewportZoom < 0 || px > canvas.width || py + viewportZoom < 0 || py > canvas.height) return;

                let color = terrainRegistry?.terrains[room.terrain]?.studio_hex || "#1e293b";

                // Overlay ViewModes on Live Rooms
                if (viewMode === "tide" && tideMap) {
                    // Map room coords to tide map if possible? 
                    // High complexity: For now, favor terrain colors for 'Observe'.
                }

                ctx.fillStyle = color;
                ctx.fillRect(px, py, viewportZoom - 1, viewportZoom - 1);
            });
        }
    }, [mode, grid, rooms, elevMap, moistMap, tideMap, secMap, viewMode, offset, viewportZoom, terrainRegistry]);

    useEffect(() => {
        let frame = requestAnimationFrame(function loop() {
            draw();
            frame = requestAnimationFrame(loop);
        });
        return () => cancelAnimationFrame(frame);
    }, [draw]);

    const handleMouseDown = (e: React.MouseEvent) => {
        if (e.button === 1 || e.shiftKey) {
            setIsPanning(true);
        } else {
            setIsPainting(true);
            const rect = canvasRef.current!.getBoundingClientRect();
            const gx = Math.floor((e.clientX - rect.left - offset.x) / (mode === 'sculpt' ? (tileSize * (viewportZoom / 10)) : viewportZoom));
            const gy = Math.floor((e.clientY - rect.top - offset.y) / (mode === 'sculpt' ? (tileSize * (viewportZoom / 10)) : viewportZoom));
            onPaint(gx, gy);
        }
        setLastMouse({ x: e.clientX, y: e.clientY });
    };

    const handleMouseMove = (e: React.MouseEvent) => {
        const rect = canvasRef.current!.getBoundingClientRect();
        const gx = Math.floor((e.clientX - rect.left - offset.x) / (mode === 'sculpt' ? (tileSize * (viewportZoom / 10)) : viewportZoom));
        const gy = Math.floor((e.clientY - rect.top - offset.y) / (mode === 'sculpt' ? (tileSize * (viewportZoom / 10)) : viewportZoom));

        onHover(gx, gy);

        if (isPanning) {
            setOffset(prev => ({ x: prev.x + (e.clientX - lastMouse.x), y: prev.y + (e.clientY - lastMouse.y) }));
        } else if (isPainting) {
            onPaint(gx, gy);
        }
        setLastMouse({ x: e.clientX, y: e.clientY });
    };

    return (
        <div className="absolute inset-0 bg-slate-950 cursor-crosshair overflow-hidden">
            <canvas
                ref={canvasRef}
                onMouseDown={handleMouseDown}
                onMouseMove={handleMouseMove}
                onMouseUp={() => { setIsPainting(false); setIsPanning(false); onPaintEnd(); }}
                onWheel={(e) => {
                    const delta = e.deltaY > 0 ? 0.9 : 1.1;
                    setViewportZoom(prev => Math.max(1, Math.min(300, prev * delta)));
                }}
                onContextMenu={(e) => {
                    e.preventDefault();
                    const rect = canvasRef.current!.getBoundingClientRect();
                    const gx = Math.floor((e.clientX - rect.left - offset.x) / (mode === 'sculpt' ? (tileSize * (viewportZoom / 10)) : viewportZoom));
                    const gy = Math.floor((e.clientY - rect.top - offset.y) / (mode === 'sculpt' ? (tileSize * (viewportZoom / 10)) : viewportZoom));
                    onRightClick(gx, gy);
                }}
                className="w-full h-full block"
            />
            {/* Visual HUD Layers could go here */}
        </div>
    );
};
