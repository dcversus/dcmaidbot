/**
 * Type definitions for PRP-016 Multi-Room Interactive House Exploration Frontend
 */

export type RenderText = {
  format?: string;
  text?: string;
  env?: string;
  font: string;
  color: string;
  when?: "hover" | "click" | undefined;
};

export type WidgetStateMeta = {
  state: string;
  overlay: string;
  bbox: [number, number, number, number];
  render_text?: RenderText;
  region?: {
    mode: "cells" | "full";
    cells?: number[][];
  };
};

export type WidgetMeta = {
  id: string;
  states: WidgetStateMeta[];
};

export type MapMeta = {
  W: number;
  H: number;
  tile: number;
  widgets: WidgetMeta[];
  base_image: string;
  world_name: string;
  floor_name: string;
  location_name: string;
  generated_at: string;
};

export type WorldConfig = {
  world_name: string;
  version: string;
  style: {
    art_style: string;
    palette: string;
    camera: string;
    tile_size: number;
    grid: { cols: number; rows: number };
    hiDPI_scale: number;
  };
  floors: FloorConfig[];
};

export type FloorConfig = {
  id: string;
  name: string;
  seed_offset?: number;
  locations: LocationConfig[];
};

export type LocationConfig = {
  id: string;
  name: string;
  seed_offset?: number;
  description_prompt: string;
  bounds: { cols: number; rows: number };
  connections?: ConnectionConfig[];
  widgets?: WidgetConfig[];
};

export type ConnectionConfig = {
  to: string;
  type: string;
  grid: { x: number; y: number };
  from_side: string;
  to_side: string;
};

export type WidgetConfig = {
  id: string;
  type: string;
  name: string;
  grid: { x: number; y: number; w: number; h: number };
  prompt_base?: string;
  states: WidgetStateConfig[];
  region?: {
    mode: "cells" | "full";
    cells?: number[][];
  };
  config?: Record<string, any>;
};

export type WidgetStateConfig = {
  state: string;
  prompt?: string;
  region?: {
    mode: "cells" | "full";
    cells?: number[][];
  };
  render_text?: RenderText;
};

export type RenderState = {
  floorId: string;
  locId: string;
  base: HTMLImageElement;
  overlays: Record<string, HTMLImageElement>;
  meta: MapMeta;
  hoverWidgetId?: string;
  clickWidgetId?: string;
  isLoading: boolean;
  error?: string;
};

export type NavigationState = {
  currentFloor: string;
  currentLocation: string;
  availableLocations: LocationConfig[];
  transitionProgress: number;
  isTransitioning: boolean;
};

export type PerformanceMetrics = {
  loadTime: number;
  renderTime: number;
  cacheHitRate: number;
  memoryUsage: number;
  fps: number;
};

export type WorldRendererOptions = {
  canvasId: string;
  enableDebugMode?: boolean;
  enablePerformanceMonitoring?: boolean;
  pixelPerfectRendering?: boolean;
};

export type InteractionEvent = {
  type: "hover" | "click" | "navigate";
  widgetId?: string;
  location?: { floorId: string; locationId: string };
  timestamp: number;
  position: { x: number; y: number };
};

export type DebugInfo = {
  fps: number;
  renderTime: number;
  cacheStats: {
    hits: number;
    misses: number;
    total: number;
  };
  loadedAssets: number;
  totalAssets: number;
  currentHover: string | null;
  currentClick: string | null;
}