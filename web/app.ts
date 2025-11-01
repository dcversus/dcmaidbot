/**
 * Main canvas rendering application for PRP-016 Multi-Room Interactive House Exploration
 */

import {
  assetLoader,
  preloadLocation,
  getAssetUrl,
  getWidgetOverlayUrl,
  getBaseImageUrl
} from './loader';
import type {
  RenderState,
  MapMeta,
  WidgetMeta,
  WidgetStateMeta,
  RenderText,
  WorldConfig,
  LocationConfig,
  PerformanceMetrics,
  InteractionEvent
} from './types';

export class WorldRenderer {
  private canvas: HTMLCanvasElement;
  private ctx: CanvasRenderingContext2D;
  private state: RenderState;
  private worldConfig: WorldConfig | null = null;
  private isInitialized: boolean = false;
  private animationFrameId: number | null = null;
  private lastFrameTime: number = 0;
  private frameCount: number = 0;

  // Performance monitoring
  private performanceMetrics: PerformanceMetrics = {
    loadTime: 0,
    renderTime: 0,
    cacheHitRate: 0,
    memoryUsage: 0,
    fps: 0
  };

  // Event tracking
  private eventHistory: InteractionEvent[] = [];
  private onInteraction?: (event: InteractionEvent) => void;

  constructor(canvasId: string, options: {
    enableDebugMode?: boolean;
    enablePerformanceMonitoring?: boolean;
    pixelPerfectRendering?: boolean;
  } = {}) {
    this.canvas = document.getElementById(canvasId) as HTMLCanvasElement;
    if (!this.canvas) {
      throw new Error(`Canvas element with id '${canvasId}' not found`);
    }

    const ctx = this.canvas.getContext('2d');
    if (!ctx) {
      throw new Error('Failed to get 2D rendering context');
    }
    this.ctx = ctx;

    // Initialize empty state
    this.state = {
      floorId: '',
      locId: '',
      base: new Image(),
      overlays: {},
      meta: {
        W: 0,
        H: 0,
        tile: 64,
        widgets: [],
        base_image: 'base.png',
        world_name: '',
        floor_name: '',
        location_name: '',
        tracked_at: ''
      },
      isLoading: false
    };

    // Configure canvas for pixel-perfect rendering
    if (options.pixelPerfectRendering !== false) {
      this.ctx.imageSmoothingEnabled = false;
    }

    console.log('🎮 WorldRenderer initialized');
  }

  async initialize(floorId: string, locId: string): Promise<void> {
    /** Initialize renderer with specific floor and location. */
    if (this.isInitialized) {
      console.warn('⚠️ Renderer already initialized');
      return;
    }

    const startTime = performance.now();

    try {
      this.state.isLoading = true;
      this.state.floorId = floorId;
      this.state.locId = locId;

      // Load world configuration
      if (!this.worldConfig) {
        this.worldConfig = await assetLoader.loadWorld();
      }

      // Load location metadata
      this.state.meta = await assetLoader.loadMeta(floorId, locId);

      // Set canvas dimensions
      this.setupCanvas();

      // Load assets
      await this.loadAssets();

      // Setup event handlers
      this.setupEventHandlers();

      // Start render loop
      this.startRenderLoop();

      this.isInitialized = true;
      this.state.isLoading = false;

      // Update performance metrics
      this.performanceMetrics.loadTime = performance.now() - startTime;

      console.log(`✅ Renderer initialized for ${floorId}/${locId}`);
      console.log(`📊 Load time: ${this.performanceMetrics.loadTime.toFixed(2)}ms`);

    } catch (error) {
      this.state.isLoading = false;
      this.state.error = error instanceof Error ? error.message : 'Unknown error';
      console.error('❌ Failed to initialize renderer:', error);
      throw error;
    }
  }

  private setupCanvas(): void {
    /** Setup canvas dimensions and scaling. */
    const DPR = window.devicePixelRatio || 1;
    const { W, H } = this.state.meta;

    // Set canvas resolution
    this.canvas.width = W * DPR;
    this.canvas.height = H * DPR;

    // Set canvas display size
    this.canvas.style.width = `${W}px`;
    this.canvas.style.height = `${H}px`;

    // Scale context for pixel-perfect rendering
    this.ctx.scale(DPR, DPR);

    console.log(`🖼️ Canvas setup: ${W}x${H} (DPR: ${DPR})`);
  }

