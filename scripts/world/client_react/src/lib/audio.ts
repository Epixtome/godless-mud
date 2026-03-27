/** [V9.3 GODLESS SPATIAL AUDIO ENGINE] */
import { useStore } from '../store/useStore';

class AudioService {
    private context: AudioContext | null = null;
    private masterGain: GainNode | null = null;
    private panner: PannerNode | null = null;
    private buffers: Record<string, AudioBuffer> = {};
    private lastPlayTime: Record<string, number> = {};

    private SOUND_MAP: Record<string, string> = {
        'footstep': 'https://assets.mixkit.co/active_storage/sfx/2092/2092-preview.mp3',
        'clash': 'https://assets.mixkit.co/active_storage/sfx/1116/1116-preview.mp3', // Thuddier Impact
        'blessing': 'https://assets.mixkit.co/active_storage/sfx/2005/2005-preview.mp3',
        'error': 'https://assets.mixkit.co/active_storage/sfx/2571/2571-preview.mp3'
    };

    constructor() {}

    private init() {
        if (this.context) return;
        this.context = new (window.AudioContext || (window as any).webkitAudioContext)();
        this.masterGain = this.context.createGain();
        this.masterGain.gain.value = 0.8; // Master Volume 80%
        this.masterGain.connect(this.context.destination);
        
        Object.entries(this.SOUND_MAP).forEach(([id, url]) => this.loadBuffer(id, url));
    }

    private async loadBuffer(id: string, url: string) {
        try {
            const response = await fetch(url);
            const arrayBuffer = await response.arrayBuffer();
            if (this.context) {
                const audioBuffer = await this.context.decodeAudioData(arrayBuffer);
                this.buffers[id] = audioBuffer;
            }
        } catch (e) {
            console.error(`Failed to load sound: ${id}`, e);
        }
    }

    public playSpatial(id: string, relX: number = 0, relY: number = 0, intensity: number = 1.0) {
        this.init();
        if (!this.context || !this.buffers[id] || this.context.state !== 'running') {
            if (this.context?.state === 'suspended') this.context.resume();
            return;
        }

        // --- DEBOUNCE (V9.4) ---
        const now = Date.now();
        if (id === 'clash' && this.lastPlayTime[id] && now - this.lastPlayTime[id] < 150) {
            return; // Too frequent (Aggressive stacking prevention)
        }
        this.lastPlayTime[id] = now;

        const source = this.context.createBufferSource();
        source.buffer = this.buffers[id];

        // 3D Panner Node Logic
        const panner = this.context.createPanner();
        panner.panningModel = 'HRTF';
        panner.distanceModel = 'exponential';
        const spatialScale = 2.0;
        panner.setPosition(relX * spatialScale, 0, relY * spatialScale);

        // --- FILTER (V9.4: Cut the 'bell ring') ---
        const filter = this.context.createBiquadFilter();
        filter.type = 'lowpass';
        filter.frequency.setValueAtTime(id === 'clash' ? 2500 : 8000, this.context.currentTime);

        const gain = this.context.createGain();
        gain.gain.value = Math.min(1.2, intensity * 1.5); // Boosted volume

        // Routing: Source -> Filter -> Panner -> Gain -> Master
        source.connect(filter);
        filter.connect(panner);
        panner.connect(gain);
        gain.connect(this.masterGain!);

        source.start(0);
        // Force stop long lingering sounds (prevent drone effect)
        if (id === 'clash') {
            source.stop(this.context.currentTime + 0.5);
        }
    }

    public playGlobal(id: string, intensity: number = 1.0) {
        this.playSpatial(id, 0, 0, intensity);
    }
}

export const audioService = new AudioService();
