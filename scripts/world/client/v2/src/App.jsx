import React, { useState, useEffect, useRef, useCallback } from 'react';
import MapGrid from './components/MapGrid';
import { motion, AnimatePresence } from 'framer-motion';

// --- Godless Theme Constants ---
const COLORS = {
  bg: '#0a0a0c',
  panel: '#121216',
  accent: '#5555ff',
  danger: '#ff5555',
  warning: '#ffff55',
  success: '#55ff55',
  text: '#ddd',
  dimText: '#666',
};

const App = () => {
  const [mapData, setMapData] = useState({ grid: [], center: { x: 0, y: 0, z: 0 } });
  const [status, setStatus] = useState(null);
  const [output, setOutput] = useState([]);
  const [command, setCommand] = useState('');
  const [ws, setWs] = useState(null);
  
  const outputRef = useRef(null);

  // --- WebSocket Connection ---
  useEffect(() => {
    const socket = new WebSocket('ws://localhost:8889');
    
    socket.onopen = () => {
      appendOutput('[SYSTEM] Link Established. High-Fidelity Client Active.', COLORS.accent);
      setWs(socket);
    };

    socket.onmessage = (event) => {
      let msg = event.data.trim();
      if (msg.startsWith('{')) {
        try {
          const data = JSON.parse(msg);
          if (data.type === 'map_data') setMapData(data.data);
          else if (data.type === 'status_update') setStatus(data.data);
          else if (data.type === 'text') appendOutput(data.data);
        } catch (e) {
          console.error("Parse Error:", e);
        }
      } else {
        appendOutput(msg);
      }
    };

    socket.onclose = () => {
      appendOutput('[SYSTEM] Connection Severed. Switching to Manual Overrides.', COLORS.danger);
      setWs(null);
    };

    return () => socket.close();
  }, []);

  // --- Auto-scroll Console ---
  useEffect(() => {
    if (outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight;
    }
  }, [output]);

  const appendOutput = (text, color = COLORS.text) => {
    setOutput(prev => [...prev.slice(-200), { text, color, id: Date.now() }]);
  };

  const sendCommand = useCallback((cmd) => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send((cmd || command) + '\n');
      setCommand('');
    }
  }, [ws, command]);

  const handleTileClick = (tile) => {
    // Simple direct move logic for the demo
    // If adjacent, move. If far, send absolute move (if supported)
    if (tile.x === 0 && tile.y === -1) sendCommand('north');
    else if (tile.x === 0 && tile.y === 1) sendCommand('south');
    else if (tile.x === 1 && tile.y === 0) sendCommand('east');
    else if (tile.x === -1 && tile.y === 0) sendCommand('west');
    else appendOutput(`Targeting [${tile.x}, ${tile.y}] elevation ${tile.elevation}`, COLORS.dimText);
  };

  const currentRoom = status?.room || {};
  const exits = currentRoom.exits || {};

  return (
    <div style={{ 
      backgroundColor: COLORS.bg, 
      color: COLORS.text, 
      height: '100vh', 
      display: 'grid',
      gridTemplateColumns: 'minmax(300px, 1fr) 400px',
      gridTemplateRows: '1fr auto 120px',
      padding: '4px',
      gap: '4px',
      fontFamily: '"Outfit", "Inter", sans-serif'
    }}>
      {/* Left: Tactical Map Viewport */}
      <div style={{ 
        gridArea: '1 / 1 / 3 / 2', 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center',
        background: `radial-gradient(circle at center, #15151a 0%, #050508 100%)`,
        border: '1px solid #222',
        borderRadius: '8px',
        position: 'relative',
        overflow: 'hidden'
      }}>
        <div style={{ position: 'absolute', top: '10px', left: '10px', fontSize: '0.8em', color: COLORS.dimText }}>
          {currentRoom.name?.toUpperCase() || 'SPATIAL VOID'} 
          <span style={{ marginLeft: '10px', color: COLORS.accent }}>[Z:{currentRoom.z}]</span>
        </div>

        {/* Z-Axis Plane Peek (The "3D Ghosting" Effect) */}
        <AnimatePresence>
          {(exits.up || exits.down) && (
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 0.1 }}
              exit={{ opacity: 0 }}
              style={{
                position: 'absolute',
                width: '100%',
                height: '100%',
                pointerEvents: 'none',
                background: 'repeating-linear-gradient(45deg, #001 0px, #001 10px, #002 10px, #002 20px)',
                zIndex: 0
              }}
            />
          )}
        </AnimatePresence>

        <MapGrid grid={mapData.grid} center={mapData.center} onTileClick={handleTileClick} />
        
        {/* Dynamic Compass / Tactical HUD */}
        <div style={{
          position: 'absolute',
          bottom: '20px',
          right: '20px',
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 40px)',
          gridTemplateRows: 'repeat(3, 40px)',
          gap: '5px'
        }}>
          <CompassBtn dir="north" active={!!exits.north} onClick={() => sendCommand('north')} label="N" />
          <CompassBtn dir="west" active={!!exits.west} onClick={() => sendCommand('west')} label="W" />
          <CompassBtn dir="east" active={!!exits.east} onClick={() => sendCommand('east')} label="E" />
          <CompassBtn dir="south" active={!!exits.south} onClick={() => sendCommand('south')} label="S" />
          <div style={{ gridArea: '2 / 2' }} /> {/* Center */}
          <div style={{ gridArea: '1 / 3' }}><CompassBtn dir="up" active={!!exits.up} onClick={() => sendCommand('up')} label="▲" /></div>
          <div style={{ gridArea: '3 / 3' }}><CompassBtn dir="down" active={!!exits.down} onClick={() => sendCommand('down')} label="▼" /></div>
        </div>
      </div>

      {/* Right: Console Log */}
      <div style={{ 
        gridArea: '1 / 2 / 2 / 3', 
        backgroundColor: COLORS.panel, 
        border: '1px solid #333',
        borderRadius: '8px',
        padding: '10px',
        overflowY: 'auto',
        display: 'flex',
        flexDirection: 'column'
      }} ref={outputRef}>
        {output.map(line => (
          <div key={line.id} style={{ color: line.color, marginBottom: '2px', fontSize: '0.9em', lineHeight: '1.2' }}>
            {line.text}
          </div>
        ))}
      </div>

      {/* Bottom Right: Sensory Intelligence */}
      <div style={{ 
        gridArea: '2 / 2 / 3 / 3', 
        backgroundColor: COLORS.panel, 
        border: '1px solid #333',
        borderRadius: '8px',
        margin: '4px 0',
        padding: '10px'
      }}>
        <div style={{ fontSize: '0.7em', color: COLORS.accent, fontWeight: 'bold', marginBottom: '8px' }}>SENSORY DATA</div>
        <div style={{ fontSize: '0.85em', color: '#888', fontStyle: 'italic', marginBottom: '8px' }}>
          {currentRoom.description}
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '5px' }}>
          {currentRoom.entities?.map(ent => (
            <div key={ent.name} style={{ 
              fontSize: '0.75em', 
              padding: '2px 8px', 
              borderRadius: '10px', 
              border: `1px solid ${ent.is_player ? COLORS.accent : COLORS.danger}`,
              color: ent.color
            }}>
              {ent.symbol} {ent.name}
            </div>
          ))}
        </div>
      </div>

      {/* Bottom: Vitals & Command Interface */}
      <div style={{ 
        gridArea: '3 / 1 / 4 / 3', 
        display: 'grid', 
        gridTemplateColumns: 'minmax(400px, 1fr) 300px',
        gap: '10px',
        alignItems: 'center',
        padding: '10px',
        backgroundColor: '#0c0c10',
        borderTop: '2px solid #222'
      }}>
        {/* Vitals */}
        <div style={{ display: 'flex', gap: '20px' }}>
          <VitalBar label="HP" color={COLORS.danger} val={status?.hp?.current} max={status?.hp?.max} />
          <VitalBar label="SP" color={COLORS.success} val={status?.stamina?.current} max={status?.stamina?.max} />
          <VitalBar label="BAL" color={COLORS.warning} val={status?.balance?.current} max={status?.balance?.max} />
          {status?.resource && (
            <VitalBar label={status.resource.id.toUpperCase()} color={COLORS.accent} val={status.resource.current} max={status.resource.max} />
          )}
        </div>

        {/* Command Input */}
        <div style={{ position: 'relative' }}>
          <input 
            type="text" 
            value={command}
            onChange={(e) => setCommand(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && sendCommand()}
            placeholder="Command the Aether..."
            style={{
              width: '100%',
              backgroundColor: '#1a1a20',
              border: '1px solid #444',
              borderRadius: '4px',
              padding: '10px 15px',
              color: 'white',
              fontSize: '1em',
              outline: 'none'
            }}
          />
          <div style={{ position: 'absolute', right: '10px', top: '50%', transform: 'translateY(-50%)', fontSize: '0.6em', color: '#444' }}>
            ENTER TO COMMIT
          </div>
        </div>
      </div>
    </div>
  );
};

