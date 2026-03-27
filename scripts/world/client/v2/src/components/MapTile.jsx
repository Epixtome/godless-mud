import React, { useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

/**
 * ElevationAwareTile
 * Implements Topographic Depth Shading & The Ridge Rule visually.
 */
const MapTile = ({ tile, observerElevation = 0 }) => {
  if (!tile) return <div className="map-tile-empty" style={{ width: 24, height: 24 }} />;

  const { 
    char, 
    color, 
    visible, 
    visited, 
    elevation, 
    top_entity, 
    has_pings 
  } = tile;

  // Calculate "Lift" (Z-Axis displacement)
  const lift = useMemo(() => elevation * -4, [elevation]);
  
  // Calculate Shadow Depth: Higher elevation = softer, longer shadow
  const shadowDepth = useMemo(() => {
    if (elevation <= 0 || !visible) return 'none';
    const blur = elevation * 2;
    const spread = elevation * 0.5;
    return `0px ${elevation + 2}px ${blur}px ${spread}px rgba(0,0,0,0.6)`;
  }, [elevation, visible]);

  // Handle Fog of War & Memory (Visited but not visible)
  const baseStyle = {
    color: visible ? color : (visited ? '#444' : 'transparent'),
    transformStyle: 'preserve-3d',
  };

  return (
    <motion.div
      className={`map-tile ${visible ? 'visible' : ''} ${visited ? 'visited' : ''}`}
      initial={false}
      animate={{
        y: lift,
        scale: visible ? 1 + (elevation * 0.02) : 1,
        boxShadow: shadowDepth,
        filter: visible ? 'none' : (visited ? 'grayscale(100%) blur(0.5px)' : 'none'),
        opacity: visible ? 1 : (visited ? 0.4 : 0)
      }}
      transition={{ type: 'spring', stiffness: 200, damping: 25 }}
      style={{
        width: '24px',
        height: '24px',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        fontSize: '18px',
        position: 'relative',
        backgroundColor: visible ? 'rgba(255,255,255,0.03)' : 'transparent',
        borderRadius: '2px',
        cursor: 'pointer',
        ...baseStyle
      }}
      whileHover={{ scale: visible ? 1.2 : 1, zIndex: 100 }}
    >
      {/* Terrain Symbol */}
      <span className="terrain-symbol" style={{ zIndex: 1, fontFamily: 'monospace' }}>
        {visible || visited ? char : ''}
      </span>

      {/* Dynamic Entity Rendering (Framer Motion entry/exit) */}
      <AnimatePresence>
        {top_entity && visible && (
          <motion.span
            key={top_entity.name}
            initial={{ opacity: 0, scale: 0.2, y: 5 }}
            animate={{ opacity: 1, scale: 1.2, y: -2 }}
            exit={{ opacity: 0, scale: 0.2 }}
            style={{
              position: 'absolute',
              zIndex: 10,
              color: top_entity.color,
              fontWeight: 'bold',
              textShadow: '0 0 4px rgba(0,0,0,0.9)',
              fontFamily: 'monospace'
            }}
          >
            {top_entity.symbol}
          </motion.span>
        )}
      </AnimatePresence>

      {/* Sensory Pings (Intelligence Pulse for Unseen Entities) */}
      {has_pings && !top_entity && visible && (
        <motion.div
          animate={{ 
            scale: [1, 1.8, 1], 
            opacity: [0.3, 0.7, 0.3],
            boxShadow: ['0 0 2px #ff5', '0 0 10px #ff5', '0 0 2px #ff5']
          }}
          transition={{ repeat: Infinity, duration: 2 }}
          style={{
            position: 'absolute',
            width: '6px',
            height: '6px',
            borderRadius: '50%',
            backgroundColor: '#ffff55',
            zIndex: 5
          }}
        />
      )}
    </motion.div>
  );
};

export default MapTile;
