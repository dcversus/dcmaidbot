/**
 * Asset loading utilities for PRP-016 Multi-Room Interactive House Exploration
 */
import type { WorldConfig, MapMeta, WidgetMeta } from './types';
export declare class AssetLoader {
    private loadedImages;
    private loadingPromises;
    private cacheEnabled;
    constructor(cacheEnabled?: boolean);
    loadWorld(): Promise<WorldConfig>;
    loadMeta(floorId: string, locId: string): Promise<MapMeta>;
    loadImage(url: string): Promise<HTMLImageElement>;
    loadWidgetOverlays(floorId: string, locId: string, widgets: WidgetMeta[]): Promise<Record<string, HTMLImageElement>>;
    loadBaseImage(floorId: string, locId: string, baseImage: string): Promise<HTMLImageElement>;
    preloadLocationAssets(floorId: string, locId: string, meta: MapMeta): Promise<void>;
    getCacheStats(): {
        cached: number;
        loading: number;
        total: number;
    };
    clearCache(): void;
    getLoadedImage(url: string): HTMLImageElement | undefined;
    isImageLoaded(url: string): boolean;
    isImageLoading(url: string): boolean;
}
export declare const assetLoader: AssetLoader;
export declare function getAssetUrl(floorId: string, locId: string, assetPath: string): string;
export declare function getWidgetOverlayUrl(floorId: string, locId: string, widgetId: string, state: string): string;
export declare function getBaseImageUrl(floorId: string, locId: string): string;
export declare function preloadLocation(floorId: string, locId: string): Promise<void>;
