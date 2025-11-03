import { loadWorld, loadMeta, loadImage } from './loader';
import type { MapMeta, WidgetMeta, WidgetStateMeta, AppState } from './types';

type State = AppState;

const DPR = window.devicePixelRatio || 1;

function pickState(meta: WidgetMeta, stateName: string): WidgetStateMeta | undefined {
  return meta.states.find(s => s.state === stateName);
}

function pointInBBox(x: number, y: number, b: [number, number, number, number]): boolean {
  return x >= b[0] && y >= b[1] && x < b[0] + b[2] && y < b[1] + b[3];
}

async function init(floorId: string, locId: string) {
  const canvas = document.getElementById('c') as HTMLCanvasElement;
  const ctx = canvas.getContext('2d')!;
  const meta = await loadMeta(floorId, locId);
  const base = await loadImage(`/output/floors/${floorId}/${locId}/base.png`);

  canvas.width = meta.W * DPR;
  canvas.height = meta.H * DPR;
  canvas.style.width = meta.W + 'px';
  canvas.style.height = meta.H + 'px';
  ctx.imageSmoothingEnabled = false; // pixel art

  // preload overlays
  const overlays: Record<string, HTMLImageElement> = {};
  for (const w of meta.widgets) {
    for (const s of w.states) {
      const key = s.overlay;
      overlays[key] = await loadImage(`/output/floors/${floorId}/${locId}/${key}`);
    }
  }

  const state: State = { floorId, locId, base, overlays, meta };

  // input events
  canvas.addEventListener('mousemove', (e) => {
    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left) * DPR;
    const y = (e.clientY - rect.top) * DPR;
    state.hoverWidgetId = undefined;
    // compute topmost hover
    for (const w of state.meta.widgets) {
      const hover = pickState(w, 'hover') || pickState(w, 'idle'); // prefer hover
      if (!hover) continue;
      if (pointInBBox(x, y, hover.bbox)) { state.hoverWidgetId = w.id; break; }
    }
    draw(ctx, state);
  });

  canvas.addEventListener('click', (e) => {
    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left) * DPR;
    const y = (e.clientY - rect.top) * DPR;
    state.clickWidgetId = undefined;
    for (const w of state.meta.widgets) {
      // click region = hover bbox by default; can customize in world.json via click state bbox
      const click = pickState(w, 'click') || pickState(w, 'hover') || pickState(w, 'idle');
      if (!click) continue;
      if (pointInBBox(x, y, click.bbox)) { state.clickWidgetId = w.id; break; }
    }
    draw(ctx, state);
  });

  // clock tick for dynamic text
  setInterval(() => draw(ctx, state), 1000);

  draw(ctx, state);
}

function draw(ctx: CanvasRenderingContext2D, s: State) {
  const { meta, base } = s;
  ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
  ctx.drawImage(base, 0, 0, ctx.canvas.width, ctx.canvas.height);

  // pass 1: overlays (idle/hover)
  for (const w of meta.widgets) {
    const isHover = (s.hoverWidgetId === w.id);
    const stateName = isHover ? 'hover' : 'idle';
    const st = pickState(w, stateName) || pickState(w, 'idle');
    if (!st) continue;
    const img = s.overlays[st.overlay];
    // If full-screen replacement on hover, draw over entire canvas:
    if (st.bbox[2] === meta.W && st.bbox[3] === meta.H) {
      ctx.drawImage(img, 0, 0, ctx.canvas.width, ctx.canvas.height);
    } else {
      const [x, y, wpx, hpx] = st.bbox.map(v => v * DPR) as [number, number, number, number];
      ctx.drawImage(img, x, y, wpx, hpx, x, y, wpx, hpx); // overlay canvas-aligned
      maybeRenderText(ctx, st, x, y, wpx, hpx);
    }
  }

  // pass 2: click state overlay (priority)
  if (s.clickWidgetId) {
    const w = meta.widgets.find(_ => _.id === s.clickWidgetId)!;
    const st = pickState(w, 'click') || pickState(w, 'hover') || pickState(w, 'idle');
    if (st) {
      const img = s.overlays[st.overlay];
      if (st.bbox[2] === meta.W && st.bbox[3] === meta.H) {
        ctx.drawImage(img, 0, 0, ctx.canvas.width, ctx.canvas.height);
      } else {
        const [x, y, wpx, hpx] = st.bbox.map(v => v * DPR) as [number, number, number, number];
        ctx.drawImage(img, x, y, wpx, hpx, x, y, wpx, hpx);
        maybeRenderText(ctx, st, x, y, wpx, hpx);
      }
    }
  }
}

function maybeRenderText(ctx: CanvasRenderingContext2D, st: WidgetStateMeta, x: number, y: number, w: number, h: number) {
  const rt = st.render_text;
  if (!rt) return;
  // Decide when: if 'when' defined and not matching current pass, you can gate it externally
  ctx.imageSmoothingEnabled = false;
  ctx.textBaseline = 'top';
  ctx.font = `12px ${rt.font || 'monospace'}`;
  ctx.fillStyle = rt.color || '#ffffff';
  let text = rt.text || '';
  if (rt.env === "GIT_COMMIT_SHORT") {
    text = (window as any).__GIT_COMMIT_SHORT__ || 'unknown';
  }
  if (rt.format) {
    const d = new Date();
    const pad = (n: number) => String(n).padStart(2, '0');
    const HH = pad(d.getHours()), mm = pad(d.getMinutes()), ss = pad(d.getSeconds());
    text = rt.format.replace('HH', HH).replace('mm', mm).replace('ss', ss);
  }
  // draw centered within bbox
  const tx = x + 4, ty = y + 4;
  ctx.fillText(text, tx, ty);
}

// Boot
init('floor_2', 'liliths_room');
