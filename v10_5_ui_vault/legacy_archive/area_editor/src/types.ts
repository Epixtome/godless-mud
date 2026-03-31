export interface Room {
  id: string;
  zone_id: string;
  name: string;
  description: string;
  x: number;
  y: number;
  z: number;
  terrain: string;
  elevation: number;
  traversal_cost: number;
  opacity: number;
  symbol: string | null;
  manual_exits: boolean;
  exits: Record<string, string>;
  tags: string[];
  items: any[];
  monsters: any[];
  doors: Record<string, any>;
}

export interface ZoneMetadata {
  id: string;
  name: string;
  security_level: string;
  grid_logic: boolean;
  target_cr: number;
}

export interface ZoneData {
  metadata: ZoneMetadata;
  rooms: Room[];
}
