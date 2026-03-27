import React, { useMemo, useEffect, useRef } from 'react';
import { motion, useAnimation } from 'framer-motion';
import MapTile from './MapTile';

/**
 * MapGrid
 * Renders a grid of ElevationAwareTiles with transition tweening.
 */
const MapGrid = ({ grid, center, onTileClick }) => {
  const controls = useAnimation();
  const prevCenterRef = useRef(center);

  // Animating Grid Slide when center shifts
  useEffect(() => {
    if (!prevCenterRef.current || !center) return;
    
    // Calculate displacement
    const dx = prevCenterRef.current.x - center.x;
    const dy = prevCenterRef.current.y - center.y;
    
    if (dx !== 0 || dy !== 0) {
      // Offset grid by -1 tile in the direction of movement
      // Then tween back to center 0,0
      controls.set({ x: dx * 24, y: -dy * 24 });
      controls.start({ 
        x: 0, 
        y: 0, 
        transition: { type: 'spring', stiffness: 200, damping: 25 } 
      });
    }
    
    prevCenterRef.current = center;
  }, [center, controls]);

  if (!grid || grid.length === 0) return (
    <div className="map-grid-loading">Awaiting Spatial Sync...</div>
  );

  return (
    <div className="map-viewport" style={{ 
      overflow: 'hidden', 
      width: 'fit-content', 
      backgroundColor: '#050505',
      border: '1px solid #222',
      borderRadius: '4px',
      padding: '4px',
      userSelect: 'none'
    }}>
      <motion.div
        className="map-grid-container"
        animate={controls}
        style={{
          display: 'grid',
          gridTemplateColumns: `repeat(${grid[0].length}, 24px)`,
          gap: '2px'
        }}
      >
        {grid.map((row, y) => (
          <React.Fragment key={`row-${y}`}>
            {row.map((tile, x) => (
              <div 
                key={`tile-${tile.x}-${tile.y}`}
                onClick={() => onTileClick && onTileClick(tile)}
              >
                <MapTile tile={tile} />
              </div>
            ))}
          </React.Fragment>
        ))}
      </motion.div>
    </div>
  );
};

export default MapGrid;
