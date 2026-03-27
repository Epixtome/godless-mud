import React, { useState, useEffect } from 'react';
import { useStore } from '../store/useStore';
import { sendRaw } from '../lib/socket';
import { Shield, User, LogIn, Trash2, Ghost, Clock } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import clsx from 'clsx';

const LoginOverlay: React.FC = () => {
    const { isConnected, isLoggedByServer, savedCharacters, removeCharacter } = useStore();
    const [name, setName] = useState('');
    const [password, setPassword] = useState('');
    const [step, setStep] = useState<'name' | 'password'>('name');
    const [isLoading, setIsLoading] = useState(false);

    useEffect(() => {
        const handleAuthStep = (e: any) => {
            if (e.detail === 'password') {
                setStep('password');
                setIsLoading(false);
            }
        };
        window.addEventListener('godless:auth_step', handleAuthStep);
        return () => window.removeEventListener('godless:auth_step', handleAuthStep);
    }, []);

    // Hide if logged in
    if (isLoggedByServer) return null;

    const handleLogin = (e?: React.FormEvent) => {
        if (e) e.preventDefault();
        if (!name) return;
        
        setIsLoading(true);
        sendRaw(name);
        // Step transition now handled by GES 'auth:require_password'
    };

    const handlePassword = (e: React.FormEvent) => {
        e.preventDefault();
        if (!password) return;
        
        setIsLoading(true);
        sendRaw(password);
        // We don't clear loading here; GES will clear the overlay on success
    };

    const selectSaved = (charName: string) => {
        setName(charName);
        sendRaw(charName);
        // Transition handled by GES event
    };

    return (
        <AnimatePresence>
            {!isLoggedByServer && (
                <motion.div 
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="fixed inset-0 z-[200] bg-black/90 backdrop-blur-md flex items-center justify-center p-4 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-slate-900/40 via-black to-black"
                >
                    <motion.div 
                        initial={{ scale: 0.9, y: 20 }}
                        animate={{ scale: 1, y: 0 }}
                        className="w-full max-w-md bg-slate-900/40 border border-white/10 rounded-2xl p-8 shadow-2xl backdrop-blur-xl relative overflow-hidden"
                    >
                        {/* Decorative Background Elements */}
                        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-cyan-500/50 to-transparent" />
                        
                        <div className="text-center mb-8">
                            <motion.div 
                                animate={{ 
                                    textShadow: ["0 0 10px rgba(34,211,238,0.2)", "0 0 20px rgba(34,211,238,0.4)", "0 0 10px rgba(34,211,238,0.2)"]
                                }}
                                transition={{ duration: 4, repeat: Infinity }}
                                className="text-4xl font-black tracking-tighter text-white mb-2 italic"
                            >
                                GODLESS
                            </motion.div>
                            <p className="text-xs uppercase tracking-[0.3em] text-slate-500 font-bold">Resonance Protocol v9.5</p>
                        </div>

                        {step === 'name' ? (
                            <div className="space-y-6">
                                {savedCharacters.length > 0 && (
                                    <div className="space-y-3">
                                        <div className="text-[10px] uppercase tracking-widest text-slate-500 font-bold flex items-center gap-2">
                                            <Clock size={10} /> Saved Identities
                                        </div>
                                        <div className="grid gap-2">
                                            {savedCharacters.map((char) => (
                                                <div key={char.name} className="group flex items-center gap-2">
                                                    <button
                                                        onClick={() => selectSaved(char.name)}
                                                        className="flex-1 flex items-center justify-between p-3 rounded-xl bg-white/5 border border-white/5 hover:bg-cyan-500/20 hover:border-cyan-500/40 transition-all text-left group"
                                                    >
                                                        <div className="flex items-center gap-3">
                                                            <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center text-slate-400 group-hover:text-cyan-400">
                                                                <User size={16} />
                                                            </div>
                                                            <span className="font-bold text-slate-300 group-hover:text-white transition-colors capitalize">{char.name}</span>
                                                        </div>
                                                        <LogIn size={14} className="opacity-0 group-hover:opacity-100 transition-opacity text-cyan-400" />
                                                    </button>
                                                    <button 
                                                        onClick={() => removeCharacter(char.name)}
                                                        className="p-3 rounded-xl hover:bg-red-500/10 hover:text-red-400 text-slate-600 transition-colors"
                                                        title="Forget Identity"
                                                    >
                                                        <Trash2 size={14} />
                                                    </button>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                <form onSubmit={handleLogin} className="space-y-4 pt-4 border-t border-white/5">
                                    <div className="text-[10px] uppercase tracking-widest text-slate-500 font-bold flex items-center gap-2">
                                        <Ghost size={10} /> Manifest New Essence
                                    </div>
                                    <div className="relative">
                                        <User className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
                                        <input
                                            autoFocus
                                            type="text"
                                            placeholder="IDENTITY NAME"
                                            value={name}
                                            onChange={(e) => setName(e.target.value)}
                                            className="w-full bg-white/5 border border-white/10 rounded-xl py-4 pl-12 pr-4 text-white focus:outline-none focus:border-cyan-500/50 focus:bg-white/10 transition-all font-bold placeholder:text-slate-700 uppercase tracking-wider"
                                        />
                                    </div>
                                    <button
                                        type="submit"
                                        disabled={!name || !isConnected}
                                        className="w-full py-4 bg-white text-black font-black rounded-xl hover:bg-cyan-400 transition-all disabled:opacity-50 disabled:grayscale uppercase tracking-widest text-xs flex items-center justify-center gap-2"
                                    >
                                        Establish Connection <LogIn size={14} />
                                    </button>
                                </form>
                            </div>
                        ) : (
                            <form onSubmit={handlePassword} className="space-y-6">
                                <div className="text-center">
                                    <div className="w-16 h-16 rounded-full bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center mx-auto mb-4 text-cyan-400 shadow-[0_0_20px_rgba(34,211,238,0.2)]">
                                        <Shield size={32} />
                                    </div>
                                    <h2 className="text-xl font-black text-white capitalize">{name}</h2>
                                    <p className="text-xs text-slate-500 font-medium">Identity Verification Required</p>
                                </div>
                                
                                <div className="relative">
                                    <Shield className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
                                    <input
                                        autoFocus
                                        type="password"
                                        placeholder="••••••••"
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        className="w-full bg-white/5 border border-white/10 rounded-xl py-4 pl-12 pr-4 text-white focus:outline-none focus:border-yellow-500/50 focus:bg-white/10 transition-all font-mono placeholder:text-slate-700 tracking-widest text-center text-lg"
                                    />
                                </div>

                                <div className="grid grid-cols-2 gap-3">
                                    <button
                                        type="button"
                                        onClick={() => setStep('name')}
                                        className="py-3 rounded-xl border border-white/5 text-slate-500 font-bold text-[10px] uppercase hover:bg-white/5 hover:text-slate-300 transition-all"
                                    >
                                        Change Identity
                                    </button>
                                    <button
                                        type="submit"
                                        className="py-3 rounded-xl bg-yellow-500 text-black font-black text-[10px] uppercase hover:bg-yellow-400 transition-all shadow-[0_0_15px_rgba(234,179,8,0.3)]"
                                    >
                                        Verify Purity
                                    </button>
                                </div>
                            </form>
                        )}

                        <div className="mt-8 pt-6 border-t border-white/5 flex items-center justify-between text-[10px] font-bold text-slate-600">
                            <span className="flex items-center gap-2 uppercase tracking-widest">
                                <div className={clsx("w-1.5 h-1.5 rounded-full animate-pulse", isConnected ? "bg-green-500 shadow-[0_0_8px_#22c55e]" : "bg-red-500")} />
                                {isConnected ? "Subspace Link Active" : "Searching for Node..."}
                            </span>
                            <span className="uppercase tracking-[0.2em] opacity-50">Experimental</span>
                        </div>
                    </motion.div>
                </motion.div>
            )}
        </AnimatePresence>
    );
};

export default LoginOverlay;
