/**
 * Main canvas rendering application for PRP-016 Multi-Room Interactive House Exploration
 */
import { assetLoader } from './loader';
export class WorldRenderer {
    constructor(canvasId, options = {}) {
        this.worldConfig = null;
        this.isInitialized = false;
        this.animationFrameId = null;
        this.lastFrameTime = 0;
        this.frameCount = 0;
        // Performance monitoring
        this.performanceMetrics = {
            loadTime: 0,
            renderTime: 0,
            cacheHitRate: 0,
            memoryUsage: 0,
            fps: 0
        };
        // Event tracking
        this.eventHistory = [];
        this.canvas = document.getElementById(canvasId);
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
                generated_at: ''
            },
            isLoading: false
        };
        // Initialize navigation state
        this.navigationState = {
            currentFloor: '',
            currentLocation: '',
            availableConnections: [],
            transitionProgress: 0,
            isTransitioning: false,
            transitionDuration: 800 // 800ms transition duration
        };
        // Configure canvas for pixel-perfect rendering
        if (options.pixelPerfectRendering !== false) {
            this.ctx.imageSmoothingEnabled = false;
        }
        console.log('🎮 WorldRenderer initialized');
    }
    async initialize(floorId, locId) {
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
            // Update navigation state for new location
            this.navigationState.currentFloor = floorId;
            this.navigationState.currentLocation = locId;
            this.updateAvailableConnections();
            this.isInitialized = true;
            this.state.isLoading = false;
            // Update performance metrics
            this.performanceMetrics.loadTime = performance.now() - startTime;
            console.log(`✅ Renderer initialized for ${floorId}/${locId}`);
            console.log(`📊 Load time: ${this.performanceMetrics.loadTime.toFixed(2)}ms`);
        }
        catch (error) {
            this.state.isLoading = false;
            this.state.error = error instanceof Error ? error.message : 'Unknown error';
            console.error('❌ Failed to initialize renderer:', error);
            throw error;
        }
    }
    setupCanvas() {
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
    async loadAssets() {
        /** Load all required assets for current location. */
        const { floorId, locId, meta } = this.state;
        // Load base image
        this.state.base = await assetLoader.loadBaseImage(floorId, locId, meta.base_image);
        // Load widget overlays
        this.state.overlays = await assetLoader.loadWidgetOverlays(floorId, locId, meta.widgets);
        console.log(`📦 Assets loaded: ${Object.keys(this.state.overlays).length} overlays`);
    }
    setupEventHandlers() {
        /** Setup mouse event handlers for widget interaction. */
        this.canvas.addEventListener('mousemove', this.handleMouseMove.bind(this));
        this.canvas.addEventListener('click', this.handleClick.bind(this));
        this.canvas.addEventListener('mouseleave', this.handleMouseLeave.bind(this));
        // Handle window resize
        window.addEventListener('resize', this.handleResize.bind(this));
        console.log('🖱️ Event handlers setup complete');
    }
    handleMouseMove(event) {
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
    handleClick(event) {
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
            // Check if clicked widget is a connection widget
            const connection = this.findConnectionForWidget(clickedWidgetId);
            if (connection) {
                console.log(`🚪 Connection clicked: ${connection.type} to ${connection.to}`);
                this.trackInteraction('connection', clickedWidgetId, { x, y });
                this.useConnection(connection);
            }
            // Reset click state after a short delay
            setTimeout(() => {
                this.state.clickWidgetId = undefined;
            }, 200);
        }
    }
    findConnectionForWidget(widgetId) {
        /** Find connection associated with a widget. */
        for (const connection of this.navigationState.availableConnections) {
            if (connection.widget_id === widgetId) {
                return connection;
            }
        }
        return undefined;
    }
    handleMouseLeave() {
        /** Handle mouse leave events. */
        this.state.hoverWidgetId = undefined;
    }
    handleResize() {
        /** Handle window resize events. */
        // Re-setup canvas dimensions
        this.setupCanvas();
        // Trigger redraw
        this.draw();
    }
    findWidgetAtPosition(x, y) {
        /** Find which widget is at the given position. */
        const { meta } = this.state;
        for (const widget of meta.widgets) {
            // Try click state first, then hover, then idle
            const clickState = this.getWidgetState(widget, 'click');
            const hoverState = this.getWidgetState(widget, 'hover') || this.getWidgetState(widget, 'idle');
            const stateToCheck = clickState || hoverState;
            if (!stateToCheck)
                continue;
            const [bx, by, bw, bh] = stateToCheck.bbox;
            if (x >= bx && x < bx + bw && y >= by && y < by + bh) {
                return widget.id;
            }
        }
        return undefined;
    }
    getWidgetState(widget, stateName) {
        /** Get specific state metadata for a widget. */
        return widget.states.find(s => s.state === stateName);
    }
    startRenderLoop() {
        /** Start the render loop. */
        const render = (currentTime) => {
            // Calculate FPS
            if (this.lastFrameTime > 0) {
                const deltaTime = currentTime - this.lastFrameTime;
                this.performanceMetrics.fps = 1000 / deltaTime;
            }
            this.lastFrameTime = currentTime;
            this.frameCount++;
            // Update navigation state (handle transitions)
            this.updateNavigationState();
            // Draw frame
            this.draw();
            // Continue loop
            this.animationFrameId = requestAnimationFrame(render);
        };
        this.animationFrameId = requestAnimationFrame(render);
        console.log('🎬 Render loop started');
    }
    draw() {
        /** Main draw function. */
        const startTime = performance.now();
        try {
            const { meta, base, overlays } = this.state;
            // Clear canvas
            this.ctx.clearRect(0, 0, this.ctx.canvas.width, this.ctx.canvas.height);
            // Apply transition effect if navigating
            if (this.navigationState.isTransitioning) {
                this.drawTransitionEffect();
            }
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
        }
        catch (error) {
            console.error('❌ Draw error:', error);
        }
        // Update performance metrics
        this.performanceMetrics.renderTime = performance.now() - startTime;
    }
    drawWidgetOverlays(interactionType) {
        /** Draw widget overlays based on interaction state. */
        const { meta, overlays, hoverWidgetId, clickWidgetId } = this.state;
        for (const widget of meta.widgets) {
            const isHovered = widget.id === hoverWidgetId;
            const isClicked = widget.id === clickWidgetId;
            let stateName;
            if (interactionType === 'click' && isClicked) {
                stateName = 'click';
            }
            else if (interactionType === 'hover' && isHovered) {
                stateName = 'hover';
            }
            else {
                stateName = 'idle';
            }
            const state = this.getWidgetState(widget, stateName);
            if (!state)
                continue;
            const overlay = overlays[state.overlay];
            if (!overlay || !overlay.complete)
                continue;
            const [x, y, w, h] = state.bbox;
            // Draw overlay
            this.ctx.drawImage(overlay, x, y, w, h);
            // Draw dynamic text if present
            if (state.render_text) {
                this.drawRenderText(state.render_text, x, y, w, h);
            }
        }
    }
    drawWidgetOverlay(widgetId, stateName) {
        /** Draw specific widget state overlay. */
        const { meta, overlays } = this.state;
        const widget = meta.widgets.find(w => w.id === widgetId);
        if (!widget)
            return;
        const state = this.getWidgetState(widget, stateName);
        if (!state)
            return;
        const overlay = overlays[state.overlay];
        if (!overlay || !overlay.complete)
            return;
        const [x, y, w, h] = state.bbox;
        // Draw overlay
        this.ctx.drawImage(overlay, x, y, w, h);
        // Draw dynamic text if present
        if (state.render_text) {
            this.drawRenderText(state.render_text, x, y, w, h);
        }
    }
    drawRenderText(renderText, x, y, w, h) {
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
            text = window.__GIT_COMMIT_SHORT__ || 'unknown';
        }
        if (renderText.format) {
            const now = new Date();
            const pad = (n) => String(n).padStart(2, '0');
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
    drawDynamicText() {
        /** Draw dynamic text elements (clock, version, etc.). */
        // This can be extended for global dynamic elements
        // Currently handled per-widget in drawRenderText
    }
    drawDebugInfo() {
        /** Draw debug information overlay. */
        this.ctx.save();
        this.ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
        this.ctx.fillRect(10, 10, 220, 120);
        this.ctx.fillStyle = '#00ff00';
        this.ctx.font = '10px monospace';
        this.ctx.textBaseline = 'top';
        const debugInfo = [
            `FPS: ${this.performanceMetrics.fps.toFixed(1)}`,
            `Render: ${this.performanceMetrics.renderTime.toFixed(2)}ms`,
            `Hover: ${this.state.hoverWidgetId || 'none'}`,
            `Click: ${this.state.clickWidgetId || 'none'}`,
            `Assets: ${Object.keys(this.state.overlays).length}`,
            `Nav: ${this.navigationState.currentFloor}/${this.navigationState.currentLocation}`,
            `Transition: ${this.navigationState.isTransitioning ? (this.navigationState.transitionProgress * 100).toFixed(0) + '%' : 'none'}`
        ];
        debugInfo.forEach((line, index) => {
            this.ctx.fillText(line, 15, 15 + index * 12);
        });
        this.ctx.restore();
    }
    drawTransitionEffect() {
        /** Draw transition effect during navigation. */
        const progress = this.navigationState.transitionProgress;
        // Create a fading overlay effect
        this.ctx.save();
        // Fade out current room
        if (progress < 0.5) {
            const fadeProgress = progress * 2; // 0 to 1 during first half
            this.ctx.fillStyle = `rgba(0, 0, 0, ${fadeProgress * 0.8})`;
            this.ctx.fillRect(0, 0, this.ctx.canvas.width, this.ctx.canvas.height);
            // Add transition text
            this.ctx.fillStyle = `rgba(255, 255, 255, ${fadeProgress})`;
            this.ctx.font = 'bold 24px PressStart2P, monospace';
            this.ctx.textAlign = 'center';
            this.ctx.textBaseline = 'middle';
            this.ctx.fillText('Entering new room...', this.ctx.canvas.width / 2, this.ctx.canvas.height / 2);
        }
        // Fade in new room
        else {
            const fadeProgress = (progress - 0.5) * 2; // 0 to 1 during second half
            this.ctx.fillStyle = `rgba(0, 0, 0, ${(1 - fadeProgress) * 0.8})`;
            this.ctx.fillRect(0, 0, this.ctx.canvas.width, this.ctx.canvas.height);
        }
        this.ctx.restore();
    }
    trackInteraction(type, widgetId, position) {
        /** Track user interaction for analytics. */
        const event = {
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
    async changeLocation(floorId, locId) {
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
    async navigateToLocation(floorId, locId) {
        /** Navigate to a location with transition animation. */
        if (!this.worldConfig) {
            console.error('❌ World config not loaded');
            return;
        }
        // Find target location in world config
        const targetFloor = this.worldConfig.floors.find(f => f.id === floorId);
        if (!targetFloor) {
            console.error(`❌ Floor ${floorId} not found`);
            return;
        }
        const targetLocation = targetFloor.locations.find(l => l.id === locId);
        if (!targetLocation) {
            console.error(`❌ Location ${locId} not found in floor ${floorId}`);
            return;
        }
        // Start transition animation
        this.navigationState.isTransitioning = true;
        this.navigationState.targetLocation = { floorId, locationId: locId };
        this.navigationState.transitionStartTime = performance.now();
        this.navigationState.transitionProgress = 0;
        console.log(`🚀 Starting navigation transition to ${floorId}/${locId}`);
        // Track navigation event with connection info
        this.trackInteraction('navigate', undefined, undefined);
    }
    updateNavigationState() {
        /** Update navigation state during transition animation. */
        if (!this.navigationState.isTransitioning || !this.navigationState.targetLocation) {
            return;
        }
        const currentTime = performance.now();
        const elapsed = currentTime - (this.navigationState.transitionStartTime || 0);
        const progress = Math.min(elapsed / this.navigationState.transitionDuration, 1);
        this.navigationState.transitionProgress = progress;
        // Complete transition when finished
        if (progress >= 1) {
            this.completeNavigation();
        }
    }
    async completeNavigation() {
        /** Complete navigation transition and load new location. */
        const target = this.navigationState.targetLocation;
        if (!target)
            return;
        console.log(`✅ Navigation transition complete, loading ${target.floorId}/${target.locationId}`);
        // Reset transition state
        this.navigationState.isTransitioning = false;
        this.navigationState.transitionProgress = 0;
        this.navigationState.targetLocation = undefined;
        // Load new location
        await this.changeLocation(target.floorId, target.locationId);
        // Update navigation connections for new location
        this.updateAvailableConnections();
    }
    updateAvailableConnections() {
        /** Update available connections from current location. */
        if (!this.worldConfig) {
            this.navigationState.availableConnections = [];
            return;
        }
        const currentFloor = this.worldConfig.floors.find(f => f.id === this.state.floorId);
        if (!currentFloor) {
            this.navigationState.availableConnections = [];
            return;
        }
        const currentLocation = currentFloor.locations.find(l => l.id === this.state.locId);
        if (!currentLocation || !currentLocation.connections) {
            this.navigationState.availableConnections = [];
            return;
        }
        this.navigationState.availableConnections = currentLocation.connections;
        console.log(`🔗 Available connections: ${this.navigationState.availableConnections.length} doors/paths`);
    }
    getNavigationState() {
        /** Get current navigation state. */
        return { ...this.navigationState };
    }
    async useConnection(connection) {
        /** Use a connection to navigate to connected location. */
        console.log(`🚪 Using connection: ${connection.type} to ${connection.to}`);
        // Parse target location (format: "floor_id/location_id" or just "location_id" for same floor)
        const parts = connection.to.split('/');
        let targetFloorId, targetLocationId;
        if (parts.length === 2) {
            [targetFloorId, targetLocationId] = parts;
        }
        else {
            // Same floor
            targetFloorId = this.state.floorId;
            targetLocationId = parts[0];
        }
        // Check if connection is bidirectional and validate
        if (connection.bidirectional !== false) {
            // TODO: Validate reverse connection exists
        }
        // Navigate to target location with transition
        await this.navigateToLocation(targetFloorId, targetLocationId);
    }
    setInteractionCallback(callback) {
        /** Set callback for interaction events. */
        this.onInteraction = callback;
    }
    getPerformanceMetrics() {
        /** Get current performance metrics. */
        const cacheStats = assetLoader.getCacheStats();
        this.performanceMetrics.cacheHitRate = cacheStats.cached / Math.max(cacheStats.total, 1);
        return { ...this.performanceMetrics };
    }
    getEventHistory() {
        /** Get interaction event history. */
        return [...this.eventHistory];
    }
    isDebugMode() {
        /** Check if debug mode is enabled. */
        return window.__DEBUG_MODE__ === true;
    }
    destroy() {
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
export async function createWorldRenderer(canvasId, floorId, locId, options) {
    /** Create and initialize a WorldRenderer instance. */
    const renderer = new WorldRenderer(canvasId, options);
    await renderer.initialize(floorId, locId);
    return renderer;
}
//# sourceMappingURL=app.js.map