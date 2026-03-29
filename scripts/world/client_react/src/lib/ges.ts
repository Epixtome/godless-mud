import { sendEvent } from './socket';
import { useStore } from '../store/useStore';
import { audioService } from './audio';

let reconnectTimeout: any = null;

export const connectToGES = (url?: string) => {
    if (!url) {
        const isDev = window.location.port === '3000' || window.location.port === '3001';
        const host = isDev ? 'localhost:8000' : window.location.host;
        url = `ws://${host}/ws`;
    }
    const store = useStore.getState();
    const ws = new WebSocket(url);

    ws.onopen = () => {
        console.log("Connected to GES");
        store.setConnected(true);
        if (reconnectTimeout) clearTimeout(reconnectTimeout);
        // Register the socket globally for sending
        import('./socket').then(m => m.setSocket(ws));
    };

    ws.onmessage = (event) => {
        try {
            const frame = JSON.parse(event.data);
            const { type, data } = frame;

            switch (type) {
                case 'admin:catalog':
                    store.setAdminCatalog(data);
                    break;
                case 'status_update':
                    store.setStatus(data);
                    break;
                case 'map_data':
                    if (data.context === 'map' || data.context === 'look') {
                        store.setTacticalMapData(data.perception);
                    }
                    break;
                case 'combat_event':
                    // Trigger visual floating text
                    store.addCombatNotification(data);
                    break;
                case 'audio:event':
                    audioService.playSpatial(data.id, data.rel_x, data.rel_y, data.intensity);
                    break;
                case 'log:message':
                    store.addLog(data.text);
                    break;
                case 'auth:require_name':
                    store.setLoggedByServer(false);
                    break;
                case 'auth:require_password':
                    // Server is ready for password
                    window.dispatchEvent(new CustomEvent('godless:auth_step', { detail: 'password' }));
                    break;
                case 'auth:success':
                    store.setLoggedByServer(true);
                    store.setAdminStatus(data.isAdmin);
                    if (data.name) store.saveCharacter(data.name);
                    break;
                case 'error':
                    console.error("GES Error:", data.message);
                    break;
                default:
                    console.warn("Unhandled GES type:", type);
            }
        } catch (e) {
            store.addLog(event.data);
        }
    };

    ws.onclose = () => {
        console.log("Disconnected from GES");
        store.setConnected(false);
        import('./socket').then(m => m.setSocket(null));
        reconnectTimeout = setTimeout(() => connectToGES(url), 3000);
    };

    ws.onerror = (err) => {
        console.error("GES Socket Error:", err);
    };
};

export const sendCommand = (cmd: string) => {
    // Legacy support
    import('./socket').then(m => m.sendRaw(cmd));
};

export const dispatchAbility = (ability: any) => {
    if (!ability || !ability.ready) return;
    
    const store = useStore.getState();
    const status = store.status;
    
    let targetStr = "";
    if (ability.type === 'damage') {
        // If no target, find first mob in room
        if (!status?.target) {
            const firstMob = status?.room?.entities?.find((e: any) => !e.is_player);
            if (firstMob) {
                targetStr = ` ${firstMob.name}`;
            }
        }
    } else if (ability.type === 'defense') {
        // Non-offensive defaults to self (e.g. heal, shielding)
        targetStr = " self";
    }

    sendCommand(`cast ${ability.id}${targetStr}`);
};

