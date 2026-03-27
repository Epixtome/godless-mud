import { sendEvent } from './socket';
import { useStore } from '../store/useStore';

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
                case 'status_update':
                    store.setStatus(data);
                    break;
                case 'map_data':
                    if (data.context === 'map' || data.context === 'look') {
                        store.setTacticalMapData(data.perception);
                    }
                    break;
                case 'log:message':
                    store.addLog(data.text);
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
