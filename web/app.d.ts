/**
 * Main canvas rendering application for PRP-016 Multi-Room Interactive House Exploration
 */
import type { PerformanceMetrics, InteractionEvent, NavigationState, ConnectionConfig } from './types';
export declare class WorldRenderer {
    private canvas;
    private ctx;
    private state;
    private worldConfig;
    private navigationState;
    private isInitialized;
    private animationFrameId;
    private lastFrameTime;
    private frameCount;
    private performanceMetrics;
    private eventHistory;
    private onInteraction?;
    constructor(canvasId: string, options?: {
        enableDebugMode?: boolean;
        enablePerformanceMonitoring?: boolean;
        pixelPerfectRendering?: boolean;
    });
    initialize(floorId: string, locId: string): Promise<void>;
    private setupCanvas;
    private loadAssets;
    private setupEventHandlers;
    private handleMouseMove;
    private handleClick;
    private findConnectionForWidget;
    private handleMouseLeave;
    private handleResize;
    private findWidgetAtPosition;
    private getWidgetState;
    private startRenderLoop;
    private draw;
    private drawWidgetOverlays;
    private drawWidgetOverlay;
    private drawRenderText;
    private drawDynamicText;
    private drawDebugInfo;
    private drawTransitionEffect;
    private trackInteraction;
    changeLocation(floorId: string, locId: string): Promise<void>;
    navigateToLocation(floorId: string, locId: string): Promise<void>;
    updateNavigationState(): void;
    private completeNavigation;
    private updateAvailableConnections;
    getNavigationState(): NavigationState;
    useConnection(connection: ConnectionConfig): Promise<void>;
    setInteractionCallback(callback: (event: InteractionEvent) => void): void;
    getPerformanceMetrics(): PerformanceMetrics;
    getEventHistory(): InteractionEvent[];
    isDebugMode(): boolean;
    destroy(): void;
}
export declare function createWorldRenderer(canvasId: string, floorId: string, locId: string, options?: {
    enableDebugMode?: boolean;
    enablePerformanceMonitoring?: boolean;
    pixelPerfectRendering?: boolean;
}): Promise<WorldRenderer>;
