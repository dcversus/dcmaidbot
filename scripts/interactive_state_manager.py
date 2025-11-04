#!/usr/bin/env python3
"""
Interactive State Management System for PRP-016

Enhances the index.html with improved widget state transitions,
smooth tile swapping, and better interactive feedback.

This script provides the JavaScript code to be injected into index.html
for enhanced interactivity and state management.
"""

import json
from typing import Dict


class InteractiveStateManager:
    """
    Manages interactive state transitions for widgets and tiles.

    This system handles:
    - Smooth state transitions (idle → hover → click)
    - Tile swapping for different widget states
    - Visual feedback and animations
    - Event management and cleanup
    """

    def __init__(self):
        self.widget_states = {}  # Current state of each widget
        self.tile_cache = {}  # Preloaded tile images
        self.transition_timers = {}  # Timers for state transitions
        self.event_listeners = {}  # Event listener cleanup functions

    def generate_enhanced_javascript(self, world_data: Dict) -> str:
        """
        Generate enhanced JavaScript for interactive state management.

        Args:
            world_data: World configuration data

        Returns:
            JavaScript code as string
        """
        js_code = f"""
// ============================================
// ENHANCED INTERACTIVE STATE MANAGEMENT
// ============================================

class EnhancedStateManager {{
    constructor() {{
        this.widgetStates = new Map();
        this.tileCache = new Map();
        this.transitionTimers = new Map();
        this.eventListeners = new Map();
        this.loadingTiles = new Set();

        // Configuration from world data
        this.worldData = {json.dumps(world_data)};
        this.locations = this.worldData.locations || [];

        console.log('🎮 EnhancedStateManager initialized');
        this.preloadAllTiles();
        this.setupGlobalEventListeners();
    }}

    // Preload all tile images for smooth transitions
    async preloadAllTiles() {{
        console.log('🔄 Preloading all interactive tile states...');

        for (const location of this.locations) {{
            const locationId = location.id;
            console.log(`📦 Preloading tiles for ${{locationId}}`);

            // Find all widgets in this location
            for (const widget of location.widgets || []) {{
                const widgetId = widget.id;

                // Preload all states for this widget
                const states = ['idle', 'hover', 'click'];
                for (const state of states) {{
                    const tileKey = `${{locationId}}_${{widgetId}}_${{state}}`;

                    // Check if tile files exist
                    const tilePaths = this.findTilePaths(locationId, widgetId, state);
                    if (tilePaths.length > 0) {{
                        this.preloadTile(tileKey, tilePaths[0]);
                    }}
                }}
            }}
        }}

        console.log('✅ Tile preloading completed');
    }}

    // Find tile file paths for a specific widget and state
    findTilePaths(locationId, widgetId, state) {{
        const paths = [];

        // Look for individual widget tiles
        for (let x = 0; x < 4; x++) {{
            for (let y = 0; y < 4; y++) {{
                const tilePath = `static/world/${{locationId}}/tile_${{state}}_${{x}}_${{y}}.png`;
                paths.push(tilePath);
            }}
        }}

        return paths;
    }}

    // Preload a single tile image
    async preloadTile(tileKey, tilePath) {{
        return new Promise((resolve, reject) => {{
            const img = new Image();
            img.onload = () => {{
                this.tileCache.set(tileKey, {{
                    path: tilePath,
                    image: img,
                    loaded: true,
                    timestamp: Date.now()
                }});
                resolve(img);
            }};
            img.onerror = () => {{
                console.warn(`⚠️  Failed to load tile: ${{tilePath}}`);
                resolve(null);
            }};
            img.src = tilePath;
        }});
    }}

    // Get cached tile for a widget state
    getCachedTile(locationId, widgetId, state) {{
        const tileKey = `${{locationId}}_${{widgetId}}_${{state}}`;
        const cached = this.tileCache.get(tileKey);

        if (cached && cached.loaded) {{
            return cached;
        }}

        return null;
    }}

    // Setup global event listeners
    setupGlobalEventListeners() {{
        // Handle keyboard navigation
        document.addEventListener('keydown', (e) => {{
            if (e.key === 'Escape') {{
                this.closeAllModals();
            }}
        }});

        // Handle window resize
        window.addEventListener('resize', () => {{
            this.debounce(this.handleResize.bind(this), 250);
        }});

        // Handle visibility change (tab switching)
        document.addEventListener('visibilitychange', () => {{
            if (document.hidden) {{
                this.pauseAnimations();
            }} else {{
                this.resumeAnimations();
            }}
        }});
    }}

    // Enhanced widget state transition
    transitionWidgetState(locationId, widgetId, newState, callback = null) {{
        console.log(`🔄 Transitioning widget ${{widgetId}} to ${{newState}}`);

        // Cancel any existing transition timer
        const timerKey = `${{locationId}}_${{widgetId}}`;
        if (this.transitionTimers.has(timerKey)) {{
            clearTimeout(this.transitionTimers.get(timerKey));
        }}

        // Get current state
        const currentState = this.widgetStates.get(timerKey) || 'idle';
        if (currentState === newState) {{
            if (callback) callback();
            return;
        }}

        // Get cached tiles
        const currentTile = this.getCachedTile(locationId, widgetId, currentState);
        const newTile = this.getCachedTile(locationId, widgetId, newState);

        if (!newTile) {{
            console.warn(`⚠️  No cached tile for ${{locationId}}_${{widgetId}}_${{newState}}`);
            if (callback) callback();
            return;
        }}

        // Perform smooth transition
        this.performTileTransition(locationId, widgetId, currentState, newState, callback);

        // Update state
        this.widgetStates.set(timerKey, newState);
    }}

    // Perform smooth tile transition with animations
    performTileTransition(locationId, widgetId, fromState, toState, callback = null) {{
        const widgetElements = document.querySelectorAll(`[data-widget-id="${{widgetId}}"][data-location-id="${{locationId}}"]`);

        widgetElements.forEach(element => {{
            const tileElement = element.querySelector('.widget-tile') || element;

            // Add transition classes
            tileElement.classList.add('state-transitioning');
            tileElement.classList.add(`state-${{fromState}}-to-${{toState}}`);

            // Play transition sound
            this.playTransitionSound(toState);

            // Apply visual effects
            this.applyTransitionEffects(tileElement, toState);

            // Update tile image after a short delay for smooth transition
            const timerKey = `${{locationId}}_${{widgetId}}`;
            const timer = setTimeout(() => {{
                // Update tile image
                this.updateWidgetTile(tileElement, locationId, widgetId, toState);

                // Remove transition classes after animation
                setTimeout(() => {{
                    tileElement.classList.remove('state-transitioning');
                    tileElement.classList.remove(`state-${{fromState}}-to-${{toState}}`);
                    tileElement.classList.remove('state-idle', 'state-hover', 'state-click');
                    tileElement.classList.add(`state-${{toState}}`);

                    if (callback) callback();
                }}, 150);
            }}, 50);

            this.transitionTimers.set(timerKey, timer);
        }});
    }}

    // Update widget tile image
    updateWidgetTile(element, locationId, widgetId, state) {{
        const cachedTile = this.getCachedTile(locationId, widgetId, state);
        if (cachedTile && cachedTile.image) {{
            const tileElement = element.querySelector('.widget-tile') || element;

            // Apply image with fade effect
            tileElement.style.opacity = '0.7';
            setTimeout(() => {{
                if (tileElement.tagName === 'IMG') {{
                    tileElement.src = cachedTile.path;
                }} else {{
                    tileElement.style.backgroundImage = `url(${{cachedTile.path}})`;
                    tileElement.style.backgroundSize = 'cover';
                    tileElement.style.backgroundPosition = 'center';
                }}
                tileElement.style.opacity = '1';
            }}, 100);
        }}
    }}

    // Apply visual transition effects
    applyTransitionEffects(element, state) {{
        // Remove all effect classes
        element.classList.remove('effect-glow', 'effect-pulse', 'effect-shake');

        switch (state) {{
            case 'hover':
                element.classList.add('effect-glow');
                break;
            case 'click':
                element.classList.add('effect-pulse');
                // Add subtle shake effect
                setTimeout(() => {{
                    element.classList.add('effect-shake');
                    setTimeout(() => {{
                        element.classList.remove('effect-shake');
                    }}, 300);
                }}, 100);
                break;
        }}
    }}

    // Play transition sound effects
    playTransitionSound(state) {{
        if (!window.worldManager || !window.worldManager.audioManager) {{
            return;
        }}

        switch (state) {{
            case 'hover':
                window.worldManager.audioManager.playHover();
                break;
            case 'click':
                window.worldManager.audioManager.playClick();
                break;
            case 'idle':
                // Optional: play subtle return sound
                break;
        }}
    }}

    // Setup widget event listeners
    setupWidgetEventListeners(locationId, widgetId, widgetElement) {{
        const eventKey = `${{locationId}}_${{widgetId}}`;

        // Remove existing listeners for this widget
        if (this.eventListeners.has(eventKey)) {{
            const listeners = this.eventListeners.get(eventKey);
            listeners.forEach(listener => {{
                listener.element.removeEventListener(listener.event, listener.handler);
            }});
        }}

        const listeners = [];

        // Mouse enter (hover)
        const mouseEnterHandler = (e) => {{
            e.preventDefault();
            this.transitionWidgetState(locationId, widgetId, 'hover');
        }};
        widgetElement.addEventListener('mouseenter', mouseEnterHandler);
        listeners.push({{ element: widgetElement, event: 'mouseenter', handler: mouseEnterHandler }});

        // Mouse leave (return to idle)
        const mouseLeaveHandler = (e) => {{
            e.preventDefault();
            this.transitionWidgetState(locationId, widgetId, 'idle');
        }};
        widgetElement.addEventListener('mouseleave', mouseLeaveHandler);
        listeners.push({{ element: widgetElement, event: 'mouseleave', handler: mouseLeaveHandler }});

        // Mouse click
        const clickHandler = (e) => {{
            e.preventDefault();
            this.transitionWidgetState(locationId, widgetId, 'click');

            // Return to hover after click animation
            setTimeout(() => {{
                this.transitionWidgetState(locationId, widgetId, 'hover');
            }}, 500);
        }};
        widgetElement.addEventListener('click', clickHandler);
        listeners.push({{ element: widgetElement, event: 'click', handler: clickHandler }});

        // Touch support for mobile
        const touchStartHandler = (e) => {{
            e.preventDefault();
            this.transitionWidgetState(locationId, widgetId, 'hover');
        }};
        widgetElement.addEventListener('touchstart', touchStartHandler);
        listeners.push({{ element: widgetElement, event: 'touchstart', handler: touchStartHandler }});

        const touchEndHandler = (e) => {{
            e.preventDefault();
            this.transitionWidgetState(locationId, widgetId, 'click');

            setTimeout(() => {{
                this.transitionWidgetState(locationId, widgetId, 'hover');
            }}, 500);
        }};
        widgetElement.addEventListener('touchend', touchEndHandler);
        listeners.push({{ element: widgetElement, event: 'touchend', handler: touchEndHandler }});

        // Store listeners for cleanup
        this.eventListeners.set(eventKey, listeners);
    }}

    // Debounce function for resize handling
    debounce(func, wait) {{
        let timeout;
        return function executedFunction(...args) {{
            const later = () => {{
                clearTimeout(timeout);
                func(...args);
            }};
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        }};
    }}

    // Handle window resize
    handleResize() {{
        console.log('📐 Handling window resize');
        // Recalculate positions and update tile displays
        this.updateAllWidgetDisplays();
    }}

    // Update all widget displays
    updateAllWidgetDisplays() {{
        for (const [key, state] of this.widgetStates) {{
            const [locationId, widgetId] = key.split('_');
            const widgetElements = document.querySelectorAll(`[data-widget-id="${{widgetId}}"][data-location-id="${{locationId}}"]`);

            widgetElements.forEach(element => {{
                this.updateWidgetTile(element, locationId, widgetId, state);
            }});
        }}
    }}

    // Pause animations when page is hidden
    pauseAnimations() {{
        console.log('⏸️ Pausing animations');
        document.querySelectorAll('.effect-glow, .effect-pulse').forEach(el => {{
            el.style.animationPlayState = 'paused';
        }});
    }}

    // Resume animations when page is visible
    resumeAnimations() {{
        console.log('▶️ Resuming animations');
        document.querySelectorAll('.effect-glow, .effect-pulse').forEach(el => {{
            el.style.animationPlayState = 'running';
        }});
    }}

    // Close all modals
    closeAllModals() {{
        const modals = document.querySelectorAll('.modal-overlay');
        modals.forEach(modal => {{
            if (modal.style.display !== 'none') {{
                modal.style.display = 'none';
            }}
        }});
    }}

    // Cleanup method
    cleanup() {{
        console.log('🧹 Cleaning up EnhancedStateManager');

        // Clear all timers
        for (const timer of this.transitionTimers.values()) {{
            clearTimeout(timer);
        }}
        this.transitionTimers.clear();

        // Remove all event listeners
        for (const [key, listeners] of this.eventListeners) {{
            listeners.forEach(listener => {{
                listener.element.removeEventListener(listener.event, listener.handler);
            }});
        }}
        this.eventListeners.clear();

        // Clear caches
        this.tileCache.clear();
        this.widgetStates.clear();
    }}

    // Get current state for debugging
    getCurrentState(locationId, widgetId) {{
        return this.widgetStates.get(`${{locationId}}_${{widgetId}}`) || 'idle';
    }}

    // Debug method to list all loaded tiles
    listLoadedTiles() {{
        console.log('📋 Loaded tiles:');
        for (const [key, tile] of this.tileCache) {{
            console.log(`  ${{key}}: ${{tile.path}} (${{tile.loaded ? 'loaded' : 'failed'}})`);
        }}
    }}
}}

// Enhanced CSS for state transitions
const enhancedCSS = `
.state-transitioning {{
    transition: all 0.2s ease-in-out;
}}

.state-idle-to-hover {{
    filter: brightness(1.1) saturate(1.2);
}}

.state-hover-to-click {{
    filter: brightness(1.2) saturate(1.3);
}}

.state-click-to-hover {{
    filter: brightness(1.1) saturate(1.2);
}}

.state-hover-to-idle {{
    filter: brightness(1.0) saturate(1.0);
}}

.effect-glow {{
    box-shadow: 0 0 20px rgba(100, 200, 255, 0.5);
    animation: glow 2s ease-in-out infinite;
}}

.effect-pulse {{
    animation: pulse 0.5s ease-in-out;
}}

.effect-shake {{
    animation: shake 0.3s ease-in-out;
}}

@keyframes glow {{
    0%, 100% {{ opacity: 0.8; }}
    50% {{ opacity: 1; }}
}}

@keyframes pulse {{
    0% {{ transform: scale(1); }}
    50% {{ transform: scale(1.05); }}
    100% {{ transform: scale(1); }}
}}

@keyframes shake {{
    0%, 100% {{ transform: translateX(0); }}
    25% {{ transform: translateX(-2px); }}
    75% {{ transform: translateX(2px); }}
}}

.widget-tile {{
    transition: opacity 0.1s ease-in-out;
}}
`;

// Inject enhanced CSS
const styleSheet = document.createElement('style');
styleSheet.textContent = enhancedCSS;
document.head.appendChild(styleSheet);

// Initialize the enhanced state manager
window.enhancedStateManager = new EnhancedStateManager();

console.log('🎮 Enhanced state management system loaded');
"""
        return js_code

    def generate_enhanced_integration_code(self) -> str:
        """
        Generate code to integrate enhanced state management with existing widgets.

        Returns:
            JavaScript integration code
        """
        return """
// ============================================
// ENHANCED WIDGET INTEGRATION
// ============================================

// Patch existing widget creation to use enhanced state management
if (window.worldManager && window.worldManager.widgetManager) {
    const originalCreateWidget = window.worldManager.widgetManager.createWidget;

    window.worldManager.widgetManager.createWidget = function(config, locationId, x, y) {
        console.log('🎨 Creating enhanced widget with ID:', config.id);

        // Create the widget using original method
        const widget = originalCreateWidget.call(this, config, locationId, x, y);

        // Wait for widget to be rendered, then enhance it
        setTimeout(() => {
            const widgetElement = document.querySelector(`[data-widget-id="${config.id}"][data-location-id="${locationId}"]`);
            if (widgetElement && window.enhancedStateManager) {
                console.log(`🔄 Enhancing widget ${config.id}`);

                // Add data attributes for enhanced state management
                widgetElement.setAttribute('data-widget-id', config.id);
                widgetElement.setAttribute('data-location-id', locationId);
                widgetElement.setAttribute('data-widget-type', config.type);

                // Setup enhanced event listeners
                window.enhancedStateManager.setupWidgetEventListeners(locationId, config.id, widgetElement);

                // Initialize widget state
                window.enhancedStateManager.widgetStates.set(`${locationId}_${config.id}`, 'idle');
                widgetElement.classList.add('state-idle');
            }
        }, 100);

        return widget;
    };

    console.log('✅ Enhanced widget integration active');
} else {
    console.warn('⚠️  Widget manager not found, enhanced integration skipped');
}

// Make enhanced state manager globally available
window.debugStateManagement = function() {
    if (window.enhancedStateManager) {
        console.log('🔍 Enhanced State Manager Debug Info:');
        window.enhancedStateManager.listLoadedTiles();
        console.log('Widget states:', Array.from(window.enhancedStateManager.widgetStates.entries()));
        console.log('Active timers:', window.enhancedStateManager.transitionTimers.size);
    } else {
        console.warn('Enhanced state manager not initialized');
    }
};

// Global function to manually trigger state transitions
window.triggerWidgetState = function(locationId, widgetId, state) {
    if (window.enhancedStateManager) {
        window.enhancedStateManager.transitionWidgetState(locationId, widgetId, state);
    } else {
        console.warn('Enhanced state manager not initialized');
    }
};

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.enhancedStateManager) {
        window.enhancedStateManager.cleanup();
    }
});

console.log('🎮 Enhanced state management integration complete');
"""

    def generate_complete_script(self, world_data: Dict) -> str:
        """
        Generate complete JavaScript code for enhanced state management.

        Args:
            world_data: World configuration data

        Returns:
            Complete JavaScript code as string
        """
        state_manager_js = self.generate_enhanced_javascript(world_data)
        integration_js = self.generate_enhanced_integration_code()

        return f"""
// ============================================
// ENHANCED INTERACTIVE STATE MANAGEMENT
// Generated by InteractiveStateManager
// ============================================

{state_manager_js}

{integration_js}
"""


def main():
    """Generate the enhanced state management JavaScript."""
    print("🎮 Generating Enhanced Interactive State Management System")
    print("=" * 60)

    # Load world data
    try:
        with open("static/world.json", "r") as f:
            world_data = json.load(f)
        print("✅ Loaded world.json")
    except Exception as e:
        print(f"❌ Failed to load world.json: {e}")
        return

    # Create state manager
    state_manager = InteractiveStateManager()

    # Generate JavaScript code
    js_code = state_manager.generate_complete_script(world_data)

    # Save to file
    output_file = "static/enhanced_state_management.js"
    with open(output_file, "w") as f:
        f.write(js_code)

    print(f"✅ Generated enhanced state management script: {output_file}")
    print(f"   📊 Worlds: {len(world_data.get('locations', []))} locations")

    # Count widgets
    total_widgets = sum(
        len(loc.get("widgets", [])) for loc in world_data.get("locations", [])
    )
    print(f"   🎯 Widgets: {total_widgets} total widgets")

    print("\n📝 To integrate with index.html:")
    print(f'   Add to index.html: <script src="{output_file}"></script>')
    print("   Or inject the code directly into a <script> tag")


if __name__ == "__main__":
    main()
