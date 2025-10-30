# PRP-016 Quick Reference Guide

**For rapid implementation - use alongside full research document**

---

## Phase 1A: Welcome Modal (START HERE)

### HTML Structure
```html
<div class="modal-overlay" id="welcome-modal">
  <div class="modal-container">
    <button class="modal-close">×</button>
    <h1>Welcome to Lilith's Room! 🎀</h1>
    <div class="modal-body">
      <!-- Content -->
    </div>
    <div class="modal-actions">
      <a href="https://github.com/dcversus/dcmaidbot" class="btn btn-secondary">View on GitHub</a>
      <button class="btn btn-primary" id="enter-room">GO TO THE ROOM 🚪</button>
    </div>
  </div>
</div>
```

### CSS Essentials
```css
.modal-overlay {
  position: fixed;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(10px);
  z-index: 10000;
}

.modal-container {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  border: 2px solid rgba(255, 105, 180, 0.3);
  border-radius: 20px;
  padding: 40px;
  max-width: 600px;
}

body.modal-open {
  transform: scale(0.95);
  filter: blur(8px) brightness(0.7);
  overflow: hidden;
}
```

### JavaScript
```javascript
function openModal() {
  document.body.classList.add('modal-open');
  document.getElementById('welcome-modal').classList.add('active');
  audio.playSound('modal-open');
}

function closeModal() {
  document.getElementById('welcome-modal').classList.remove('active');
  setTimeout(() => {
    document.body.classList.remove('modal-open');
  }, 300);
  audio.playSound('modal-close');
}
```

---

## Phase 1B: Music System

### Audio Manager Class
```javascript
class AudioManager {
  constructor() {
    this.context = new (window.AudioContext || window.webkitAudioContext)();
    this.sounds = {};
    this.music = null;
  }

  async loadSound(name, url) {
    const response = await fetch(url);
    const arrayBuffer = await response.arrayBuffer();
    const audioBuffer = await this.context.decodeAudioData(arrayBuffer);
    this.sounds[name] = audioBuffer;
  }

  playSound(name, volume = 1.0) {
    if (!this.sounds[name]) return;
    const source = this.context.createBufferSource();
    source.buffer = this.sounds[name];
    source.connect(this.context.destination);
    source.start(0);
  }

  async playMusic(url, loop = true) {
    const audio = new Audio(url);
    audio.loop = loop;
    audio.volume = 0.3;
    this.music = audio;
    await audio.play();
  }

  stopMusic() {
    if (this.music) {
      this.music.pause();
      this.music = null;
    }
  }
}

const audio = new AudioManager();
```

### Music Sources
- **Pixabay**: https://pixabay.com/music/ (search "lofi", "anime", "chill")
- **FreePD**: https://freepd.com/
- **Incompetech**: https://incompetech.com/music/

### Required Sounds
1. `bgm-lofi-anime.mp3` - Background music (2-3 min loop, <5MB)
2. `hover.mp3` - Subtle whoosh (<50KB)
3. `click.mp3` - Button click (<50KB)
4. `modal-open.mp3` - Slide up sound
5. `modal-close.mp3` - Pop sound
6. `tick-tock-loop.mp3` - Clock ticking
7. `funny-song.mp3` - Cactus widget
8. `reveal.mp3` - Room discovery

---

## Phase 1C: Widget Click Actions

### Widget HTML
```html
<div class="widget"
     data-widget="clock"
     data-action="play-ticking">
  <div class="widget-preview">Play ticking sound</div>
</div>
```

### Action Registry
```javascript
const widgetActions = {
  'clock': () => audio.playSound('tick-tock-loop'),
  'version': () => window.open('https://github.com/dcversus/dcmaidbot/blob/main/CHANGELOG.md', '_blank'),
  'commit': (ctx) => window.open(`https://github.com/dcversus/dcmaidbot/commit/${ctx.commitHash}`, '_blank'),
  'redis': () => window.open('https://status.theedgestory.org', '_blank'),
  'postgres': () => window.open('https://status.theedgestory.org', '_blank'),
  'bot-status': () => window.open('https://t.me/dcmaidbot', '_blank'),
  'cactus': () => audio.playSound('funny-song')
};

document.querySelectorAll('.widget').forEach(widget => {
  widget.addEventListener('click', () => {
    const type = widget.dataset.widget;
    widgetActions[type]?.();
  });
});
```

---

## Phase 1D: Widget Hover States

### CSS Image Swap
```css
.widget[data-widget="clock"] {
  background-image: url('/static/widgets/clock-idle.png');
  transition: all 0.3s ease;
}

