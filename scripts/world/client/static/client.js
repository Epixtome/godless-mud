(function() {
    // --- State & DOM References ---
    let ws;
    let dragging = null;
    let startX, startY, winX, winY;
    let blessingsStore = [];
    let selectedTarget = null;
    let currentStatus = null;

    const output = document.getElementById('output');
    const outputContainer = document.getElementById('output-container');
    const input = document.getElementById('command-input');
    const mapDisplay = document.getElementById('map-display');
    const tacticalDisplay = document.getElementById('tactical-display');
    const hfTacticalDisplay = document.getElementById('hf-tactical-display');
    const roomHeader = document.getElementById('room-name-header');
    const blessingBar = document.getElementById('blessing-list');
    
    const hpFill = document.getElementById('hp-fill'), hpText = document.getElementById('hp-text');
    const spFill = document.getElementById('sp-fill'), spText = document.getElementById('sp-text');
    const balFill = document.getElementById('bal-fill'), balText = document.getElementById('bal-text');
    
    const classContainer = document.getElementById('class-bar-container');
    const classFill = document.getElementById('class-fill'), classText = document.getElementById('class-text'), classLabel = document.getElementById('class-label');

    const roomDesc = document.getElementById('room-description'), roomEntities = document.getElementById('room-entities');
    const timeIcon = document.getElementById('time-icon'), timeText = document.getElementById('time-text');
    const weatherIcon = document.getElementById('weather-icon'), weatherText = document.getElementById('weather-text');
    const locText = document.getElementById('location-text');

    // --- Window Management ---
    document.querySelectorAll('.window-header').forEach(header => {
        header.onmousedown = (e) => {
            if (header.parentElement.classList.contains('pinned')) return;
            dragging = header.parentElement;
            startX = e.clientX;
            startY = e.clientY;
            winX = dragging.offsetLeft;
            winY = dragging.offsetTop;
            dragging.style.zIndex = 1000;
            document.querySelectorAll('.window').forEach(w => { if (w !== dragging) w.style.zIndex = 10; });
        };
    });

    window.onmousemove = (e) => {
        if (!dragging) return;
        dragging.style.left = (winX + (e.clientX - startX)) + 'px';
        dragging.style.top = (winY + (e.clientY - startY)) + 'px';
    };

    window.onmouseup = () => { dragging = null; };

    // --- Communication ---
    function connect() {
        ws = new WebSocket('ws://localhost:8000/ws');

        ws.onopen = () => appendOutput('\n[SYSTEM] Protocol Stabilized. Secure Link Active.\n');

        ws.onmessage = (event) => {
            const raw = event.data.trim();
            if (!raw) return;

            // 1. Attempt GES Parse
            let eventObj = null;
            try {
                if (raw.startsWith('{')) eventObj = JSON.parse(raw);
            } catch (e) {
                console.error("GES Parse Error:", e, raw);
            }

            if (eventObj && eventObj.type) {
                try {
                    const payload = eventObj.data || {};
                    
                    if (eventObj.type === 'map_data') {
                        renderMap(payload.perception || payload, payload.context || eventObj.context);
                        return;
                    }
                    if (eventObj.type === 'status_update') {
                        updateStatus(payload);
                        return;
                    }
                    if (eventObj.type === 'log:message') {
                        appendOutput(eventObj.text || payload.text || "");
                        return;
                    }
                    if (eventObj.type === 'text') {
                        appendOutput(payload.text || payload || "");
                        return;
                    }
                    if (eventObj.type === 'combat_event') {
                        triggerDamagePopup(payload);
                        return;
                    }
                    if (eventObj.type === 'prompt') {
                        return;
                    }
                } catch (err) {
                    console.error("GES Execution Error:", err, eventObj);
                    // Fall through to raw output if processing failed
                }
            }

            // 2. Fallback to raw output
            appendOutput(raw);
        };

        ws.onclose = () => appendOutput('\n[SYSTEM] Connection severed.');
        ws.onerror = (e) => appendOutput('\n[SYSTEM] Critical WebSocket Error.');
    }

    function triggerDamagePopup(hit) {
        if (hit.type === 'damage') {
            // 1. Find the target in the Sensory Data shard
            const rows = Array.from(document.querySelectorAll('.entity-row'));
            const targetRow = rows.find(r => r.innerText.includes(hit.target_name));
            
            if (targetRow) {
                const popup = document.createElement('div');
                popup.className = 'damage-popup' + (hit.is_critical ? ' crit' : '');
                popup.innerText = `-${hit.value}`;
                targetRow.appendChild(popup);
                setTimeout(() => popup.remove(), 1200);
            }

            // 2. If it's the player being hit, flash the vitals window red
            if (hit.target_name === currentStatus?.name) {
                const vitals = document.getElementById('win-vitals');
                if (vitals) {
                    vitals.classList.add('flash-red');
                    setTimeout(() => vitals.classList.remove('flash-red'), 500);
                }
            }
        }
    }

    function updateStatus(status) {
        if (!status) return;
        currentStatus = status;

        if (status.is_admin && document.getElementById('win-dev')) {
            document.getElementById('win-dev').style.display = 'block';
        }
        
        if (hpFill) hpFill.style.width = (status.hp?.current / status.hp?.max * 100 || 0) + '%';
        if (hpText) hpText.innerText = `VITALITY: ${status.hp?.current || 0}/${status.hp?.max || 0}`;
        
        if (spFill) spFill.style.width = (status.stamina?.current / status.stamina?.max * 100 || 0) + '%';
        if (spText) spText.innerText = `STAMINA: ${status.stamina?.current || 0}/${status.stamina?.max || 0}`;

        if (balFill) balFill.style.width = (status.balance?.current / status.balance?.max * 100 || 0) + '%';
        if (balText) balText.innerText = `POSTURE: ${status.balance?.current || 0}/${status.balance?.max || 0}`;
        
        if (classContainer) {
            if (status.resource && status.resource.id !== 'balance') {
                classContainer.style.display = 'block';
                const label = status.resource.name || 'RESOURCE';
                if (classFill) classFill.style.width = (status.resource.current / status.resource.max * 100 || 0) + '%';
                if (classText) classText.innerText = `${label.toUpperCase()}: ${status.resource.current}/${status.resource.max}`;
                
                if (classFill) {
                    if (status.resource.id === 'fury') classFill.style.background = 'linear-gradient(90deg, #600, #f22)';
                    else if (status.resource.id === 'chi') classFill.style.background = 'linear-gradient(90deg, #650, #ff0)';
                    else classFill.style.background = 'linear-gradient(90deg, #166, #2ff)';
                }
            } else {
                classContainer.style.display = 'none';
            }
        }

        if (status.room) {
            if (locText) locText.innerText = status.room.name || 'Unknown Area';
            if (roomHeader) roomHeader.innerText = status.room.name || 'MINIMAP';
            if (roomDesc) roomDesc.innerText = status.room.description || '';
            if (roomEntities) {
                roomEntities.innerHTML = '';
                if (status.room.entities && status.room.entities.length > 0) {
                    status.room.entities.forEach(ent => {
                        const row = document.createElement('div');
                        row.className = 'entity-row' + (selectedTarget === ent.name ? ' selected' : '');
                        row.style.fontSize = '0.85em';
                        row.style.padding = '4px 8px';
                        row.style.borderBottom = '1px solid #222';
                        row.style.cursor = 'pointer';
                        row.style.transition = 'background 0.2s';
                        if (selectedTarget === ent.name) row.style.background = '#331';

                        row.onclick = () => {
                            selectedTarget = (selectedTarget === ent.id) ? null : ent.id;
                            updateStatus(status); 
                        };

                        const color = ent.is_player ? '#55f' : (ent.is_hostile ? '#f55' : '#ff5');
                        row.innerHTML = `<span style="color:${color}; font-weight:bold;">${ent.symbol}</span> <span style="color:#ddd;">${ent.name}</span>`;
                        roomEntities.appendChild(row);
                    });
                } else {
                    roomEntities.innerHTML = '<div style="font-size:0.7em; color:#444; padding:5px;">No Entities Detected.</div>';
                    selectedTarget = null;
                }
            }
        }
        
        // --- Combat Status Sync (Bug 6) ---
        const targetContainer = document.getElementById('combat-target-container');
        const targetName = document.getElementById('target-name');
        const targetHpFill = document.getElementById('target-hp-fill');
        const effectsList = document.getElementById('status-effects-list');

        if (status.target) {
            if (targetContainer) targetContainer.style.display = 'block';
            if (targetName) targetName.innerText = status.target.name.toUpperCase();
            if (targetHpFill) targetHpFill.style.width = (status.target.hp.current / status.target.hp.max * 100) + '%';
        } else if (targetContainer) {
            targetContainer.style.display = 'none';
        }

        if (effectsList) {
            effectsList.innerHTML = '';
            if (status.status_effects && status.status_effects.length > 0) {
                status.status_effects.forEach(eff => {
                    const badge = document.createElement('div');
                    badge.style.background = '#322';
                    badge.style.border = '1px solid #722';
                    badge.style.color = '#f55';
                    badge.style.fontSize = '0.6em';
                    badge.style.padding = '2px 6px';
                    badge.style.borderRadius = '2px';
                    badge.style.fontWeight = 'bold';
                    badge.innerText = `${eff.name} (${eff.duration}s)`;
                    effectsList.appendChild(badge);
                });
            } else {
                effectsList.innerHTML = '<div style="font-size:0.7em; color:#444;">No active afflictions.</div>';
            }
        }
        
        if (timeText) timeText.innerText = status.time || 'Unknown';
        if (timeIcon) {
            timeIcon.innerText = status.is_day ? '☀️' : '🌙';
            if (status.time === "Morning") timeIcon.innerText = '🌅';
            if (status.time === "Evening") timeIcon.innerText = '🌆';
        }

        if (weatherText) weatherText.innerText = (status.weather || 'clear').replace('_', ' ').toUpperCase();
        if (weatherIcon) {
            const wTable = { 'clear': '☀️', 'cloudy': '☁️', 'rainy': '🌧️', 'thunderstorm': '🌩️' };
            weatherIcon.innerText = wTable[status.weather] || '☁️';
        }

        if (status.blessings && blessingBar) {
            const bSetChanged = JSON.stringify(status.blessings) !== JSON.stringify(blessingsStore);
            if (bSetChanged || blessingBar.children.length === 0) {
                renderBlessingBar(status.blessings);
            }
        }
    }

    function sendCommand(cmdOverride) {
        let cmd = cmdOverride || input.value;
        const isSkill = cmdOverride && !cmd.includes(' ') && !cmd.startsWith('@');
        
        if (isSkill) {
            if (selectedTarget) {
                // Find name from selection ID
                const ent = currentStatus?.room?.entities?.find(e => e.id === selectedTarget);
                if (ent) cmd += ' ' + ent.name;
            } else if (currentStatus?.room?.entities) {
                const firstMob = currentStatus.room.entities.find(ent => !ent.is_player);
                if (firstMob) cmd += ' ' + firstMob.name;
            }
        }

        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(cmd + '\n');
        }
        input.select();
    }
    window.sendCommand = sendCommand;

    function renderBlessingBar(blessings) {
        blessingsStore = blessings;
        blessingBar.innerHTML = '';
        if (!blessings || blessings.length === 0) {
            blessingBar.innerHTML = '<div style="font-size:0.7em; color:#555; padding:10px;">No Blessings Equipped</div>';
            return;
        }
        blessings.slice(0, 9).forEach((b, i) => {
            const btn = document.createElement('div');
            btn.className = 'blessing-btn';
            
            // [Bug 59] Setup/Payoff Logic
            const isSetup = b.tags?.includes('setup') || b.type === 'setup';
            const isPayoff = b.tags?.includes('payoff') || b.type === 'finisher';
            const role = isSetup ? 'SETUP' : (isPayoff ? 'PAYOFF' : 'UTIL');
            const roleColor = isSetup ? '#5af' : (isPayoff ? '#f5a' : '#aaa');

            // Dimming logic if unusable (e.g. no resources - future enhancement)
            // For now, let's just style by role.
            btn.style.borderLeft = `3px solid ${roleColor}`;
            
            btn.innerHTML = `
                <span class="role" style="font-size:0.5em; color:${roleColor}; position:absolute; top:2px; left:5px;">${role}</span>
                <span class="name">${b.name.toUpperCase()}</span>
                <span class="key-hint" style="font-size:0.6em; color:#666;">[${i+1}]</span>
            `;
            btn.onclick = () => sendCommand(b.id);
            blessingBar.appendChild(btn);
        });
    }

    function renderMap(mapData, context) {
        if (!mapData || !mapData.grid) return;
        const target = (context === 'map') ? tacticalDisplay : mapDisplay;
        if (!target) return;

        // --- Standard Map Rendering ---
        let html = '';
        mapData.grid.forEach(row => {
            row.forEach(tile => {
                let char = tile.char || '?';
                let style = `color:${tile.color || '#555'};`;
                if (tile.top_entity) {
                    char = tile.top_entity.symbol;
                    style = `color:${tile.top_entity.color};font-weight:bold;`;
                } else if (tile.x === 0 && tile.y === 0) {
                    char = '@'; style = 'color:white;font-weight:bold;';
                }
                if (!tile.visible) { char = ' '; style = 'color:black;'; }
                html += `<span class="map-tile" style="${style}">${char}</span>`;
            });
            html += '<br>';
        });
        target.innerHTML = html;

        // --- High-Fidelity Spatial Rendering ---
        if (context === 'map' && hfTacticalDisplay) {
            hfTacticalDisplay.style.gridTemplateColumns = `repeat(${mapData.grid[0].length}, 24px)`;
            hfTacticalDisplay.innerHTML = ''; // Clear for redraw
            
            mapData.grid.forEach(row => {
                row.forEach(tile => {
                    const el = document.createElement('div');
                    el.className = 'premium-tile';
                    
                    if (tile.visible || tile.visited) {
                        const elev = tile.elevation || 0;
                        const lift = elev * -4;
                        const shadowBlur = elev * 2;
                        const shadow = elev > 0 ? `0 ${elev + 2}px ${shadowBlur}px rgba(0,0,0,0.6)` : 'none';
                        
                        el.style.transform = `translateY(${lift}px) scale(${1 + (elev * 0.02)})`;
                        el.style.boxShadow = shadow;
                        el.style.opacity = tile.visible ? 1 : 0.6;
                        if (!tile.visible) el.style.filter = 'grayscale(80%) brightness(0.7)';
                        el.style.background = tile.visible ? 'rgba(255,255,255,0.1)' : 'rgba(255,255,255,0.05)';

                        const terrain = document.createElement('span');
                        terrain.className = 'terrain-symbol';
                        terrain.style.color = tile.color;
                        terrain.innerText = tile.char;
                        el.appendChild(terrain);

                        if (tile.top_entity && tile.visible) {
                            const ent = document.createElement('span');
                            ent.className = 'entity-symbol';
                            ent.style.color = tile.top_entity.color;
                            ent.innerText = tile.top_entity.symbol;
                            el.appendChild(ent);
                        } else if (tile.has_pings && tile.visible) {
                            const ping = document.createElement('div');
                            ping.className = 'ping-pulse';
                            el.appendChild(ping);
                        }
                    } else {
                        el.style.opacity = 0;
                    }

                    hfTacticalDisplay.appendChild(el);
                });
            });
        }
    }

    function appendOutput(text) {
        if (!text) return;
        const colorMap = {
            '0': '#bbbbbb', '31': '#ff5555', '32': '#55ff55', '33': '#ffff55',
            '34': '#5555ff', '35': '#ff55ff', '36': '#55ffff', '37': '#bbbbbb',
            '90': '#555555', '91': '#ff5555', '92': '#55ff55', '93': '#ffff55', '94': '#5555ff'
        };
        const segments = text.split(/\x1b\[/);
        let finalHtml = '';
        let sty = { color: '#bbb', bold: false };

        segments.forEach((seg, i) => {
            if (i === 0) { finalHtml += renderSegment(seg, sty); return; }
            const match = seg.match(/^([0-9;]*)m([\s\S]*)$/);
            if (!match) { finalHtml += seg; return; }
            match[1].split(';').forEach(code => {
                const c = parseInt(code);
                if (c === 0) { sty.color = '#bbb'; sty.bold = false; }
                else if (c === 1) sty.bold = true;
                else if (colorMap[code]) sty.color = colorMap[code];
            });
            finalHtml += renderSegment(match[2], sty);
        });

        function renderSegment(str, s) {
            let clean = str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
            return `<span style="color:${s.color};${s.bold ? 'font-weight:bold;' : ''}">${clean}</span>`;
        }

        const div = document.createElement('div');
        div.style.lineHeight = '1.1';
        div.innerHTML = finalHtml;
        output.appendChild(div);
        outputContainer.scrollTop = outputContainer.scrollHeight;
    }

    input.onkeypress = (e) => { if (e.key === 'Enter') sendCommand(); };
    window.onkeydown = (e) => {
        if (document.activeElement === input) return;
        const key = parseInt(e.key);
        if (key >= 1 && key <= 9 && blessingsStore[key - 1]) sendCommand(blessingsStore[key - 1].id);
    };

    connect();
})();
