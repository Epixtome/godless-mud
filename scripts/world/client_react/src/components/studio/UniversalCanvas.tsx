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
    elevation?: number;
}

interface UniversalCanvasProps {
    mode: 'sculpt' | 'observe';
    grid?: string[][];
    rooms?: Room[];
    elevMap?: number[][];
    moistMap?: number[][];
    viewMode: "terrain" | "elev" | "moist" | "tide" | "sec";
    tileSize?: number;
    brushRadius: number;
    zoom: number;
    onPaint: (x: number, y: number) => void;
    onPaintEnd: () => void;
    onHover: (x: number, y: number) => void;
    onRightClick: (x: number, y: number) => void;
    onCenterRequest: (x: number, y: number) => void;
    centerPos?: { x: number, y: number } | null;
    anchorX?: number;
    anchorY?: number;
}

/**
 * [V11.16] Godless "Infinite Radiance" Canvas
 * High-performance offscreen buffering with anti-darkening logic and limitless zoom.
 */
export const UniversalCanvas: React.FC<UniversalCanvasProps> = ({
    mode,
    grid,
    rooms,
    elevMap,
    moistMap,
    viewMode,
    tileSize = 8, 
    brushRadius,
    zoom,
    onPaint,
    onPaintEnd,
    onHover,
    onRightClick,
    onCenterRequest,
    centerPos,
    anchorX = 0,
    anchorY = 0
}) => {
    const { terrainRegistry } = useStore();
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const bufferRef = useRef<HTMLCanvasElement | null>(null);
    
    const [isPainting, setIsPainting] = useState(false);
    const [offset, setOffset] = useState({ x: 0, y: 0 });
    const [viewportZoom, setViewportZoom] = useState(zoom || 25);
    const [lastMouse, setLastMouse] = useState({ x: 0, y: 0 });
    const [isPanning, setIsPanning] = useState(false);

    // --- INITIALIZE BUFFER ---
    useEffect(() => {
        if (!bufferRef.current) {
            bufferRef.current = document.createElement("canvas");
            bufferRef.current.width = WIDTH * tileSize;
            bufferRef.current.height = HEIGHT * tileSize;
        }
    }, [tileSize]);

    // --- UPDATE BUFFER (Radiant Shaders) ---
    // [V11.16] Eliminates gaps and applies a brilliance boost to prevent darkening on zoom-out.
    useEffect(() => {
        const buffer = bufferRef.current;
        if (!buffer || !grid || !terrainRegistry) return;
        const bCtx = buffer.getContext("2d");
        if (!bCtx) return;

        bCtx.clearRect(0, 0, buffer.width, buffer.height);
        
        for (let y = 0; y < grid.length; y++) {
            for (let x = 0; x < grid[y].length; x++) {
                let color = "#111111";
                if (viewMode === "terrain") {
                    const terr = terrainRegistry?.terrains[grid[y][x]];
                    const baseHex = terr?.studio_hex || terr?.hex || "#444";
                    
                    // [V12.0] Vellum Shader: Elevation Tinting
                    const elev = elevMap ? (elevMap[y][x] || 0) : 0.5;
                    const brightness = 0.7 + (elev * 0.6); // 0.7 to 1.3
                    color = applyTint(baseHex, brightness);
                } else if (viewMode === "elev" && elevMap) {
                    const e = Math.floor(elevMap[y][x] * 255);
                    color = `rgb(${e}, ${e}, ${e})`;
                } else if (viewMode === "moist" && moistMap) {
                    const m = Math.floor(moistMap[y][x] * 255);
                    color = `rgb(0, 50, ${m})`; // Bluer moisture
                }
                
                bCtx.fillStyle = color;
                bCtx.fillRect(x * tileSize, y * tileSize, tileSize, tileSize);
                
                // [V12.0] Vellum Shader: Cell Shadowing
                bCtx.strokeStyle = "rgba(0,0,0,0.15)";
                bCtx.lineWidth = 1;
                bCtx.strokeRect(x * tileSize, y * tileSize, tileSize, tileSize);
            }
        }
    }, [grid, elevMap, moistMap, viewMode, terrainRegistry, tileSize]);

    // Utility: Sovereign Tint Engine
    const applyTint = (hex: string, factor: number) => {
        const r = parseInt(hex.slice(1, 3), 16);
        const g = parseInt(hex.slice(3, 5), 16);
        const b = parseInt(hex.slice(5, 7), 16);
        return `rgb(${Math.min(255, r * factor)}, ${Math.min(255, g * factor)}, ${Math.min(255, b * factor)})`;
    };

    // --- MAIN RENDER ---
    const draw = useCallback(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext("2d");
        if (!ctx) return;

        // Resize
        if (canvas.width !== canvas.parentElement?.clientWidth || canvas.height !== canvas.parentElement?.clientHeight) {
            canvas.width = canvas.parentElement?.clientWidth || 800;
            canvas.height = canvas.parentElement?.clientHeight || 600;
        }

        // Void Background
        ctx.fillStyle = "#05060f";
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // Grid Pattern (Subtle guidance)
        if (viewportZoom > 5) {
            ctx.strokeStyle = "rgba(255, 255, 255, 0.03)";
            ctx.lineWidth = 1;
            const step = viewportZoom * 5;
            for (let x = offset.x % step; x < canvas.width; x += step) {
                ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, canvas.height); ctx.stroke();
            }
            for (let y = offset.y % step; y < canvas.height; y += step) {
                ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(canvas.width, y); ctx.stroke();
            }
        }

        // --- LAYER 1: MIRROR MONITOR (World Rooms) ---
        if (rooms) {
            const gap = viewportZoom > 4 ? 1 : 0; 
            rooms.forEach(room => {
                const px = offset.x + room.x * viewportZoom;
                const py = offset.y + room.y * viewportZoom;
                if (px + viewportZoom < 0 || px > canvas.width || py + viewportZoom < 0 || py > canvas.height) return;

                const terr = terrainRegistry?.terrains[room.terrain];
                const baseHex = terr?.studio_hex || terr?.hex || "#1e293b";
                
                // [V12.0] Vellum Shader: Elevation Tinting (Direct Room Logic)
                const elevFactor = 0.7 + ((room.elevation || 0) + 5) / 10 * 0.6; // Scale -5/5 to 0.7/1.3
                const color = applyTint(baseHex, elevFactor);

                ctx.fillStyle = color;
                ctx.fillRect(px, py, viewportZoom - gap, viewportZoom - gap);
                
                // Tactical Border for Rooms
                if (viewportZoom > 6) {
                    ctx.strokeStyle = "rgba(0,0,0,0.2)";
                    ctx.strokeRect(px, py, viewportZoom - gap, viewportZoom - gap);
                }
            });
        }

        // --- LAYER 2: GENESIS ENGINE (The Shard) ---
        if (bufferRef.current && grid) {
            const sizeFactor = (viewportZoom / tileSize) * (tileSize);
            const anchorOffsetX = (anchorX || 0) * viewportZoom;
            const anchorOffsetY = (anchorY || 0) * viewportZoom;
            const drawX = offset.x + anchorOffsetX;
            const drawY = offset.y + anchorOffsetY;
            
            // Apply Smoothing logic
            ctx.imageSmoothingEnabled = (viewportZoom < 2); // Only smooth when tiny
            
            ctx.drawImage(
                bufferRef.current, 
                drawX, 
                drawY, 
                WIDTH * (viewportZoom), 
                HEIGHT * (viewportZoom)
            );

            // Shard Frame
            ctx.strokeStyle = "rgba(168, 85, 247, 0.6)";
            ctx.lineWidth = Math.max(1, viewportZoom / 10);
            ctx.strokeRect(drawX, drawY, WIDTH * viewportZoom, HEIGHT * viewportZoom);
        }
    }, [rooms, grid, offset, viewportZoom, terrainRegistry, anchorX, anchorY, tileSize]);

    useEffect(() => {
        let frame = requestAnimationFrame(function loop() {
            draw();
            frame = requestAnimationFrame(loop);
        });
        return () => cancelAnimationFrame(frame);
    }, [draw]);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        
        if (mode === 'sculpt' && offset.x === 0 && offset.y === 0) {
            const size = tileSize * (viewportZoom / 10);
            setOffset({
                x: (canvas.parentElement?.clientWidth || 800) / 2 - (WIDTH * size) / 2,
                y: (canvas.parentElement?.clientHeight || 600) / 2 - (HEIGHT * size) / 2
            });
        }
    }, [mode, centerPos]);

    const handleMouseDown = (e: React.MouseEvent) => {
        if (e.button === 1 || e.shiftKey) { setIsPanning(true); } 
        else {
            setIsPainting(true);
            const rect = canvasRef.current!.getBoundingClientRect();
            const gx = Math.floor((e.clientX - rect.left - offset.x) / viewportZoom);
            const gy = Math.floor((e.clientY - rect.top - offset.y) / viewportZoom);
            onPaint(gx, gy);
        }
        setLastMouse({ x: e.clientX, y: e.clientY });
    };

    const handleMouseMove = (e: React.MouseEvent) => {
        const rect = canvasRef.current!.getBoundingClientRect();
        const gx = Math.floor((e.clientX - rect.left - offset.x) / viewportZoom);
        const gy = Math.floor((e.clientY - rect.top - offset.y) / viewportZoom);
        onHover(gx, gy);

        if (isPanning) {
            setOffset(prev => ({ x: prev.x + (e.clientX - lastMouse.x), y: prev.y + (e.clientY - lastMouse.y) }));
        } else if (isPainting) {
            onPaint(gx, gy);
        }
        setLastMouse({ x: e.clientX, y: e.clientY });
    };

    return (
        <div className="absolute inset-0 bg-[#05060f] cursor-crosshair overflow-hidden">
            <canvas
                ref={canvasRef}
                onMouseDown={handleMouseDown}
                onMouseMove={handleMouseMove}
                onMouseUp={() => { setIsPainting(false); setIsPanning(false); onPaintEnd(); }}
                onWheel={(e) => {
                    const delta = e.deltaY > 0 ? 0.9 : 1.1;
                    // [V11.16] INFINITE ZOOM: Expanded range from 0.05 to 1000.
                    setViewportZoom(prev => Math.max(0.05, Math.min(1000, prev * delta)));
                }}
                onContextMenu={(e) => {
                    e.preventDefault();
                    const rect = canvasRef.current!.getBoundingClientRect();
                    const gx = Math.floor((e.clientX - rect.left - offset.x) / viewportZoom);
                    const gy = Math.floor((e.clientY - rect.top - offset.y) / viewportZoom);
                    if (e.shiftKey) {
                        onCenterRequest(gx, gy);
                    } else {
                        onRightClick(gx, gy);
                    }
                }}
                className="w-full h-full block"
            />
        </div>
    );
};