.widget[data-widget="clock"]:hover {
  background-image: url('/static/widgets/clock-active.png');
  transform: translateY(-10px) scale(1.05);
  box-shadow: 0 15px 40px rgba(255, 105, 180, 0.5);
}

/* Glow effect */
.widget::before {
  content: '';
  position: absolute;
  inset: -5px;
  background: linear-gradient(45deg, #ff69b4, #ff1493);
  border-radius: inherit;
  opacity: 0;
  z-index: -1;
  filter: blur(20px);
  transition: opacity 0.3s ease;
}

.widget:hover::before {
  opacity: 0.6;
}
```

### JavaScript Preloading
```javascript
// Preload hover images
document.querySelectorAll('.widget').forEach(widget => {
  const type = widget.dataset.widget;
  const img = new Image();
  img.src = `/static/widgets/${type}-active.png`;
});

// Play hover sound
widget.addEventListener('mouseenter', () => {
  audio.playSound('hover', 0.3);
});
```

---

## Dark Souls Location Discovery

### Full Implementation
```html
<div class="location-discovered">
  <div class="location-text">
    <h1 class="location-name">POOL</h1>
    <p class="location-subtitle">Location Discovered</p>
  </div>
</div>
```

```css
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@700&display=swap');

.location-discovered {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.9);
  backdrop-filter: blur(10px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;
  opacity: 0;
  pointer-events: none;
}

.location-discovered.active {
  animation: fadeInOut 4s ease forwards;
}

@keyframes fadeInOut {
  0% { opacity: 0; }
  15% { opacity: 1; }
  85% { opacity: 1; }
  100% { opacity: 0; }
}

.location-name {
  font-family: 'Cinzel', serif;
  font-size: 72px;
  color: #fff;
  text-shadow: 0 0 20px rgba(255, 215, 0, 0.8);
  letter-spacing: 8px;
  animation: textReveal 3s ease forwards;
}

@keyframes textReveal {
  0% { opacity: 0; transform: translateY(30px); filter: blur(10px); }
  20% { opacity: 1; transform: translateY(0); filter: blur(0); }
  80% { opacity: 1; }
  100% { opacity: 0; transform: translateY(-30px); filter: blur(10px); }
}
```

```javascript
function showLocationDiscovered(name) {
  const overlay = document.querySelector('.location-discovered');
  overlay.querySelector('.location-name').textContent = name.toUpperCase();
  overlay.classList.add('active');
  audio.playSound('reveal', 0.7);

  setTimeout(() => overlay.classList.remove('active'), 4000);
}

// Trigger on first visit
if (!localStorage.getItem(`discovered_pool`)) {
  showLocationDiscovered('Pool');
  localStorage.setItem(`discovered_pool`, 'true');
}
```

---

## 3x3 Grid Layout

### Responsive Grid
```css
.room-container {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  grid-template-rows: repeat(3, 1fr);
  gap: 20px;
  width: 100%;
  max-width: 1200px;
  aspect-ratio: 1 / 1;
  padding: 40px;
  position: relative;
}

.widget {
  position: relative;
  aspect-ratio: 1 / 1;
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.3s ease;
}

/* Mobile: 2x2 grid */
@media (max-width: 768px) {
  .room-container {
    grid-template-columns: repeat(2, 1fr);
    gap: 15px;
    padding: 20px;
  }
}
```

---

## Easter Egg System

### HTML
```html
<div class="easter-egg-trigger"
     data-egg="meditation"
     style="top: 15%; left: 30%; width: 80px; height: 120px;">
  <img src="/static/easter-egg-lilit-meditation.png" alt="Easter Egg">
</div>
```

### CSS
```css
.easter-egg-trigger {
  position: absolute;
  cursor: pointer;
  opacity: 0.1;
  filter: grayscale(100%);
  transition: all 0.3s ease;
}

.easter-egg-trigger:hover {
  opacity: 1;
  filter: grayscale(0%);
  transform: scale(1.1);
  box-shadow: 0 0 20px rgba(255, 215, 0, 0.8);
}

.easter-egg-trigger:not(.found) {
  animation: eggPulse 3s infinite;
}

@keyframes eggPulse {
  0%, 100% { opacity: 0.1; }
  50% { opacity: 0.3; }
}
```

### JavaScript
```javascript
class EasterEggManager {
  constructor() {
    this.eggs = [
      { id: 'meditation', room: 'lilith-room', found: false },
      { id: 'organizing', room: 'lilith-room', found: false },
      // ... 9 total
    ];
    this.loadProgress();
  }

  findEgg(eggId) {
    const egg = this.eggs.find(e => e.id === eggId);
    if (egg && !egg.found) {
      egg.found = true;
      this.saveProgress();
      this.showNotification(egg);
      return true;
    }
    return false;
  }

  loadProgress() {
    const found = JSON.parse(localStorage.getItem('easter_eggs_found') || '[]');
    this.eggs.forEach(egg => {
      egg.found = found.includes(egg.id);
    });
  }

  saveProgress() {
    const found = this.eggs.filter(e => e.found).map(e => e.id);
    localStorage.setItem('easter_eggs_found', JSON.stringify(found));
  }
}

const easterEggs = new EasterEggManager();

document.querySelectorAll('.easter-egg-trigger').forEach(trigger => {
  trigger.addEventListener('click', function() {
    if (easterEggs.findEgg(this.dataset.egg)) {
      this.classList.add('found');
      audio.playSound('easter-egg-found');
    }
  });
});
```

---

## Performance: Virtual Scrolling

### Efficient Room Rendering
```javascript
class VirtualScroller {
  constructor() {
    this.totalRooms = 25;
    this.visibleRange = 3; // Only render 3 rooms at a time
    this.currentRoom = 1;
  }

  renderVisibleRooms() {
    const start = Math.max(1, this.currentRoom - 1);
    const end = Math.min(this.totalRooms, this.currentRoom + this.visibleRange);

    // Clear and render only visible rooms
    for (let i = start; i <= end; i++) {
      this.renderRoom(i);
    }
  }

  onScroll() {
    const scrollY = window.scrollY;
    const roomHeight = window.innerHeight;
    const newRoom = Math.floor(scrollY / roomHeight) + 1;

    if (newRoom !== this.currentRoom) {
      this.currentRoom = newRoom;
      this.renderVisibleRooms();
    }
  }
}
```

---

## Image Optimization

### WebP Conversion
```bash
# Using ImageMagick
convert input.png -quality 80 output.webp

# Using cwebp
cwebp -q 80 input.png -o output.webp

# Batch convert all PNGs
for file in *.png; do cwebp -q 80 "$file" -o "${file%.png}.webp"; done
```

### Lazy Loading
```html
<img src="placeholder.webp"
     data-src="full-image.webp"
     loading="lazy"
     alt="Room background">
```

```javascript
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const img = entry.target;
      img.src = img.dataset.src;
      observer.unobserve(img);
    }
  });
});

