import type { MapMeta, AppState, WidgetMeta, WidgetStateMeta } from './types';
import { loadWorld, loadMeta, loadImage } from './loader';

// Retro color palette (DB32-inspired)
const RETRO_COLORS = {
  bg: '#0a0a0a',
  primary: '#9ad1ff',
  secondary: '#ffd37f',
  accent: '#ff6b9d',
  text: '#e8e8e8',
  border: '#404040',
  floorIndicator: '#6bcb77',
  locationBg: '#1a1a2e',
  panelBg: 'rgba(26, 26, 46, 0.95)'
};

class RetroGameInterface {
  private canvas: HTMLCanvasElement;
  private ctx: CanvasRenderingContext2D;
  private appState: AppState;
  private floorIndicators: Map<string, HTMLElement> = new Map();
  private locationPanels: Map<string, HTMLElement> = new Map();
  private overlayPanels: Map<string, HTMLElement> = new Map();
  private widgetStates: Map<string, string> = new Map();
  private animationFrame: number = 0;
  private isScrolling: boolean = false;
  private currentFloorValue: number = 2; // Start on floor 2

  constructor() {
    this.canvas = document.getElementById('c') as HTMLCanvasElement;
    if (!this.canvas) throw new Error('Canvas not found');

    this.ctx = this.canvas.getContext('2d')!;
    this.appState = {
      floorId: '',
      locId: '',
      base: new Image(),
      overlays: {},
      meta: { W: 1280, H: 768, tile: 64, widgets: [] },
      worldConfig: null
    };

    this.init();
  }

  private async init() {
    this.setupCanvas();
    this.createRetroUI();
    await this.loadWorld();
    this.startGameLoop();
    this.setupEventListeners();
  }

  private setupCanvas() {
    // Set canvas size to match world
    this.canvas.width = 1280;
    this.canvas.height = 768;

    // Enable crisp pixel rendering
    this.ctx.imageSmoothingEnabled = false;

    // Set dark background
    this.canvas.style.background = RETRO_COLORS.bg;
    this.canvas.style.border = `2px solid ${RETRO_COLORS.border}`;
  }

  private createRetroUI() {
    // Create floor changer
    this.createFloorChanger();

    // Create overlay panel container
    this.createOverlayContainer();

    // Apply retro styling
    document.body.style.background = RETRO_COLORS.bg;
    document.body.style.color = RETRO_COLORS.text;
    document.body.style.fontFamily = '"Press Start 2P", monospace';
    document.body.style.fontSize = '12px';
    document.body.style.margin = '0';
    document.body.style.padding = '20px';
    document.body.style.overflow = 'hidden';
  }

