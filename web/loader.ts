/**
 * Asset loading utilities for PRP-016 Multi-Room Interactive House Exploration
 */

import type { WorldConfig, MapMeta, WidgetMeta, WidgetStateMeta } from './types';

export class AssetLoader {
  private loadedImages: Map<string, HTMLImageElement> = new Map();
  private loadingPromises: Map<string, Promise<HTMLImageElement>> = new Map();
  private cacheEnabled: boolean = true;

  constructor(cacheEnabled: boolean = true) {
    this.cacheEnabled = cacheEnabled;
  }

  async loadWorld(): Promise<WorldConfig> {
    /** Load world configuration from JSON file. */
    try {
      const response = await fetch('/static/world.json');
      if (!response.ok) {
        throw new Error(`Failed to load world.json: ${response.status}`);
      }
      const config: WorldConfig = await response.json();
      console.log(`✅ Loaded world config: ${config.world_name}`);
      return config;
    } catch (error) {
      console.error('❌ Error loading world config:', error);
      throw error;
    }
  }

  async loadMeta(floorId: string, locId: string): Promise<MapMeta> {
    /** Load map metadata for specific floor and location. */
    try {
      const url = `/static/output/floors/${floorId}/${locId}/map.meta.json`;
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`Failed to load metadata: ${response.status}`);
      }
      const meta: MapMeta = await response.json();
      console.log(`✅ Loaded metadata for ${floorId}/${locId}`);
      return meta;
    } catch (error) {
      console.error(`❌ Error loading metadata for ${floorId}/${locId}:`, error);
      throw error;
    }
  }

  async loadImage(url: string): Promise<HTMLImageElement> {
    /** Load image with caching support. */
    // Check cache first
    if (this.cacheEnabled && this.loadedImages.has(url)) {
      return this.loadedImages.get(url)!;
    }

    // Check if already loading
    if (this.loadingPromises.has(url)) {
      return this.loadingPromises.get(url)!;
    }

    // Create loading promise
    const loadingPromise = new Promise<HTMLImageElement>((resolve, reject) => {
      const img = new Image();
      img.onload = () => {
        this.loadedImages.set(url, img);
        this.loadingPromises.delete(url);
        resolve(img);
      };
      img.onerror = () => {
        this.loadingPromises.delete(url);
        reject(new Error(`Failed to load image: ${url}`));
      };
      img.src = url;
    });

    this.loadingPromises.set(url, loadingPromise);
    return loadingPromise;
  }

  async loadWidgetOverlays(
    floorId: string,
    locId: string,
    widgets: WidgetMeta[]
  ): Promise<Record<string, HTMLImageElement>> {
    /** Load all widget overlay images for a location. */
    const overlays: Record<string, HTMLImageElement> = {};
    const loadingPromises: Promise<void>[] = [];

    for (const widget of widgets) {
      for (const state of widget.states) {
        const overlayUrl = `/static/output/floors/${floorId}/${locId}/${state.overlay}`;

        loadingPromises.push(
          this.loadImage(overlayUrl)
            .then(img => {
              overlays[state.overlay] = img;
            })
            .catch(error => {
              console.warn(`⚠️ Failed to load widget overlay: ${overlayUrl}`, error);
            })
        );
      }
    }

    await Promise.all(loadingPromises);
    return overlays;
  }

  async loadBaseImage(floorId: string, locId: string, baseImage: string): Promise<HTMLImageElement> {
    /** Load base scene image for a location. */
    const baseUrl = `/static/output/floors/${floorId}/${locId}/${baseImage}`;
    return this.loadImage(baseUrl);
  }

  preloadLocationAssets(floorId: string, locId: string, meta: MapMeta): Promise<void> {
    /** Preload all assets for a location. */
    return new Promise((resolve, reject) => {
      const promises: Promise<any>[] = [];

      // Load base image
      promises.push(this.loadBaseImage(floorId, locId, meta.base_image));

      // Load widget overlays
      promises.push(this.loadWidgetOverlays(floorId, locId, meta.widgets));

      Promise.all(promises)
        .then(() => {
          console.log(`✅ Preloaded all assets for ${floorId}/${locId}`);
          resolve();
        })
        .catch(error => {
          console.error(`❌ Failed to preload assets for ${floorId}/${locId}:`, error);
          reject(error);
        });
    });
  }

  getCacheStats(): { cached: number; loading: number; total: number } {
    /** Get cache statistics. */
    return {
      cached: this.loadedImages.size,
      loading: this.loadingPromises.size,
      total: this.loadedImages.size + this.loadingPromises.size
    };
  }

  clearCache(): void {
    /** Clear all cached images. */
    this.loadedImages.clear();
    this.loadingPromises.clear();
    console.log('🗑️ Cleared asset cache');
  }

  getLoadedImage(url: string): HTMLImageElement | undefined {
    /** Get cached image without loading. */
    return this.loadedImages.get(url);
  }

  isImageLoaded(url: string): boolean {
    /** Check if image is loaded. */
    return this.loadedImages.has(url);
  }

  isImageLoading(url: string): boolean {
    /** Check if image is currently loading. */
    return this.loadingPromises.has(url);
  }
}

// Global asset loader instance
export const assetLoader = new AssetLoader();

// Utility functions for asset management
export function getAssetUrl(floorId: string, locId: string, assetPath: string): string {
  /** Generate full URL for an asset. */
  return `/static/output/floors/${floorId}/${locId}/${assetPath}`;
}

export function getWidgetOverlayUrl(
  floorId: string,
  locId: string,
  widgetId: string,
  state: string
): string {
  /** Generate URL for specific widget state overlay. */
  return `/static/output/floors/${floorId}/${locId}/overlays/${widgetId}__${state}.png`;
}

export function getBaseImageUrl(floorId: string, locId: string): string {
  /** Generate URL for base scene image. */
  return `/static/output/floors/${floorId}/${locId}/base.png`;
}

export async function preloadLocation(
  floorId: string,
  locId: string
): Promise<void> {
  /** Preload all assets for a location using global loader. */
  const meta = await assetLoader.loadMeta(floorId, locId);
  return assetLoader.preloadLocationAssets(floorId, locId, meta);
}