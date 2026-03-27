import React, { useMemo } from 'react';

// ANSI-to-CSS Mapping (v8.2 standard)
const ANSI_COLORS: Record<string, string> = {
  '31': 'text-red-500',    // Red
  '32': 'text-green-500',  // Green
  '33': 'text-yellow-500', // Yellow
  '34': 'text-blue-500',   // Blue
  '35': 'text-purple-500', // Purple
  '36': 'text-cyan-500',   // Cyan
  '37': 'text-slate-200',  // White/Grey
  '90': 'text-slate-500',  // Dark Grey
  '91': 'text-rose-400',   // Light Red
  '92': 'text-emerald-400',// Light Green
  '93': 'text-amber-400',  // Light Yellow
  '1': 'font-black',       // Bold/Highlight
};

interface AnsiTextProps {
  text: string;
}

export const AnsiText = ({ text }: AnsiTextProps) => {
  const spans = useMemo(() => {
    // Regex for \u001b[...m sequences
    const parts = text.split(/(\u001b\[[0-9;]*m)/);
    let activeClasses: string[] = [];
    
    return parts.map((part, i) => {
      const match = part.match(/\u001b\[([0-9;]*)m/);
      if (match) {
        const codes = match[1].split(';');
        if (codes.includes('0')) {
          activeClasses = []; // Reset
        } else {
          codes.forEach(code => {
            if (ANSI_COLORS[code]) activeClasses.push(ANSI_COLORS[code]);
          });
        }
        return null;
      }
      if (!part) return null;
      return (
        <span key={i} className={activeClasses.join(' ')}>
          {part}
        </span>
      );
    });
  }, [text]);

  return <div className="inline mr-1 whitespace-pre-wrap">{spans}</div>;
};

export default AnsiText;
