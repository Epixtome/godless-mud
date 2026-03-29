import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { clsx } from 'clsx';

interface CombatTextOverlayProps {
    combatNotifications: any[];
    mapData: any;
    tileSize: number;
}

export const CombatTextOverlay = ({ combatNotifications, mapData, tileSize }: CombatTextOverlayProps) => {
    return (
        <AnimatePresence>
            {combatNotifications.map((notif: any) => {
                const center = mapData?.center || { x: 0, y: 0 };
                const gridX = notif.x ?? center.x;
                const gridY = notif.y ?? center.y;
                
                return (
                    <motion.div
                        key={notif.id}
                        initial={{ opacity: 0, scale: 0.1, y: 20 }}
                        animate={{ 
                            opacity: [0, 1, 1, 0.8], 
                            scale: [1.5, 1.2, 1, 0.9],
                            y: -120 
                        }}
                        exit={{ opacity: 0, y: -180, transition: { duration: 0.8 } }}
                        transition={{ duration: 1.5, ease: "easeOut" }}
                        className={clsx(
                            "absolute z-[100] font-black text-sm pointer-events-none whitespace-nowrap tracking-tighter drop-shadow-2xl",
                            notif.is_critical ? "text-yellow-400 text-lg scale-150" : 
                            notif.type === 'damage' ? "text-red-500" : "text-blue-400"
                        )}
                        style={{
                            left: '50%',
                            top: '50%',
                            transform: 'translate(-50%, -50%)',
                            marginLeft: ((gridX - center.x) * (tileSize + 2)) + (notif.offsetX || 0),
                            marginTop: ((gridY - center.y) * (tileSize + 2)) + (notif.offsetY || 0),
                        }}
                    >
                        {notif.is_critical && "💥 "}
                        {notif.type === 'damage' ? `-${notif.value}` : notif.type.toUpperCase()}
                        {notif.is_critical && "!"}
                    </motion.div>
                );
            })}
        </AnimatePresence>
    );
};