document.querySelectorAll('img[data-src]').forEach(img => observer.observe(img));
```

---

## AI Image Generation Prompts

### Prompt Template
```
[ROOM TYPE], isometric perspective, anime style, cozy aesthetics,
warm lighting, detailed interior, soft shadows, kawaii vibes,
pastel color palette, high detail, 4K resolution,
--ar 1:1 --style anime --quality 2
```

### Example Prompts
```
Lilith's Room:
"Teenage girl's bedroom, isometric view, anime style, pink and purple theme,
desk with computer, bookshelf with manga, bed with plushies, window with city view,
fairy lights, cozy atmosphere, kawaii aesthetic, --ar 1:1"

Parents' Room:
"Adult bedroom, isometric view, double bed with two people sleeping,
warm blue lighting, family photos on nightstand, peaceful atmosphere,
anime style, intimate and loving vibes, --ar 1:1"

Kitchen:
"Modern kitchen, isometric view, bright and clean, cooking utensils,
refrigerator with magnets, dining table, plants, warm yellow lighting,
anime style, cozy family kitchen, --ar 1:1"
```

---

## File Structure

```
static/
├── sounds/
│   ├── bgm-lofi-anime.mp3
│   ├── hover.mp3
│   ├── click.mp3
│   ├── modal-open.mp3
│   ├── modal-close.mp3
│   ├── tick-tock-loop.mp3
│   ├── funny-song.mp3
│   └── reveal.mp3
├── rooms/
│   ├── room-1.webp
│   ├── room-2.webp
│   └── ... (25 total)
├── widgets/
│   ├── clock-idle.png
│   ├── clock-active.png
│   ├── cactus-idle.png
│   ├── cactus-active.png
│   └── ... (all widget states)
├── easter-egg-*.png (9 images)
├── styles.css
└── app.js
```

---

## Implementation Order

1. ✅ Welcome Modal (HTML + CSS + JS)
2. ✅ Music System (AudioManager class + music toggle)
3. ✅ Sound Effects (preload + widget hover/click sounds)
4. ✅ Widget Click Actions (action registry)
5. ✅ Widget Hover States (image swap + glow effect)
6. ⏳ Multi-room scroll system
7. ⏳ Easter egg placement
8. ⏳ Dark Souls location discovery
9. ⏳ Performance optimization (virtual scroll + lazy load)
10. ⏳ Mobile testing

---

**Ready to implement!** 🚀

Start with Phase 1A (Welcome Modal) and work sequentially.