  private async loadAssets(): Promise<void> {
    /** Load all required assets for current location. */
    const { floorId, locId, meta } = this.state;

    // Load base image
    this.state.base = await assetLoader.loadBaseImage(floorId, locId, meta.base_image);

    // Load widget overlays
    this.state.overlays = await assetLoader.loadWidgetOverlays(floorId, locId, meta.widgets);

    console.log(`📦 Assets loaded: ${Object.keys(this.state.overlays).length} overlays`);
  }

  private setupEventHandlers(): void {
    /** Setup mouse event handlers for widget interaction. */
    this.canvas.addEventListener('mousemove', this.handleMouseMove.bind(this));
    this.canvas.addEventListener('click', this.handleClick.bind(this));
    this.canvas.addEventListener('mouseleave', this.handleMouseLeave.bind(this));

    // Handle window resize
    window.addEventListener('resize', this.handleResize.bind(this));

    console.log('🖱️ Event handlers setup complete');
  }

  private handleMouseMove(event: MouseEvent): void {
    /** Handle mouse move events for hover states. */
    const rect = this.canvas.getBoundingClientRect();
    const DPR = window.devicePixelRatio || 1;
    const x = (event.clientX - rect.left) * DPR;
    const y = (event.clientY - rect.top) * DPR;

    // Find hovered widget
    const hoveredWidgetId = this.findWidgetAtPosition(x, y);

    if (hoveredWidgetId !== this.state.hoverWidgetId) {
      this.state.hoverWidgetId = hoveredWidgetId;
      this.trackInteraction('hover', hoveredWidgetId, { x, y });
    }
  }

  private handleClick(event: MouseEvent): void {
    /** Handle click events for widget interaction. */
    const rect = this.canvas.getBoundingClientRect();
    const DPR = window.devicePixelRatio || 1;
    const x = (event.clientX - rect.left) * DPR;
    const y = (event.clientY - rect.top) * DPR;

    // Find clicked widget
    const clickedWidgetId = this.findWidgetAtPosition(x, y);

    if (clickedWidgetId) {
      this.state.clickWidgetId = clickedWidgetId;
      this.trackInteraction('click', clickedWidgetId, { x, y });

      // Reset click state after a short delay
      setTimeout(() => {
        this.state.clickWidgetId = undefined;
      }, 200);
    }
  }

  private handleMouseLeave(): void {
    /** Handle mouse leave events. */
    this.state.hoverWidgetId = undefined;
  }

  private handleResize(): void {
    /** Handle window resize events. */
    // Re-setup canvas dimensions
    this.setupCanvas();
    // Trigger redraw
    this.draw();
  }

  private findWidgetAtPosition(x: number, y: number): string | undefined {
    /** Find which widget is at the given position. */
    const { meta } = this.state;

    for (const widget of meta.widgets) {
      // Try click state first, then hover, then idle
      const clickState = this.getWidgetState(widget, 'click');
      const hoverState = this.getWidgetState(widget, 'hover') || this.getWidgetState(widget, 'idle');

      const stateToCheck = clickState || hoverState;
      if (!stateToCheck) continue;

      const [bx, by, bw, bh] = stateToCheck.bbox;
      if (x >= bx && x < bx + bw && y >= by && y < by + bh) {
        return widget.id;
      }
    }

    return undefined;
  }

  private getWidgetState(widget: WidgetMeta, stateName: string): WidgetStateMeta | undefined {
    /** Get specific state metadata for a widget. */
    return widget.states.find(s => s.state === stateName);
  }

  private startRenderLoop(): void {
    /** Start the render loop. */
    const render = (currentTime: number) => {
      // Calculate FPS
      if (this.lastFrameTime > 0) {
        const deltaTime = currentTime - this.lastFrameTime;
        this.performanceMetrics.fps = 1000 / deltaTime;
      }
      this.lastFrameTime = currentTime;
      this.frameCount++;

      // Draw frame
      this.draw();

      // Continue loop
      this.animationFrameId = requestAnimationFrame(render);
    };

    this.animationFrameId = requestAnimationFrame(render);
    console.log('🎬 Render loop started');
  }