  private createFloorChanger() {
    const floorChanger = document.createElement('div');
    floorChanger.id = 'floor-changer';
    floorChanger.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: ${RETRO_COLORS.panelBg};
      border: 2px solid ${RETRO_COLORS.border};
      padding: 15px;
      border-radius: 8px;
      z-index: 1000;
      min-width: 200px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.8);
    `;

    const title = document.createElement('div');
    title.textContent = 'FLOOR';
    title.style.cssText = `
      color: ${RETRO_COLORS.secondary};
      font-size: 10px;
      margin-bottom: 10px;
      text-align: center;
      border-bottom: 1px solid ${RETRO_COLORS.border};
      padding-bottom: 5px;
    `;

    floorChanger.appendChild(title);

    // Create floor indicators for each floor
    const floors = ['B1', '1F', '2F', 'F1', 'F2', 'F3', 'F4', 'F5'];
    floors.forEach(floor => {
      const indicator = document.createElement('div');
      indicator.id = `floor-${floor}`;
      indicator.textContent = floor;
      indicator.style.cssText = `
        padding: 8px 12px;
        margin: 2px 0;
        background: ${RETRO_COLORS.locationBg};
        border: 1px solid ${RETRO_COLORS.border};
        color: ${RETRO_COLORS.text};
        cursor: pointer;
        transition: all 0.2s;
        text-align: center;
        font-size: 10px;
      `;

      indicator.addEventListener('click', () => {
        this.selectFloor(floor);
      });

      indicator.addEventListener('mouseenter', () => {
        indicator.style.background = RETRO_COLORS.primary;
        indicator.style.color = RETRO_COLORS.bg;
      });

      indicator.addEventListener('mouseleave', () => {
        if (!indicator.classList.contains('active')) {
          indicator.style.background = RETRO_COLORS.locationBg;
          indicator.style.color = RETRO_COLORS.text;
        }
      });

      floorChanger.appendChild(indicator);
      this.floorIndicators.set(floor, indicator);
    });

    document.body.appendChild(floorChanger);
  }

  private createOverlayContainer() {
    const overlayContainer = document.createElement('div');
    overlayContainer.id = 'overlay-container';
    overlayContainer.style.cssText = `
      position: fixed;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      z-index: 2000;
      pointer-events: none;
    `;
    document.body.appendChild(overlayContainer);
  }

  private selectFloor(floor: string) {
    // Clear all active states
    this.floorIndicators.forEach(indicator => {
      indicator.classList.remove('active');
      indicator.style.background = RETRO_COLORS.locationBg;
      indicator.style.color = RETRO_COLORS.text;
    });

    // Set active floor
    const activeIndicator = this.floorIndicators.get(floor);
    if (activeIndicator) {
      activeIndicator.classList.add('active');
      activeIndicator.style.background = RETRO_COLORS.floorIndicator;
      activeIndicator.style.color = RETRO_COLORS.bg;
    }

    // Update current floor value
    const floorMap: Record<string, number> = {
      'B1': -1, '1F': 1, '2F': 2, 'F1': 1, 'F2': 2,
      'F3': 3, 'F4': 4, 'F5': 5
    };
    this.currentFloorValue = floorMap[floor] || 2;

    // Navigate to floor (placeholder - will connect to world navigation)
    this.navigateToFloor(floor);
  }

  private navigateToFloor(floor: string) {
    // TODO: Implement actual floor navigation based on world sequence
    console.log(`Navigating to floor: ${floor}`);

    // For now, just update the display
    this.updateLocationDisplay(floor);
  }

  private updateLocationDisplay(floor: string) {
    // Update location indicator in floor changer
    const activeIndicator = this.floorIndicators.get(floor);
    if (activeIndicator) {
      // Add current location indicator
      let locationText = floor;
      if (this.appState.locId) {
        const locationName = this.appState.locId.replace(/_/g, ' ').toUpperCase();
        locationText = `${floor} - ${locationName}`;
      }

      // Update indicator text to show current location
      activeIndicator.innerHTML = locationText.split('<br>').join('<br>');
      activeIndicator.style.fontSize = '9px';
    }
  }

  private async loadWorld() {
    try {
      const worldData = await loadWorld();
      this.appState.worldConfig = worldData;

      // Load first location
      const firstLocation = worldData.sequence[0];
      await this.loadLocation(firstLocation);

      // Set initial floor indicator
      this.selectFloor('2F');
    } catch (error) {
      console.error('Failed to load world:', error);
    }
  }

  private async loadLocation(locationId: string) {
    try {
      // Find location in world data
      let locationData = null;
      let floorId = '';

      for (const floor of this.appState.worldConfig?.floors || []) {
        const location = floor.locations.find((loc: any) => loc.id === locationId);
        if (location) {
          locationData = location;
          floorId = floor.id;
          break;
        }
      }

      if (!locationData) {
        console.error(`Location ${locationId} not found`);
        return;
      }

      // Load base image
      const baseUrl = `/output/floors/${floorId}/${locationId}/base.png`;
      this.appState.base = await loadImage(baseUrl);

      // Load metadata
      const meta = await loadMeta(floorId, locationId);
      this.appState.meta = meta;
      this.appState.floorId = floorId;
      this.appState.locId = locationId;

      // Load widget overlays
      this.appState.overlays = {};
      for (const widget of meta.widgets) {
        for (const state of widget.states) {
          const overlayUrl = `/output/floors/${floorId}/${locationId}/overlays/${widget.id}__${state.state}.png`;
          try {
            this.appState.overlays[`${widget.id}_${state.state}`] = await loadImage(overlayUrl);
          } catch (error) {
            console.warn(`Failed to load overlay: ${overlayUrl}`);
          }
        }

        // Initialize widget state
        this.widgetStates.set(widget.id, 'idle');
      }

      // Update location display
      this.updateLocationDisplay('2F'); // Will update based on actual floor mapping

    } catch (error) {
      console.error('Failed to load location:', error);
    }
  }

  private setupEventListeners() {
    this.canvas.addEventListener('click', (e) => this.handleClick(e));

    // Handle scroll for floor navigation (if implemented)
    document.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
        this.handleFloorNavigation(e.key === 'ArrowRight' ? 1 : -1);
      }
    });
  }

  private handleFloorNavigation(direction: number) {
    const floors = ['B1', '1F', '2F', 'F1', 'F2', 'F3', 'F4', 'F5'];
    const currentIndex = floors.findIndex(floor =>
      this.floorIndicators.get(floor)?.classList.contains('active')
    );

    if (currentIndex !== -1) {
      const newIndex = Math.max(0, Math.min(floors.length - 1, currentIndex + direction));
      this.selectFloor(floors[newIndex]);
    }
  }

  private handleClick(event: MouseEvent) {
    const rect = this.canvas.getBoundingClientRect();
    const x = (event.clientX - rect.left) * (this.canvas.width / rect.width);
    const y = (event.clientY - rect.top) * (this.canvas.height / rect.height);

    // Check which widget was clicked
    for (const widget of this.appState.meta.widgets) {
      const bbox = widget.states.find(s => s.state === 'idle')?.bbox;
      if (bbox && x >= bbox[0] && x < bbox[0] + bbox[2] &&
          y >= bbox[1] && y < bbox[1] + bbox[3]) {
        this.handleWidgetClick(widget.id);
        break;
      }
    }
  }

  private handleWidgetClick(widgetId: string) {
    const currentState = this.widgetStates.get(widgetId) || 'idle';
    const widget = this.appState.meta.widgets.find(w => w.id === widgetId);

    if (!widget) return;

    // Handle different widget types
    switch (widget.id) {
      case 'digital_clock':
        this.handleDigitalClockClick();
        break;
      case 'changelog_book':
        this.handleChangelogBookClick();
        break;
      case 'cactus_plant':
        this.handleCactusPlantClick();
        break;
      case 'commit_badge':
        this.handleCommitBadgeClick();
        break;
      default:
        // Generic widget behavior
        this.handleGenericWidgetClick(widgetId, currentState);
    }
  }

  private handleDigitalClockClick() {
    // Toggle clock states: idle -> hover -> click -> idle
    const states = ['idle', 'hover', 'click'];
    const currentState = this.widgetStates.get('digital_clock') || 'idle';
    const currentIndex = states.indexOf(currentState);
    const nextState = states[(currentIndex + 1) % states.length];

    this.widgetStates.set('digital_clock', nextState);
    console.log(`Digital clock state: ${nextState}`);
  }

  private handleChangelogBookClick() {
    // Show changelog overlay panel
    this.showOverlayPanel('changelog_book', 'md', 'https://raw.githubusercontent.com/dcversus/dcmaidbot/main/CHANGELOG.md');
  }

  private handleCactusPlantClick() {
    // Toggle cactus growth state
    const currentState = this.widgetStates.get('cactus_plant') || 'idle-small';
    const states = ['idle-small', 'click-small', 'idle-medium', 'click-medium', 'idle-large', 'click-large'];
    const currentIndex = states.indexOf(currentState);
    const nextState = states[(currentIndex + 1) % states.length];

    this.widgetStates.set('cactus_plant', nextState);
    console.log(`Cactus plant state: ${nextState}`);
  }

  private handleCommitBadgeClick() {
    // Toggle commit badge display
    const currentState = this.widgetStates.get('commit_badge') || 'idle';
    const nextState = currentState === 'idle' ? 'hover' : 'idle';

    this.widgetStates.set('commit_badge', nextState);
    console.log(`Commit badge state: ${nextState}`);
  }

  private handleGenericWidgetClick(widgetId: string, currentState: string) {
    // Generic state cycling for unknown widgets
    const widget = this.appState.meta.widgets.find(w => w.id === widgetId);
    if (!widget) return;

    const states = widget.states.map(s => s.state);
    const currentIndex = states.indexOf(currentState);
    const nextState = states[(currentIndex + 1) % states.length];

    this.widgetStates.set(widgetId, nextState);
    console.log(`${widgetId} state: ${nextState}`);
  }

  private showOverlayPanel(widgetId: string, type: 'text' | 'md' | 'link', content: string) {
    // Remove existing panel
    this.hideOverlayPanel();

    const panel = document.createElement('div');
    panel.id = `overlay-${widgetId}`;
    panel.style.cssText = `
      background: ${RETRO_COLORS.panelBg};
      border: 3px solid ${RETRO_COLORS.primary};
      border-radius: 12px;
      padding: 20px;
      max-width: 800px;
      max-height: 600px;
      overflow-y: auto;
      pointer-events: auto;
      box-shadow: 0 8px 32px rgba(0,0,0,0.9);
      animation: slideIn 0.3s ease-out;
    `;

    // Add close button
    const closeBtn = document.createElement('button');
    closeBtn.textContent = 'X';
    closeBtn.style.cssText = `
      position: absolute;
      top: 10px;
      right: 10px;
      background: ${RETRO_COLORS.accent};
      color: white;
      border: none;
      width: 30px;
      height: 30px;
      border-radius: 50%;
      cursor: pointer;
      font-family: 'Press Start 2P', monospace;
      font-size: 12px;
    `;
    closeBtn.addEventListener('click', () => this.hideOverlayPanel());
    panel.appendChild(closeBtn);

    // Add content based on type
    if (type === 'md') {
      this.loadMarkdownContent(panel, content);
    } else if (type === 'link') {
      this.loadLinkContent(panel, content);
    } else {
      panel.innerHTML += `<div style="color: ${RETRO_COLORS.text}; font-size: 12px; line-height: 1.6;">${content}</div>`;
    }

    // Position panel
    const overlayContainer = document.getElementById('overlay-container')!;
    overlayContainer.appendChild(panel);
    overlayContainer.style.pointerEvents = 'auto';

    this.overlayPanels.set(widgetId, panel);
  }

  private async loadMarkdownContent(panel: HTMLElement, url: string) {
    try {
      const response = await fetch(url);
      const text = await response.text();

      // Simple markdown parsing (basic)
      const html = this.parseMarkdown(text);
      const content = document.createElement('div');
      content.innerHTML = html;
      content.style.cssText = `
        color: ${RETRO_COLORS.text};
        font-size: 11px;
        line-height: 1.6;
        white-space: pre-wrap;
        margin-top: 40px;
      `;

      panel.appendChild(content);
    } catch (error) {
      console.error('Failed to load markdown:', error);
      panel.innerHTML += `<div style="color: ${RETRO_COLORS.accent};">Failed to load content</div>`;
    }
  }

  private parseMarkdown(text: string): string {
    // Very basic markdown parsing
    return text
      .split('\n')
      .map(line => {
        if (line.startsWith('## ')) {
          return `<h3 style="color: ${RETRO_COLORS.primary}; margin: 15px 0 10px 0; font-size: 14px;">${line.slice(3)}</h3>`;
        } else if (line.startsWith('# ')) {
          return `<h2 style="color: ${RETRO_COLORS.secondary}; margin: 20px 0 15px 0; font-size: 16px;">${line.slice(2)}</h2>`;
        } else if (line.startsWith('- ')) {
          return `<li style="margin: 5px 0; list-style-position: inside;">${line.slice(2)}</li>`;
        } else if (line.trim() === '') {
          return '<br>';
        } else {
          return `<div style="margin: 5px 0;">${line}</div>`;
        }
      })
      .join('');
  }

  private loadLinkContent(panel: HTMLElement, url: string) {
    const content = document.createElement('div');
    content.innerHTML = `
      <div style="color: ${RETRO_COLORS.secondary}; margin: 40px 0 20px 0; font-size: 14px;">
        External Link
      </div>
      <div style="margin: 20px 0;">
        <a href="${url}" target="_blank" style="
          color: ${RETRO_COLORS.primary};
          text-decoration: none;
          border: 2px solid ${RETRO_COLORS.primary};
          padding: 10px 20px;
          display: inline-block;
          border-radius: 8px;
          font-size: 12px;
          transition: all 0.2s;
        " onmouseover="this.style.background='${RETRO_COLORS.primary}'; this.style.color='${RETRO_COLORS.bg}'"
           onmouseout="this.style.background='transparent'; this.style.color='${RETRO_COLORS.primary}'">
          OPEN EXTERNAL LINK →
        </a>
      </div>
      <div style="color: ${RETRO_COLORS.text}; font-size: 10px; opacity: 0.7;">
        ${url}
      </div>
    `;
    panel.appendChild(content);
  }

  private hideOverlayPanel() {
    const overlayContainer = document.getElementById('overlay-container')!;
    overlayContainer.innerHTML = '';
    overlayContainer.style.pointerEvents = 'none';
    this.overlayPanels.clear();
  }

  private startGameLoop() {
    const gameLoop = () => {
      this.render();
      this.updateWidgets();
      this.animationFrame = requestAnimationFrame(gameLoop);
    };
    gameLoop();
  }

  private render() {
    // Clear canvas
    this.ctx.fillStyle = RETRO_COLORS.bg;
    this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

    // Draw base image
    if (this.appState.base.complete) {
      this.ctx.drawImage(this.appState.base, 0, 0);
    }

    // Draw widget overlays based on current states
    for (const [widgetId, state] of this.widgetStates) {
      const overlay = this.appState.overlays[`${widgetId}_${state}`];
      if (overlay && overlay.complete) {
        const widget = this.appState.meta.widgets.find(w => w.id === widgetId);
        const bbox = widget?.states.find(s => s.state === state)?.bbox;
        if (bbox) {
          this.ctx.drawImage(overlay, bbox[0], bbox[1]);
        }
      }
    }

    // Draw dynamic text overlays
    this.drawTextOverlays();
  }

  private drawTextOverlays() {
    this.ctx.save();
    this.ctx.font = '"Press Start 2P", monospace';
    this.ctx.textAlign = 'center';
    this.ctx.textBaseline = 'middle';

    // Digital clock time
    const clockState = this.widgetStates.get('digital_clock');
    if (clockState && clockState !== 'idle') {
      const widget = this.appState.meta.widgets.find(w => w.id === 'digital_clock');
      const bbox = widget?.states.find(s => s.state === clockState)?.bbox;
      const renderText = widget?.states.find(s => s.state === clockState)?.render_text;

      if (bbox && renderText) {
        this.ctx.fillStyle = renderText.color || RETRO_COLORS.primary;
        this.ctx.font = `${renderText.font_size || 12}px "${renderText.font || 'Press Start 2P'}", monospace`;

        const timeStr = this.getCurrentTime(renderText.format || 'HH:mm');
        this.ctx.fillText(timeStr, bbox[0] + bbox[2]/2, bbox[1] + bbox[3]/2);
      }
    }

    // Commit badge text
    const badgeState = this.widgetStates.get('commit_badge');
    if (badgeState && badgeState !== 'idle') {
      const widget = this.appState.meta.widgets.find(w => w.id === 'commit_badge');
      const bbox = widget?.states.find(s => s.state === badgeState)?.bbox;
      const renderText = widget?.states.find(s => s.state === badgeState)?.render_text;

      if (bbox && renderText) {
        this.ctx.fillStyle = renderText.color || RETRO_COLORS.secondary;
        this.ctx.font = `${renderText.font_size || 10}px "${renderText.font || 'Press Start 2P'}", monospace`;

        const text = renderText.text || renderText.env ? this.getEnvValue(renderText.env) : 'v1.0.0';
        this.ctx.fillText(text, bbox[0] + bbox[2]/2, bbox[1] + bbox[3]/2);
      }
    }

    this.ctx.restore();
  }

  private getCurrentTime(format: string): string {
    const now = new Date();
    if (format === 'HH:mm:ss') {
      return now.toTimeString().split(' ')[0];
    } else {
      return now.toTimeString().split(' ')[0].slice(0, 5);
    }
  }

  private getEnvValue(envVar: string): string {
    // Return mock values for now
    if (envVar === 'GIT_COMMIT_SHORT') {
      return 'abc123f';
    }
    return 'unknown';
  }

  private updateWidgets() {
    // Update time-based widgets
    if (this.widgetStates.get('digital_clock') !== 'idle') {
      // Clock updates every frame when active
    }

    // Update cactus growth animation
    const cactusState = this.widgetStates.get('cactus_plant');
    if (cactusState && cactusState.includes('click')) {
      // Animate growth when in click state
      // TODO: Implement growth animation
    }
  }
}

// Add CSS animation
const style = document.createElement('style');
style.textContent = `
  @keyframes slideIn {
    from {
      opacity: 0;
      transform: translate(-50%, -50%) scale(0.9);
    }
    to {
      opacity: 1;
      transform: translate(-50%, -50%) scale(1);
    }
  }

  @import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap');
`;
document.head.appendChild(style);

// Initialize the game interface
const game = new RetroGameInterface();
