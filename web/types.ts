export type RenderText = {
  format?: string;
  text?: string;
  env?: string;
  font: string;
  font_size?: number;
  color: string;
  when?: "hover"|"click"|undefined;
};

export type WidgetStateMeta = {
  state:string;
  overlay:string;
  bbox:[number,number,number,number];
  render_text?:RenderText;
};

export type WidgetMeta = {
  id:string;
  states:WidgetStateMeta[];
};

export type MapMeta = {
  W:number;
  H:number;
  tile:number;
  widgets:WidgetMeta[];
};

export type AppState = {
  floorId: string;
  locId: string;
  base: HTMLImageElement;
  overlays: Record<string, HTMLImageElement>;
  meta: MapMeta;
  hoverWidgetId?: string;
  clickWidgetId?: string;
  worldConfig?: any;
};