  private draw(): void {
    /** Main draw function. */
    const startTime = performance.now();

    try {
      const { meta, base, overlays } = this.state;

      // Clear canvas
      this.ctx.clearRect(0, 0, this.ctx.canvas.width, this.ctx.canvas.height);

      // Draw base image
      if (base.complete) {
        this.ctx.drawImage(base, 0, 0, meta.W, meta.H);
      }

      // Draw widget overlays (pass 1: idle/hover)
      this.drawWidgetOverlays('hover');

      // Draw widget overlays (pass 2: click state with priority)
      if (this.state.clickWidgetId) {
        this.drawWidgetOverlay(this.state.clickWidgetId, 'click');
      }

      // Draw dynamic text (clock, version info, etc.)
      this.drawDynamicText();

      // Draw debug info if enabled
      if (this.isDebugMode()) {
        this.drawDebugInfo();
      }

    } catch (error) {
      console.error('❌ Draw error:', error);
    }

    // Update performance metrics
    this.performanceMetrics.renderTime = performance.now() - startTime;
  }

  private drawWidgetOverlays(interactionType: 'hover' | 'click'): void {
    /** Draw widget overlays based on interaction state. */
    const { meta, overlays, hoverWidgetId, clickWidgetId } = this.state;

    for (const widget of meta.widgets) {
      const isHovered = widget.id === hoverWidgetId;
      const isClicked = widget.id === clickWidgetId;

      let stateName: string;
      if (interactionType === 'click' && isClicked) {
        stateName = 'click';
      } else if (interactionType === 'hover' && isHovered) {
        stateName = 'hover';
      } else {
        stateName = 'idle';
      }

      const state = this.getWidgetState(widget, stateName);
      if (!state) continue;

      const overlay = overlays[state.overlay];
      if (!overlay || !overlay.complete) continue;

      const [x, y, w, h] = state.bbox;

      // Draw overlay
      this.ctx.drawImage(overlay, x, y, w, h);

      // Draw dynamic text if present
      if (state.render_text) {
        this.drawRenderText(state.render_text, x, y, w, h);
      }
    }
  }

  private drawWidgetOverlay(widgetId: string, stateName: string): void {
    /** Draw specific widget state overlay. */
    const { meta, overlays } = this.state;
    const widget = meta.widgets.find(w => w.id === widgetId);
    if (!widget) return;

    const state = this.getWidgetState(widget, stateName);
    if (!state) return;

    const overlay = overlays[state.overlay];
    if (!overlay || !overlay.complete) return;

    const [x, y, w, h] = state.bbox;

    // Draw overlay
    this.ctx.drawImage(overlay, x, y, w, h);

    // Draw dynamic text if present
    if (state.render_text) {
      this.drawRenderText(state.render_text, x, y, w, h);
    }
  }

  private drawRenderText(renderText: RenderText, x: number, y: number, w: number, h: number): void {
    /** Draw dynamic text on widget overlay. */
    this.ctx.save();

    // Setup text styling
    this.ctx.imageSmoothingEnabled = false;
    this.ctx.textBaseline = 'top';
    this.ctx.font = `12px ${renderText.font || 'monospace'}`;
    this.ctx.fillStyle = renderText.color || '#ffffff';
    this.ctx.shadowColor = 'rgba(0, 0, 0, 0.8)';
    this.ctx.shadowBlur = 2;

    // Generate text content
    let text = renderText.text || '';
    if (renderText.env === "GIT_COMMIT_SHORT") {
      text = (window as any).__GIT_COMMIT_SHORT__ || 'unknown';
    }
    if (renderText.format) {
      const now = new Date();
      const pad = (n: number) => String(n).padStart(2, '0');
      const HH = pad(now.getHours());
      const mm = pad(now.getMinutes());
      const ss = pad(now.getSeconds());
      text = renderText.format
        .replace('HH', HH)
        .replace('mm', mm)
        .replace('ss', ss);
    }

    // Draw text centered in bbox
    const textX = x + 4;
    const textY = y + 4;
    this.ctx.fillText(text, textX, textY);

    this.ctx.restore();
  }