const CompassBtn = ({ active, dir, label, onClick }) => (
  <motion.button
    whileHover={{ scale: 1.1 }}
    whileTap={{ scale: 0.9 }}
    onClick={onClick}
    disabled={!active}
    style={{
      backgroundColor: active ? '#1a1a24' : '#050510',
      border: `1px solid ${active ? '#334' : '#112'}`,
      color: active ? 'white' : '#223',
      borderRadius: '4px',
      cursor: active ? 'pointer' : 'not-allowed',
      fontWeight: 'bold',
      fontSize: '0.8em',
      gridArea: dir === 'north' ? '1 / 2' : (dir === 'south' ? '3 / 2' : (dir === 'west' ? '2 / 1' : (dir === 'east' ? '2 / 3' : '')))
    }}
  >
    {label}
  </motion.button>
);

const VitalBar = ({ label, color, val, max }) => {
  const pct = max ? (val / max) * 100 : 0;
  return (
    <div style={{ flex: 1, minWidth: '100px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.65em', color: '#888', marginBottom: '2px' }}>
        <span>{label}</span>
        <span>{val}/{max}</span>
      </div>
      <div style={{ height: '8px', backgroundColor: '#111', borderRadius: '4px', overflow: 'hidden' }}>
        <motion.div 
          animate={{ width: `${pct}%`, backgroundColor: color }}
          transition={{ type: 'spring', bounce: 0 }}
          style={{ height: '100%', boxShadow: `0 0 10px ${color}44` }} 
        />
      </div>
    </div>
  );
};

export default App;
