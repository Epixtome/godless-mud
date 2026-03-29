declare module 'lucide-react' {
  import { FC, SVGProps } from 'react';
  export interface IconProps extends SVGProps<SVGSVGElement> {
    size?: string | number;
    color?: string;
    strokeWidth?: string | number;
  }
  export type Icon = FC<IconProps>;
  export const Shield: Icon;
  export const ShieldCheck: Icon;
  export const ShieldAlert: Icon;
  export const Terminal: Icon;
  export const Plus: Icon;
  export const Search: Icon;
  export const ChevronRight: Icon;
  export const Database: Icon;
  export const UserCog: Icon;
  export const Box: Icon;
  export const Ghost: Icon;
  export const X: Icon;
  export const RefreshCw: Icon;
  export const Zap: Icon;
  export const Map: Icon;
  export const Activity: Icon;
  export const Info: Icon;
  export const Settings: Icon;
  export const MessageSquare: Icon;
  export const MessageSquareText: Icon;
  export const Compass: Icon;
  export const Sword: Icon;
  export const Swords: Icon;
  export const Heart: Icon;
  export const Target: Icon;
  export const Users: Icon;
  export const BookOpen: Icon;
  export const AlertCircle: Icon;
  export const Send: Icon;
  export const Award: Icon;
  export const User: Icon;
  export const Fingerprint: Icon;
  export const Briefcase: Icon;
  export const Sun: Icon;
  export const Layers: Icon;
}