  private drawDynamicText(): void {
    /** Draw dynamic text elements (clock, version, etc.). */
    // This can be extended for global dynamic elements
    // Currently handled per-widget in drawRenderText
  }

  private drawDebugInfo(): void {
    /** Draw debug information overlay. */
    this.ctx.save();
    this.ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
    this.ctx.fillRect(10, 10, 200, 100);

    this.ctx.fillStyle = '#00ff00';
    this.ctx.font = '10px monospace';
    this.ctx.textBaseline = 'top';

    const debugInfo = [
      `FPS: ${this.performanceMetrics.fps.toFixed(1)}`,
      `Render: ${this.performanceMetrics.renderTime.toFixed(2)}ms`,
      `Hover: ${this.state.hoverWidgetId || 'none'}`,
      `Click: ${this.state.clickWidgetId || 'none'}`,
      `Assets: ${Object.keys(this.state.overlays).length}`
    ];

    debugInfo.forEach((line, index) => {
      this.ctx.fillText(line, 15, 15 + index * 12);
    });

    this.ctx.restore();
  }

  private trackInteraction(type: 'hover' | 'click' | 'navigate', widgetId?: string, position?: { x: number; y: number }): void {
    /** Track user interaction for analytics. */
    const event: InteractionEvent = {
      type,
      widgetId,
      timestamp: Date.now(),
      position: position || { x: 0, y: 0 }
    };

    this.eventHistory.push(event);

    // Keep only last 100 events
    if (this.eventHistory.length > 100) {
      this.eventHistory = this.eventHistory.slice(-100);
    }

    // Notify callback if set
    if (this.onInteraction) {
      this.onInteraction(event);
    }
  }

  // Public API methods

  public async changeLocation(floorId: string, locId: string): Promise<void> {
    /** Change to a different location. */
    if (floorId === this.state.floorId && locId === this.state.locId) {
      console.log(`⚠️ Already at ${floorId}/${locId}`);
      return;
    }

    console.log(`🔄 Changing location to ${floorId}/${locId}`);

    // Track navigation event
    this.trackInteraction('navigate', undefined, undefined);

    // Clean up current state
    this.state.overlays = {};
    this.state.hoverWidgetId = undefined;
    this.state.clickWidgetId = undefined;

    // Initialize new location
    await this.initialize(floorId, locId);
  }

  public setInteractionCallback(callback: (event: InteractionEvent) => void): void {
    /** Set callback for interaction events. */
    this.onInteraction = callback;
  }

  public getPerformanceMetrics(): PerformanceMetrics {
    /** Get current performance metrics. */
    const cacheStats = assetLoader.getCacheStats();
    this.performanceMetrics.cacheHitRate = cacheStats.cached / Math.max(cacheStats.total, 1);

    return { ...this.performanceMetrics };
  }

  public getEventHistory(): InteractionEvent[] {
    /** Get interaction event history. */
    return [...this.eventHistory];
  }

  public isDebugMode(): boolean {
    /** Check if debug mode is enabled. */
    return (window as any).__DEBUG_MODE__ === true;
  }

  public destroy(): void {
    /** Clean up renderer resources. */
    if (this.animationFrameId) {
      cancelAnimationFrame(this.animationFrameId);
      this.animationFrameId = null;
    }

    // Remove event listeners
    this.canvas.removeEventListener('mousemove', this.handleMouseMove.bind(this));
    this.canvas.removeEventListener('click', this.handleClick.bind(this));
    this.canvas.removeEventListener('mouseleave', this.handleMouseLeave.bind(this));
    window.removeEventListener('resize', this.handleResize.bind(this));

    this.isInitialized = false;
    console.log('🗑️ WorldRenderer destroyed');
  }
}

// Export factory function for easy initialization
export async function createWorldRenderer(
  canvasId: string,
  floorId: string,
  locId: string,
  options?: {
    enableDebugMode?: boolean;
    enablePerformanceMonitoring?: boolean;
    pixelPerfectRendering?: boolean;
  }
): Promise<WorldRenderer> {
  /** Create and initialize a WorldRenderer instance. */
  const renderer = new WorldRenderer(canvasId, options);
  await renderer.initialize(floorId, locId);
  return renderer;
}