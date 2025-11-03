import type { MapMeta } from './types';

export async function loadWorld(): Promise<any> {
  const res = await fetch('/world.json');
  return res.json();
}

export async function loadMeta(floorId: string, locId: string): Promise<MapMeta> {
  const res = await fetch(`/output/floors/${floorId}/${locId}/map.meta.json`);
  return res.json();
}

export async function loadImage(url: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = reject;
    img.src = url;
  });
}
