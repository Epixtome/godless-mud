/** [V9.2 UNIFIED SOCKET] */
let socket: WebSocket | null = null;

export const setSocket = (s: WebSocket | null) => {
    socket = s;
};

export const getSocket = () => socket;

export const sendEvent = (type: string, data: any = {}) => {
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ type, timestamp: Date.now() / 1000, data }));
    }
};

export const sendRaw = (cmd: string) => {
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(cmd);
    }
};
