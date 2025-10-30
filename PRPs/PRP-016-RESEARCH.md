# PRP-016 Research: Multi-Room Interactive House Exploration

**Research Date**: 2025-10-30
**Status**: Complete
**Research Agent**: Claude Code

---

## 1. Modern Landing Page Design Patterns (2024-2025)

### Latest Trends

**Interactive Storytelling Websites**:
- **Scroll-triggered narratives**: Content reveals as user scrolls
- **Parallax depth**: Multiple layers moving at different speeds
- **Micro-interactions**: Small animations on hover/click
- **Dark mode first**: Most modern sites default to dark themes
- **3D elements**: CSS 3D transforms for depth
- **Game-like UX**: Exploration, discovery, achievement systems

**Key Examples**:
- Apple product pages (smooth scroll reveals)
- Stripe landing page (animated gradients)
- Linear.app (dark theme, smooth animations)
- Awwwards winners 2024-2025 (experimental layouts)

**Best Practices**:
```css
/* Smooth scroll behavior */
html {
  scroll-behavior: smooth;
  scroll-snap-type: y mandatory;
}

.room {
  scroll-snap-align: start;
  scroll-snap-stop: always;
}

/* Performance optimizations */
* {
  will-change: transform, opacity;
  backface-visibility: hidden;
  perspective: 1000px;
}
```

### Immersive Storytelling Techniques

**Progressive Disclosure**:
- Reveal story elements as user scrolls
- Use fade-in animations with `IntersectionObserver`
- Combine with parallax for depth

**Example Code**:
```javascript
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('revealed');
      // Play sound effect
      playSound('reveal.mp3');
    }
  });
}, { threshold: 0.5 });

document.querySelectorAll('.room').forEach(room => {
  observer.observe(room);
});
```

**CSS for Reveals**:
```css
.room {
  opacity: 0;
  transform: translateY(50px);
  transition: opacity 0.6s ease, transform 0.8s ease;
}

.room.revealed {
  opacity: 1;
  transform: translateY(0);
}
```

### Game-like Web Experiences

**Key Patterns**:
1. **Achievement System**: Track user discoveries
2. **Progress Indicators**: Show rooms explored
3. **Easter Eggs**: Hidden clickable elements
4. **Sound Feedback**: Audio for interactions
5. **Collectibles**: Items to find across rooms

**localStorage for Persistence**:
```javascript
class ExplorationTracker {
  constructor() {
    this.visited = JSON.parse(localStorage.getItem('visited_rooms') || '[]');
    this.easterEggs = JSON.parse(localStorage.getItem('easter_eggs') || '[]');
  }

  visitRoom(roomId) {
    if (!this.visited.includes(roomId)) {
      this.visited.push(roomId);
      localStorage.setItem('visited_rooms', JSON.stringify(this.visited));
      this.showAchievement(`Discovered: ${roomId}`);
    }
  }

  findEasterEgg(eggId) {
    if (!this.easterEggs.includes(eggId)) {
      this.easterEggs.push(eggId);
      localStorage.setItem('easter_eggs', JSON.stringify(this.easterEggs));
      this.showAchievement(`Found Easter Egg: ${eggId}!`);
    }
  }

  getProgress() {
    return {
      rooms: `${this.visited.length} / 25`,
      eggs: `${this.easterEggs.length} / 9`
    };
  }
}
```

---

## 2. 3x3 Grid Layout with Isometric Perspective

### CSS Grid Techniques

**Perfect 3x3 Grid**:
```css
.room-container {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  grid-template-rows: repeat(3, 1fr);
  gap: 20px;
  width: 100%;
  max-width: 1200px;
  aspect-ratio: 1 / 1; /* Square grid */
  padding: 40px;
  position: relative;
}

.widget {
  position: relative;
  aspect-ratio: 1 / 1;
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.widget:hover {
  transform: translateY(-5px) scale(1.05);
  box-shadow: 0 10px 30px rgba(255, 105, 180, 0.3);
}
```

**Responsive Grid**:
```css
/* Mobile: 2x2 with scrollable overflow */
@media (max-width: 768px) {
  .room-container {
    grid-template-columns: repeat(2, 1fr);
    grid-template-rows: auto;
    gap: 15px;
    padding: 20px;
  }
}

/* Tablet: 3x3 */
@media (min-width: 769px) and (max-width: 1024px) {
  .room-container {
    max-width: 800px;
    gap: 18px;
  }
}
```

### Isometric CSS Transforms

**Isometric Perspective for Room**:
```css
.room-isometric {
  transform-style: preserve-3d;
  perspective: 1500px;
}

.room-container.isometric {
  transform: rotateX(60deg) rotateZ(45deg);
  transform-origin: center center;
}

.widget.isometric {
  transform: translateZ(20px);
  transition: transform 0.3s ease;
}

.widget.isometric:hover {
  transform: translateZ(80px) scale(1.1);
}
```

**Aligning Widgets with Isometric Background**:
```css
.room-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: url('/static/rooms/lilith-room-isometric.png');
  background-size: cover;
  background-position: center;
  z-index: -1;
  transform: rotateX(60deg) rotateZ(45deg);
}

/* Position widgets to match background perspective */
.widget[data-grid="0,0"] { /* Top-left corner */ }
.widget[data-grid="1,1"] { /* Center */ }
/* ...etc for 9 positions */
```

**Alternative: CSS Grid with Transform Per Cell**:
```css
/* Apply subtle 3D effect per widget without full isometric */
.widget {
  transform: perspective(1000px) rotateX(5deg) rotateY(5deg);
}

.widget:nth-child(1) { transform: perspective(1000px) rotateX(8deg) rotateY(-8deg); }
.widget:nth-child(2) { transform: perspective(1000px) rotateX(8deg) rotateY(0deg); }
.widget:nth-child(3) { transform: perspective(1000px) rotateX(8deg) rotateY(8deg); }
/* ...continue for all 9 */
```

---

## 3. Dark Souls-Style Location Discovery Effect

### CSS/JS Techniques for Cinematic Text Reveals

**Dark Souls Effect HTML**:
```html
<div class="location-discovered" data-location="Pool">
  <div class="location-text">
    <h1 class="location-name">POOL</h1>
    <p class="location-subtitle">Location Discovered</p>
  </div>
</div>
```

**CSS Animation**:
```css
.location-discovered {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.9);
  backdrop-filter: blur(10px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.6s ease;
}

.location-discovered.active {
  opacity: 1;
  pointer-events: all;
  animation: fadeInOut 4s ease forwards;
}

@keyframes fadeInOut {
  0% { opacity: 0; }
  15% { opacity: 1; }
  85% { opacity: 1; }
  100% { opacity: 0; pointer-events: none; }
}

.location-text {
  text-align: center;
  opacity: 0;
  transform: translateY(30px);
  animation: textReveal 3s ease forwards;
}

@keyframes textReveal {
  0% {
    opacity: 0;
    transform: translateY(30px);
    filter: blur(10px);
  }
  20% {
    opacity: 1;
    transform: translateY(0);
    filter: blur(0);
  }
  80% {
    opacity: 1;
    transform: translateY(0);
    filter: blur(0);
  }
  100% {
    opacity: 0;
    transform: translateY(-30px);
    filter: blur(10px);
  }
}

.location-name {
  font-family: 'Cinzel', 'Trajan Pro', serif;
  font-size: 72px;
  font-weight: 700;
  color: #fff;
  text-shadow:
    0 0 10px rgba(255, 215, 0, 0.8),
    0 0 20px rgba(255, 215, 0, 0.6),
    0 0 30px rgba(255, 215, 0, 0.4);
  letter-spacing: 8px;
  margin: 0;
}

.location-subtitle {
  font-family: 'Cinzel', serif;
  font-size: 24px;
  color: #ccc;
  text-transform: uppercase;
  letter-spacing: 4px;
  margin-top: 20px;
}
```

**JavaScript Trigger**:
```javascript
function showLocationDiscovered(locationName) {
  const overlay = document.querySelector('.location-discovered');
  const locationText = overlay.querySelector('.location-name');
  const subtitle = overlay.querySelector('.location-subtitle');

  // Update text
  locationText.textContent = locationName.toUpperCase();

  // Play dramatic sound
  playSound('dark-souls-reveal.mp3', 0.7);

  // Show overlay
  overlay.classList.add('active');

  // Auto-hide after 4 seconds
  setTimeout(() => {
    overlay.classList.remove('active');
  }, 4000);
}

// Trigger on first room visit
if (!localStorage.getItem(`discovered_${roomId}`)) {
  showLocationDiscovered(roomName);
  localStorage.setItem(`discovered_${roomId}`, 'true');
}
```

### Font Recommendations

**Epic Game-Style Fonts** (Google Fonts):
1. **Cinzel** - Roman-inspired serif (Dark Souls vibes)
2. **Trajan Pro** - Classic cinematic font (if available)
3. **IM Fell English SC** - Medieval elegance
4. **Metamorphous** - Gothic fantasy
5. **Philosopher** - Formal serif with character

**Font Import**:
```css
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700;900&family=IM+Fell+English+SC&display=swap');
```

### Animation Timing & Easing

**Best Easing Functions**:
```css
/* Smooth entrance */
animation-timing-function: cubic-bezier(0.25, 0.46, 0.45, 0.94);

/* Dramatic reveal */
animation-timing-function: cubic-bezier(0.68, -0.55, 0.265, 1.55);

/* Dark Souls style (slow start, hold, fade) */
animation-timing-function: cubic-bezier(0.42, 0, 0.58, 1);
```

**JavaScript Easing Library** (optional):
```javascript
// Use GSAP for advanced easing
gsap.to('.location-text', {
  opacity: 1,
  y: 0,
  filter: 'blur(0px)',
  duration: 1.5,
  ease: 'power3.out'
});
```

---

## 4. Music and Sound Integration

### Web Audio API Best Practices

**Audio Manager Class**:
```javascript
class AudioManager {
  constructor() {
    this.context = new (window.AudioContext || window.webkitAudioContext)();
    this.sounds = {};
    this.music = null;
    this.musicGain = this.context.createGain();
    this.sfxGain = this.context.createGain();
    this.musicGain.connect(this.context.destination);
    this.sfxGain.connect(this.context.destination);
    this.musicGain.gain.value = 0.3; // 30% volume
    this.sfxGain.gain.value = 0.5; // 50% volume
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

    const gainNode = this.context.createGain();
    gainNode.gain.value = volume;

    source.connect(gainNode);
    gainNode.connect(this.sfxGain);

    source.start(0);
    return source;
  }

  async playMusic(url, loop = true) {
    if (this.music) {
      this.stopMusic();
    }

    const audio = new Audio(url);
    audio.loop = loop;
    audio.volume = 0.3;

    const source = this.context.createMediaElementSource(audio);
    source.connect(this.musicGain);

    this.music = audio;
    await audio.play();
  }

  stopMusic() {
    if (this.music) {
      this.music.pause();
      this.music.currentTime = 0;
      this.music = null;
    }
  }

  setMusicVolume(value) {
    this.musicGain.gain.setValueAtTime(value, this.context.currentTime);
  }

  setSfxVolume(value) {
    this.sfxGain.gain.setValueAtTime(value, this.context.currentTime);
  }
}

// Global instance
const audio = new AudioManager();
```

### Copyright-Free Music Sources

**Best Sources for Anime/Lofi Music**:

1. **Pixabay Audio Library**
   - URL: https://pixabay.com/music/
   - License: Free for commercial use
   - Search: "lofi", "anime", "chill", "kawaii"
   - Format: MP3
   - Recommended tracks:
     - "Lofi Study" by FASSounds
     - "Chill Lofi Hip Hop" by Lofium
     - "Anime Vibes" by Tokyo Music Walker

2. **FreePD (Free Public Domain)**
   - URL: https://freepd.com/
   - License: Public domain
   - Categories: Ambient, Electronic, Lounge
   - Recommended: Kevin MacLeod's ambient tracks

3. **YouTube Audio Library**
   - URL: https://studio.youtube.com/channel/UC.../music
   - License: Free to use with attribution (some)
   - Filter: Genre = Ambient, Electronic
   - Download MP3 directly

4. **Purple Planet Music**
   - URL: https://www.purple-planet.com/
   - License: Free with attribution
   - Categories: Ambient, Chillout
   - High quality production

5. **Incompetech (Kevin MacLeod)**
   - URL: https://incompetech.com/music/
   - License: CC BY 4.0 (attribution required)
   - Search: "ambient", "peaceful"
   - Massive library

**Sound Effect Sources**:
1. **Freesound.org** - Community uploads, CC licenses
2. **Zapsplat.com** - Free SFX library
3. **SoundBible.com** - Public domain sounds
4. **Mixkit.co** - Modern UI sounds

**Recommended SFX**:
- Hover: "soft-whoosh.mp3", "UI_click_01.wav"
- Click: "button-click.mp3", "select.wav"
- Modal open: "slide-up.mp3"
- Modal close: "pop.mp3"
- Location discovered: "choir-ahh.mp3" + "low-rumble.mp3"
- Easter egg found: "sparkle.mp3", "chime.mp3"

### Autoplay Policy Workarounds

**Modern browsers block autoplay without user interaction**:

```javascript
class MusicToggle {
  constructor() {
    this.isPlaying = false;
    this.userInteracted = false;
  }

  init() {
    // Show music button prominently
    const musicButton = document.getElementById('music-toggle');

    // Enable on ANY user interaction
    document.addEventListener('click', () => {
      if (!this.userInteracted) {
        this.userInteracted = true;
        this.startMusic();
      }
    }, { once: true });

    musicButton.addEventListener('click', () => {
      this.toggle();
    });
  }

  async startMusic() {
    try {
      await audio.playMusic('/static/sounds/bgm-lofi-anime.mp3', true);
      this.isPlaying = true;
      this.updateButton();
    } catch (err) {
      console.log('Autoplay blocked:', err);
      // Show music button with animation
      this.showMusicPrompt();
    }
  }

  toggle() {
    if (this.isPlaying) {
      audio.stopMusic();
      this.isPlaying = false;
    } else {
      this.startMusic();
    }
    this.updateButton();
  }

  updateButton() {
    const button = document.getElementById('music-toggle');
    button.innerHTML = this.isPlaying ? '🎵 Music ON' : '🔇 Music OFF';
    button.classList.toggle('playing', this.isPlaying);
  }

  showMusicPrompt() {
    // Bounce animation on music button
    const button = document.getElementById('music-toggle');
    button.classList.add('bounce');
  }
}

const musicToggle = new MusicToggle();
musicToggle.init();
```

**CSS for Music Button**:
```css
#music-toggle {
  position: fixed;
  top: 20px;
  right: 20px;
  padding: 12px 24px;
  background: rgba(255, 105, 180, 0.9);
  color: white;
  border: none;
  border-radius: 30px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  z-index: 1000;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(255, 105, 180, 0.3);
}

#music-toggle:hover {
  background: rgba(255, 105, 180, 1);
  transform: scale(1.05);
}

#music-toggle.bounce {
  animation: bounce 1s infinite;
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

#music-toggle.playing::before {
  content: '🎵 ';
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
```

### Audio Preloading & Performance

**Preload Strategy**:
```javascript
// Preload essential sounds on page load
async function preloadAudio() {
  const essentialSounds = [
    { name: 'hover', url: '/static/sounds/hover.mp3' },
    { name: 'click', url: '/static/sounds/click.mp3' },
    { name: 'modal-close', url: '/static/sounds/pop.mp3' },
    { name: 'reveal', url: '/static/sounds/reveal.mp3' }
  ];

  const loadPromises = essentialSounds.map(({ name, url }) =>
    audio.loadSound(name, url)
  );

  await Promise.all(loadPromises);
  console.log('Essential audio preloaded');
}

// Lazy load room-specific sounds
function loadRoomSounds(roomId) {
  const roomSounds = {
    'pool': ['splash.mp3', 'water-ambience.mp3'],
    'kitchen': ['cooking.mp3', 'sizzle.mp3'],
    'garden': ['birds.mp3', 'wind.mp3']
  };

  if (roomSounds[roomId]) {
    roomSounds[roomId].forEach(filename => {
      audio.loadSound(`${roomId}-${filename}`, `/static/sounds/${roomId}/${filename}`);
    });
  }
}

// Call on page load
preloadAudio();
```

**HTML5 Audio Preload**:
```html
<!-- Preload music file -->
<link rel="preload" href="/static/sounds/bgm-lofi-anime.mp3" as="audio" type="audio/mpeg">

<!-- Preload sound effects -->
<link rel="preload" href="/static/sounds/hover.mp3" as="audio">
<link rel="preload" href="/static/sounds/click.mp3" as="audio">
```

**Performance Tips**:
- Keep BGM files < 5MB (use 128kbps MP3)
- SFX files < 100KB each
- Use MP3 format (best browser support)
- Lazy load room-specific sounds
- Unload unused audio buffers
- Use `AudioContext.suspend()` when page hidden

---

## 5. Modal Design Patterns

### Modern Modal UX Best Practices

**HTML Structure**:
```html
<div class="modal-overlay" id="welcome-modal">
  <div class="modal-container">
    <button class="modal-close" aria-label="Close modal">×</button>

    <div class="modal-content">
      <h1 class="modal-title">Welcome to Lilith's Room! 🎀</h1>

      <div class="modal-body">
        <p>Hi there! I'm <strong>Lilith</strong>, an AI waifu bot created with love by Daniil and Vasilisa.</p>

        <h3>What I can do:</h3>
        <ul>
          <li>💬 Chat in multiple languages (English, Russian, emoji!)</li>
          <li>🧠 Remember conversations with RAG</li>
          <li>😂 Tell jokes and learn from reactions</li>
          <li>🔧 Use tools (web search, games, APIs)</li>
          <li>💾 Store memories and facts</li>
        </ul>

        <div class="github-stars">
          <a href="https://github.com/dcversus/dcmaidbot" target="_blank" rel="noopener">
            ⭐ Star on GitHub
          </a>
        </div>

        <div class="telegram-link">
          <a href="https://t.me/+bkRU1_woyrY1ZTc6" target="_blank" rel="noopener">
            💬 Join Telegram Chat
          </a>
        </div>
      </div>

      <div class="modal-actions">
        <a href="https://github.com/dcversus/dcmaidbot" class="btn btn-secondary" target="_blank">
          View on GitHub
        </a>
        <button class="btn btn-primary" id="enter-room">
          GO TO THE ROOM 🚪
        </button>
      </div>
    </div>
  </div>
</div>
```

**CSS Styling**:
```css
/* Modal Overlay */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(10px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 10000;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.3s ease;
}

.modal-overlay.active {
  opacity: 1;
  pointer-events: all;
}

/* Modal Container */
.modal-container {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  border: 2px solid rgba(255, 105, 180, 0.3);
  border-radius: 20px;
  padding: 40px;
  max-width: 600px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
  position: relative;
  transform: scale(0.7);
  opacity: 0;
  transition: all 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);
}

.modal-overlay.active .modal-container {
  transform: scale(1);
  opacity: 1;
}

/* Close Button */
.modal-close {
  position: absolute;
  top: 15px;
  right: 15px;
  background: transparent;
  border: none;
  font-size: 32px;
  color: #fff;
  cursor: pointer;
  width: 40px;
  height: 40px;
  display: flex;
  justify-content: center;
  align-items: center;
  border-radius: 50%;
  transition: all 0.3s ease;
}

.modal-close:hover {
  background: rgba(255, 105, 180, 0.2);
  transform: rotate(90deg);
}

/* Content */
.modal-title {
  font-size: 32px;
  color: #ff69b4;
  margin-bottom: 20px;
  text-align: center;
}

.modal-body {
  color: #e0e0e0;
  font-size: 16px;
  line-height: 1.6;
}

.modal-body ul {
  list-style: none;
  padding: 0;
}

.modal-body li {
  padding: 8px 0;
  padding-left: 30px;
  position: relative;
}

.modal-body li::before {
  content: '✨';
  position: absolute;
  left: 0;
}

/* GitHub Stars Widget */
.github-stars {
  margin: 20px 0;
  text-align: center;
}

.github-stars a {
  display: inline-block;
  padding: 10px 20px;
  background: #24292e;
  color: white;
  text-decoration: none;
  border-radius: 8px;
  font-weight: 600;
  transition: background 0.3s ease;
}

.github-stars a:hover {
  background: #0366d6;
}

/* Telegram Link */
.telegram-link {
  margin: 20px 0;
  text-align: center;
}

.telegram-link a {
  display: inline-block;
  padding: 12px 24px;
  background: #0088cc;
  color: white;
  text-decoration: none;
  border-radius: 12px;
  font-weight: 600;
  transition: all 0.3s ease;
}

.telegram-link a:hover {
  background: #006699;
  transform: scale(1.05);
}

/* Action Buttons */
.modal-actions {
  display: flex;
  gap: 15px;
  margin-top: 30px;
  justify-content: center;
  flex-wrap: wrap;
}

.btn {
  padding: 15px 30px;
  border: none;
  border-radius: 30px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  text-decoration: none;
  display: inline-block;
}

.btn-primary {
  background: linear-gradient(135deg, #ff69b4 0%, #ff1493 100%);
  color: white;
  box-shadow: 0 4px 15px rgba(255, 105, 180, 0.4);
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(255, 105, 180, 0.6);
}

.btn-secondary {
  background: white;
  color: #333;
  box-shadow: 0 4px 15px rgba(255, 255, 255, 0.2);
}

.btn-secondary:hover {
  background: #f0f0f0;
  transform: translateY(-2px);
}

/* Mobile Responsive */
@media (max-width: 768px) {
  .modal-container {
    padding: 30px 20px;
    width: 95%;
  }

  .modal-title {
    font-size: 24px;
  }

  .modal-actions {
    flex-direction: column;
  }

  .btn {
    width: 100%;
  }
}
```

### Backdrop Blur Effects

**Advanced Blur Techniques**:
```css
/* Glass morphism effect */
.modal-overlay {
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
}

/* Fallback for browsers without backdrop-filter */
@supports not (backdrop-filter: blur(20px)) {
  .modal-overlay {
    background: rgba(0, 0, 0, 0.9);
  }
}

/* Modal container glass effect */
.modal-container {
  background: rgba(26, 26, 46, 0.8);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
}
```

### Scale Transforms for Background Content

**Zoom Out Effect**:
```css
/* Main content */
body {
  transition: transform 0.4s ease, filter 0.4s ease;
}

body.modal-open {
  transform: scale(0.95);
  filter: blur(8px) brightness(0.7);
  overflow: hidden;
}

/* Prevent scroll when modal open */
body.modal-open {
  overflow: hidden;
}
```

**JavaScript Control**:
```javascript
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  const body = document.body;

  // Add class to body
  body.classList.add('modal-open');

  // Show modal
  modal.classList.add('active');

  // Play sound
  audio.playSound('modal-open');

  // Focus trap
  trapFocus(modal);
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  const body = document.body;

  // Remove modal
  modal.classList.remove('active');

  // Remove body class after animation
  setTimeout(() => {
    body.classList.remove('modal-open');
  }, 300);

  // Play sound
  audio.playSound('modal-close');
}

// Event listeners
document.getElementById('enter-room').addEventListener('click', () => {
  closeModal('welcome-modal');
});

document.querySelector('.modal-close').addEventListener('click', () => {
  closeModal('welcome-modal');
});

// Close on outside click
document.querySelector('.modal-overlay').addEventListener('click', (e) => {
  if (e.target.classList.contains('modal-overlay')) {
    closeModal('welcome-modal');
  }
});

// Close on ESC key
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    closeModal('welcome-modal');
  }
});
```

### Accessibility Considerations

**A11y Best Practices**:
```html
<!-- ARIA attributes -->
<div class="modal-overlay" id="welcome-modal" role="dialog" aria-modal="true" aria-labelledby="modal-title">
  <div class="modal-container">
    <button class="modal-close" aria-label="Close modal">×</button>
    <h1 id="modal-title" class="modal-title">Welcome to Lilith's Room!</h1>
    <!-- content -->
  </div>
</div>
```

**Focus Trap**:
```javascript
function trapFocus(element) {
  const focusableElements = element.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );

  const firstElement = focusableElements[0];
  const lastElement = focusableElements[focusableElements.length - 1];

  element.addEventListener('keydown', (e) => {
    if (e.key === 'Tab') {
      if (e.shiftKey) {
        if (document.activeElement === firstElement) {
          e.preventDefault();
          lastElement.focus();
        }
      } else {
        if (document.activeElement === lastElement) {
          e.preventDefault();
          firstElement.focus();
        }
      }
    }
  });

  // Focus first element
  firstElement.focus();
}
```

### Mobile-Friendly Modals

**Touch Gestures**:
```javascript
// Swipe down to close modal
let touchStartY = 0;
const modal = document.querySelector('.modal-container');

modal.addEventListener('touchstart', (e) => {
  touchStartY = e.touches[0].clientY;
});

modal.addEventListener('touchmove', (e) => {
  const touchY = e.touches[0].clientY;
  const diff = touchY - touchStartY;

  if (diff > 0) {
    // Drag down
    modal.style.transform = `translateY(${diff}px) scale(${1 - diff / 1000})`;
  }
});

modal.addEventListener('touchend', (e) => {
  const touchY = e.changedTouches[0].clientY;
  const diff = touchY - touchStartY;

  if (diff > 100) {
    // Close modal
    closeModal('welcome-modal');
  } else {
    // Reset position
    modal.style.transform = '';
  }
});
```

---

## 6. Multi-Layer Scrolling Systems

### Parallax Scrolling Techniques

**Basic Parallax Setup**:
```html
<div class="parallax-container">
  <div class="parallax-layer layer-far" data-speed="0.3">
    <!-- Background layer -->
  </div>
  <div class="parallax-layer layer-mid" data-speed="0.6">
    <!-- Middle layer -->
  </div>
  <div class="parallax-layer layer-near" data-speed="1.0">
    <!-- Foreground layer -->
  </div>
</div>
```

**CSS Setup**:
```css
.parallax-container {
  position: relative;
  height: 100vh;
  overflow-y: scroll;
  scroll-behavior: smooth;
}

.parallax-layer {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  transition: transform 0.1s linear;
}

.layer-far {
  z-index: 1;
}

.layer-mid {
  z-index: 2;
}

.layer-near {
  z-index: 3;
}
```

**JavaScript Implementation**:
```javascript
class ParallaxScroller {
  constructor() {
    this.layers = document.querySelectorAll('.parallax-layer');
    this.container = document.querySelector('.parallax-container');
    this.init();
  }

  init() {
    this.container.addEventListener('scroll', () => {
      this.updateParallax();
    });

    // Initial update
    this.updateParallax();
  }

  updateParallax() {
    const scrollY = this.container.scrollTop;

    this.layers.forEach(layer => {
      const speed = parseFloat(layer.dataset.speed);
      const yPos = -(scrollY * speed);
      layer.style.transform = `translateY(${yPos}px)`;
    });
  }
}

const parallax = new ParallaxScroller();
```

### Layer Switching UI Patterns

**5-Layer Navigation**:
```html
<div class="layer-switcher">
  <button class="layer-btn" data-layer="1">
    <span class="layer-icon">🏠</span>
    <span class="layer-name">House</span>
  </button>
  <button class="layer-btn" data-layer="2">
    <span class="layer-icon">💪</span>
    <span class="layer-name">Recreation</span>
  </button>
  <button class="layer-btn active" data-layer="3">
    <span class="layer-icon">🏊</span>
    <span class="layer-name">Pool</span>
  </button>
  <button class="layer-btn" data-layer="4">
    <span class="layer-icon">🌱</span>
    <span class="layer-name">Garden</span>
  </button>
  <button class="layer-btn" data-layer="5">
    <span class="layer-icon">🏬</span>
    <span class="layer-name">Mall</span>
  </button>

  <div class="layer-indicator"></div>
</div>

<div class="layer-nav-arrows">
  <button class="arrow-btn arrow-up" id="layer-up">↑ UP</button>
  <button class="arrow-btn arrow-down" id="layer-down">↓ DOWN</button>
</div>
```

**CSS Styling**:
```css
.layer-switcher {
  position: fixed;
  left: 20px;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  flex-direction: column;
  gap: 10px;
  z-index: 1000;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(10px);
  padding: 15px;
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.layer-btn {
  background: transparent;
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  padding: 12px;
  color: white;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
  transition: all 0.3s ease;
  min-width: 80px;
}

.layer-btn:hover {
  border-color: rgba(255, 105, 180, 0.8);
  background: rgba(255, 105, 180, 0.1);
}

.layer-btn.active {
  background: rgba(255, 105, 180, 0.3);
  border-color: #ff69b4;
}

.layer-icon {
  font-size: 24px;
}

.layer-name {
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
}

.layer-nav-arrows {
  position: fixed;
  right: 20px;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  flex-direction: column;
  gap: 10px;
  z-index: 1000;
}

.arrow-btn {
  background: rgba(255, 105, 180, 0.9);
  border: none;
  border-radius: 50%;
  width: 60px;
  height: 60px;
  color: white;
  font-size: 18px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(255, 105, 180, 0.4);
}

.arrow-btn:hover {
  background: #ff1493;
  transform: scale(1.1);
}

.arrow-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

/* Mobile: horizontal layout */
@media (max-width: 768px) {
  .layer-switcher {
    left: 50%;
    top: auto;
    bottom: 20px;
    transform: translateX(-50%);
    flex-direction: row;
  }

  .layer-nav-arrows {
    right: auto;
    left: 50%;
    top: 20px;
    transform: translateX(-50%);
    flex-direction: row;
  }
}
```

**JavaScript Layer Switching**:
```javascript
class LayerManager {
  constructor() {
    this.currentLayer = 1;
    this.maxLayer = 5;
    this.layers = [];
    this.init();
  }

  init() {
    // Layer button clicks
    document.querySelectorAll('.layer-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const layer = parseInt(btn.dataset.layer);
        this.switchToLayer(layer);
      });
    });

    // Arrow navigation
    document.getElementById('layer-up').addEventListener('click', () => {
      this.navigateLayer(-1);
    });

    document.getElementById('layer-down').addEventListener('click', () => {
      this.navigateLayer(1);
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowUp') this.navigateLayer(-1);
      if (e.key === 'ArrowDown') this.navigateLayer(1);
    });
  }

  switchToLayer(layerNum) {
    if (layerNum < 1 || layerNum > this.maxLayer) return;

    this.currentLayer = layerNum;

    // Update UI
    this.updateLayerUI();

    // Scroll to layer
    this.scrollToLayer(layerNum);

    // Play transition sound
    audio.playSound('layer-switch');
  }

  navigateLayer(direction) {
    const newLayer = this.currentLayer + direction;
    this.switchToLayer(newLayer);
  }

  scrollToLayer(layerNum) {
    const layerElement = document.querySelector(`[data-layer-content="${layerNum}"]`);
    if (layerElement) {
      layerElement.scrollIntoView({ behavior: 'smooth' });
    }
  }

  updateLayerUI() {
    // Update active button
    document.querySelectorAll('.layer-btn').forEach(btn => {
      btn.classList.toggle('active', parseInt(btn.dataset.layer) === this.currentLayer);
    });

    // Update arrow buttons
    document.getElementById('layer-up').disabled = this.currentLayer === 1;
    document.getElementById('layer-down').disabled = this.currentLayer === this.maxLayer;
  }
}

const layerManager = new LayerManager();
```

### Smooth Scroll Libraries

**GSAP ScrollTrigger** (Recommended):
```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/gsap.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/ScrollTrigger.min.js"></script>
```

```javascript
gsap.registerPlugin(ScrollTrigger);

// Animate rooms on scroll
gsap.utils.toArray('.room').forEach((room, i) => {
  gsap.from(room, {
    opacity: 0,
    y: 100,
    scale: 0.9,
    scrollTrigger: {
      trigger: room,
      start: 'top 80%',
      end: 'top 20%',
      scrub: 1,
      markers: false
    }
  });
});

// Parallax layers
gsap.to('.layer-far', {
  yPercent: -30,
  ease: 'none',
  scrollTrigger: {
    trigger: '.parallax-container',
    start: 'top top',
    end: 'bottom top',
    scrub: true
  }
});
```

**Locomotive Scroll** (Alternative):
```html
<script src="https://cdn.jsdelivr.net/npm/locomotive-scroll@4.1.4/dist/locomotive-scroll.min.js"></script>
```

```javascript
const scroll = new LocomotiveScroll({
  el: document.querySelector('[data-scroll-container]'),
  smooth: true,
  multiplier: 1,
  class: 'is-revealed'
});

// Update on route change
scroll.update();
```

**CSS Scroll Snap** (No library needed):
```css
.rooms-container {
  scroll-snap-type: y mandatory;
  overflow-y: scroll;
  height: 100vh;
}

.room {
  scroll-snap-align: start;
  scroll-snap-stop: always;
  height: 100vh;
}
```

### Performance Optimization

**Virtual Scrolling for 25 Rooms**:
```javascript
class VirtualScroller {
  constructor() {
    this.rooms = Array.from({ length: 25 }, (_, i) => i + 1);
    this.visibleRange = 3; // Render 3 rooms at a time
    this.currentRoom = 1;
    this.container = document.querySelector('.rooms-container');
    this.init();
  }

  init() {
    this.renderVisibleRooms();

    this.container.addEventListener('scroll', () => {
      this.updateVisibleRooms();
    });
  }

  renderVisibleRooms() {
    const start = Math.max(1, this.currentRoom - 1);
    const end = Math.min(this.rooms.length, this.currentRoom + this.visibleRange);

    // Clear container
    this.container.innerHTML = '';

    // Render visible rooms
    for (let i = start; i <= end; i++) {
      const roomElement = this.createRoomElement(i);
      this.container.appendChild(roomElement);
    }
  }

  createRoomElement(roomNum) {
    const room = document.createElement('div');
    room.className = 'room';
    room.dataset.room = roomNum;
    room.innerHTML = this.getRoomHTML(roomNum);
    return room;
  }

  getRoomHTML(roomNum) {
    // Generate room content based on room number
    return `
      <div class="room-background" style="background-image: url('/static/rooms/room-${roomNum}.jpg')"></div>
      <div class="room-widgets">
        <!-- Widget grid -->
      </div>
    `;
  }

  updateVisibleRooms() {
    const scrollY = this.container.scrollTop;
    const roomHeight = window.innerHeight;
    const newCurrentRoom = Math.floor(scrollY / roomHeight) + 1;

    if (newCurrentRoom !== this.currentRoom) {
      this.currentRoom = newCurrentRoom;
      this.renderVisibleRooms();
    }
  }
}

const virtualScroller = new VirtualScroller();
```

**Intersection Observer for Lazy Loading**:
```javascript
const imageObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const img = entry.target;
      img.src = img.dataset.src;
      img.classList.add('loaded');
      imageObserver.unobserve(img);
    }
  });
}, {
  rootMargin: '200px' // Load 200px before visible
});

// Observe all lazy images
document.querySelectorAll('img[data-src]').forEach(img => {
  imageObserver.observe(img);
});
```

---

## 7. Interactive Widget Systems

### Hover State Management

**CSS Hover Effects**:
```css
.widget {
  position: relative;
  background-size: cover;
  background-position: center;
  transition: all 0.3s ease;
  cursor: pointer;
}

/* Default background */
.widget[data-widget="clock"] {
  background-image: url('/static/widgets/clock-idle.png');
}

/* Hover state - swap background */
.widget[data-widget="clock"]:hover {
  background-image: url('/static/widgets/clock-active.png');
  transform: translateY(-10px) scale(1.05);
  box-shadow: 0 15px 40px rgba(255, 105, 180, 0.5);
  z-index: 10;
}

/* Glow effect */
.widget::before {
  content: '';
  position: absolute;
  top: -5px;
  left: -5px;
  right: -5px;
  bottom: -5px;
  background: linear-gradient(45deg, #ff69b4, #ff1493, #c71585);
  border-radius: inherit;
  opacity: 0;
  z-index: -1;
  filter: blur(20px);
  transition: opacity 0.3s ease;
}

.widget:hover::before {
  opacity: 0.6;
}

/* Preview overlay */
.widget-preview {
  position: absolute;
  bottom: 10px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 5px 10px;
  border-radius: 8px;
  font-size: 12px;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.3s ease;
  white-space: nowrap;
}

.widget:hover .widget-preview {
  opacity: 1;
}
```

**JavaScript Image Preloading**:
```javascript
class WidgetManager {
  constructor() {
    this.widgets = document.querySelectorAll('.widget');
    this.preloadedImages = new Map();
    this.init();
  }

  init() {
    // Preload all hover images
    this.widgets.forEach(widget => {
      this.preloadHoverImage(widget);
      this.attachEventListeners(widget);
    });
  }

  preloadHoverImage(widget) {
    const widgetType = widget.dataset.widget;
    const activeImageUrl = `/static/widgets/${widgetType}-active.png`;

    const img = new Image();
    img.src = activeImageUrl;
    this.preloadedImages.set(widgetType, img);
  }

  attachEventListeners(widget) {
    widget.addEventListener('mouseenter', () => {
      this.onWidgetHover(widget);
    });

    widget.addEventListener('mouseleave', () => {
      this.onWidgetLeave(widget);
    });

    widget.addEventListener('click', () => {
      this.onWidgetClick(widget);
    });
  }

  onWidgetHover(widget) {
    const widgetType = widget.dataset.widget;

    // Play hover sound
    audio.playSound('hover', 0.3);

    // Show preview
    const preview = widget.querySelector('.widget-preview');
    if (preview) {
      preview.style.opacity = '1';
    }

    // Emit custom event
    widget.dispatchEvent(new CustomEvent('widget:hover', {
      detail: { type: widgetType }
    }));
  }

  onWidgetLeave(widget) {
    // Hide preview
    const preview = widget.querySelector('.widget-preview');
    if (preview) {
      preview.style.opacity = '0';
    }
  }

  onWidgetClick(widget) {
    const widgetType = widget.dataset.widget;
    const action = widget.dataset.action;

    // Play click sound
    this.playWidgetClickSound(widgetType);

    // Execute action
    this.executeWidgetAction(widgetType, action);
  }

  playWidgetClickSound(widgetType) {
    const soundMap = {
      'clock': 'tick-tock',
      'cactus': 'funny-song',
      'version': 'click',
      'commit': 'click',
      'uptime': 'funny-sound',
      'redis': 'status-beep',
      'postgres': 'status-beep',
      'bot-status': 'bot-beep'
    };

    const soundName = soundMap[widgetType] || 'click';
    audio.playSound(soundName);
  }

  executeWidgetAction(widgetType, action) {
    const actions = {
      'clock': () => {
        // Play ticking loop
        audio.playSound('tick-tock-loop', 0.5);
      },
      'version': () => {
        // Navigate to CHANGELOG
        window.open('https://github.com/dcversus/dcmaidbot/blob/main/CHANGELOG.md', '_blank');
      },
      'commit': () => {
        // Get commit hash from widget
        const commitHash = action;
        window.open(`https://github.com/dcversus/dcmaidbot/commit/${commitHash}`, '_blank');
      },
      'uptime': () => {
        // Play animation
        this.playUptimeAnimation();
      },
      'redis': () => {
        window.open('https://status.theedgestory.org', '_blank');
      },
      'postgres': () => {
        window.open('https://status.theedgestory.org', '_blank');
      },
      'bot-status': () => {
        window.open('https://t.me/dcmaidbot', '_blank');
      },
      'cactus': () => {
        audio.playSound('cactus-song');
      },
      'edge-story': () => {
        this.showArkSpaceship();
        window.open('https://theedgestory.org', '_blank');
      }
    };

    if (actions[widgetType]) {
      actions[widgetType]();
    }
  }

  playUptimeAnimation() {
    // Confetti or celebratory animation
    this.createConfetti();
  }

  showArkSpaceship() {
    // Render 3D Ark spaceship overlay
    const overlay = document.createElement('div');
    overlay.className = 'ark-spaceship-overlay';
    overlay.innerHTML = `
      <div class="ark-container">
        <img src="/static/ark-spaceship.png" alt="Ark Spaceship" class="ark-image">
        <p>The Edge Story awaits... 🚀</p>
      </div>
    `;
    document.body.appendChild(overlay);

    setTimeout(() => {
      overlay.remove();
    }, 3000);
  }

  createConfetti() {
    // Simple confetti effect
    const colors = ['#ff69b4', '#ff1493', '#c71585', '#ffd700', '#00ffff'];

    for (let i = 0; i < 50; i++) {
      const confetti = document.createElement('div');
      confetti.className = 'confetti';
      confetti.style.left = Math.random() * 100 + '%';
      confetti.style.background = colors[Math.floor(Math.random() * colors.length)];
      confetti.style.animationDelay = Math.random() * 3 + 's';
      document.body.appendChild(confetti);

      setTimeout(() => confetti.remove(), 4000);
    }
  }
}

const widgetManager = new WidgetManager();
```

### Click Action Patterns

**Action Registry Pattern**:
```javascript
class WidgetActionRegistry {
  constructor() {
    this.actions = new Map();
    this.registerDefaultActions();
  }

  register(widgetType, action) {
    this.actions.set(widgetType, action);
  }

  execute(widgetType, context = {}) {
    const action = this.actions.get(widgetType);
    if (action) {
      action(context);
    } else {
      console.warn(`No action registered for widget: ${widgetType}`);
    }
  }

  registerDefaultActions() {
    // Clock widget
    this.register('clock', () => {
      const clockSound = audio.playSound('tick-tock-loop', 0.5);
      // Stop after 10 seconds
      setTimeout(() => clockSound.stop(), 10000);
    });

    // Version widget
    this.register('version', (ctx) => {
      window.open('https://github.com/dcversus/dcmaidbot/blob/main/CHANGELOG.md', '_blank');
    });

    // Commit widget
    this.register('commit', (ctx) => {
      const commitHash = ctx.commitHash || 'main';
      window.open(`https://github.com/dcversus/dcmaidbot/commit/${commitHash}`, '_blank');
    });

    // Add more actions...
  }
}

const actionRegistry = new WidgetActionRegistry();

// Usage
document.querySelectorAll('.widget').forEach(widget => {
  widget.addEventListener('click', () => {
    const widgetType = widget.dataset.widget;
    const context = {
      commitHash: widget.dataset.commitHash,
      version: widget.dataset.version
    };
    actionRegistry.execute(widgetType, context);
  });
});
```

### Image Swapping Techniques

**Instant Swap (Preloaded)**:
```javascript
class ImageSwapper {
  constructor(element) {
    this.element = element;
    this.idleImage = element.dataset.idle;
    this.activeImage = element.dataset.active;
    this.currentImage = 'idle';
    this.preload();
  }

  preload() {
    // Preload active image
    const img = new Image();
    img.src = this.activeImage;
  }

  swapToActive() {
    if (this.currentImage === 'idle') {
      this.element.style.backgroundImage = `url('${this.activeImage}')`;
      this.currentImage = 'active';
    }
  }

  swapToIdle() {
    if (this.currentImage === 'active') {
      this.element.style.backgroundImage = `url('${this.idleImage}')`;
      this.currentImage = 'idle';
    }
  }
}

// Usage
const swappers = new Map();

document.querySelectorAll('.widget').forEach(widget => {
  const swapper = new ImageSwapper(widget);
  swappers.set(widget, swapper);

  widget.addEventListener('mouseenter', () => swapper.swapToActive());
  widget.addEventListener('mouseleave', () => swapper.swapToIdle());
});
```

**CSS-Only Swap (Faster)**:
```css
.widget {
  background-image: var(--idle-image);
  transition: background-image 0s;
}

.widget:hover {
  background-image: var(--active-image);
}

/* Define images as CSS custom properties */
.widget[data-widget="clock"] {
  --idle-image: url('/static/widgets/clock-idle.png');
  --active-image: url('/static/widgets/clock-active.png');
}
```

**Sprite Sheet Technique** (Most efficient):
```css
.widget {
  background-image: url('/static/widgets/sprite-sheet.png');
  background-size: 200% 100%;
  background-position: 0% 0%;
  transition: background-position 0.3s ease;
}

.widget:hover {
  background-position: 100% 0%;
}

/* Sprite sheet layout: [idle][active] side-by-side */
```

### Sound Triggering on Interactions

**Debounced Sound Triggering**:
```javascript
class SoundTrigger {
  constructor() {
    this.lastPlayTime = new Map();
    this.debounceDelay = 100; // ms
  }

  play(soundName, volume = 1.0) {
    const now = Date.now();
    const lastPlay = this.lastPlayTime.get(soundName) || 0;

    // Debounce
    if (now - lastPlay < this.debounceDelay) {
      return;
    }

    audio.playSound(soundName, volume);
    this.lastPlayTime.set(soundName, now);
  }

  playOnce(soundName, volume = 1.0) {
    if (!this.lastPlayTime.has(soundName)) {
      audio.playSound(soundName, volume);
      this.lastPlayTime.set(soundName, Date.now());
    }
  }
}

const soundTrigger = new SoundTrigger();

// Hover sound (debounced)
document.querySelectorAll('.widget').forEach(widget => {
  widget.addEventListener('mouseenter', () => {
    soundTrigger.play('hover', 0.3);
  });
});
```

---

## 8. Easter Egg Implementation

### Creative Placement Strategies

**Easter Egg System**:
```javascript
class EasterEggManager {
  constructor() {
    this.easterEggs = [
      {
        id: 'meditation',
        image: '/static/easter-egg-lilit-meditation.png',
        room: 'lilith-room',
        placement: 'poster',
        hint: 'Look for zen vibes...',
        found: false
      },
      {
        id: 'organizing',
        image: '/static/easter-egg-lilit-organizing.png',
        room: 'lilith-room',
        placement: 'notebook-screen',
        hint: 'Organization is key!',
        found: false
      },
      {
        id: 'contract',
        image: '/static/easter-egg-lilit-contract.png',
        room: 'parents-room',
        placement: 'desk-document',
        hint: 'Important papers...',
        found: false
      },
      {
        id: 'emotion-wheel',
        image: '/static/easter-egg-emotion-wheel.png',
        room: 'hall',
        placement: 'wall-poster',
        hint: 'Feelings chart on the wall',
        found: false
      },
      {
        id: 'vasilisa-armor',
        image: '/static/easter-egg-vasilisa-armor.jpg',
        room: 'parents-room',
        placement: 'framed-photo',
        hint: 'Mama in warrior mode!',
        found: false
      },
      {
        id: 'vasilisa-rollerblades',
        image: '/static/easter-egg-vasilisa-rollerblades.jpg',
        room: 'hall',
        placement: 'family-photo',
        hint: 'Casual mama vibes',
        found: false
      },
      {
        id: 'comic-1',
        image: '/static/easter-egg-comic-1.png',
        room: 'kitchen',
        placement: 'fridge-magnet',
        hint: 'Story on the fridge',
        found: false
      },
      {
        id: 'comic-2',
        image: '/static/easter-egg-comic-2.png',
        room: 'lilith-room',
        placement: 'book-cover',
        hint: 'Read between the books',
        found: false
      },
      {
        id: 'character-designs',
        image: '/static/easter-egg-character-designs.png',
        room: 'parents-room',
        placement: 'tv-screen',
        hint: 'Watch the TV closely',
        found: false
      }
    ];

    this.loadProgress();
  }

  loadProgress() {
    const found = JSON.parse(localStorage.getItem('easter_eggs_found') || '[]');
    this.easterEggs.forEach(egg => {
      egg.found = found.includes(egg.id);
    });
  }

  saveProgress() {
    const found = this.easterEggs.filter(e => e.found).map(e => e.id);
    localStorage.setItem('easter_eggs_found', JSON.stringify(found));
  }

  findEasterEgg(eggId) {
    const egg = this.easterEggs.find(e => e.id === eggId);
    if (egg && !egg.found) {
      egg.found = true;
      this.saveProgress();
      this.showFoundNotification(egg);
      this.checkCompletion();
      return true;
    }
    return false;
  }

  showFoundNotification(egg) {
    const notification = document.createElement('div');
    notification.className = 'easter-egg-found';
    notification.innerHTML = `
      <div class="egg-notification">
        <img src="${egg.image}" alt="${egg.id}">
        <h3>Easter Egg Found!</h3>
        <p>${egg.hint}</p>
        <div class="egg-progress">${this.getFoundCount()} / ${this.easterEggs.length}</div>
      </div>
    `;
    document.body.appendChild(notification);

    // Play sound
    audio.playSound('easter-egg-found');

    // Remove after 5 seconds
    setTimeout(() => {
      notification.remove();
    }, 5000);
  }

  getFoundCount() {
    return this.easterEggs.filter(e => e.found).length;
  }

  checkCompletion() {
    if (this.getFoundCount() === this.easterEggs.length) {
      this.showCompletionCelebration();
    }
  }

  showCompletionCelebration() {
    // Full-screen celebration
    const celebration = document.createElement('div');
    celebration.className = 'easter-egg-completion';
    celebration.innerHTML = `
      <div class="completion-content">
        <h1>🎉 CONGRATULATIONS! 🎉</h1>
        <p>You found all ${this.easterEggs.length} Easter Eggs!</p>
        <p class="subtitle">You're a true explorer! Nyaa~ 💖</p>
        <div class="egg-gallery">
          ${this.easterEggs.map(egg => `
            <img src="${egg.image}" alt="${egg.id}" class="egg-thumbnail">
          `).join('')}
        </div>
      </div>
    `;
    document.body.appendChild(celebration);

    // Confetti effect
    this.createConfettiExplosion();

    // Play victory music
    audio.playSound('victory-fanfare');
  }

  createConfettiExplosion() {
    // Similar to confetti in widget section
    const colors = ['#ff69b4', '#ff1493', '#ffd700', '#00ffff', '#00ff00'];
    for (let i = 0; i < 200; i++) {
      setTimeout(() => {
        const confetti = document.createElement('div');
        confetti.className = 'confetti';
        confetti.style.left = Math.random() * 100 + '%';
        confetti.style.background = colors[Math.floor(Math.random() * colors.length)];
        confetti.style.animationDelay = '0s';
        document.body.appendChild(confetti);

        setTimeout(() => confetti.remove(), 3000);
      }, i * 10);
    }
  }

  getHint(roomId) {
    const roomEggs = this.easterEggs.filter(e => e.room === roomId && !e.found);
    if (roomEggs.length > 0) {
      return roomEggs[0].hint;
    }
    return null;
  }
}

const easterEggManager = new EasterEggManager();
```

### Hidden Element Patterns

**CSS for Hidden Elements**:
```css
.easter-egg-trigger {
  position: absolute;
  cursor: pointer;
  transition: all 0.3s ease;
}

/* Blend into background initially */
.easter-egg-trigger {
  opacity: 0.1;
  filter: grayscale(100%);
}

/* Reveal on hover */
.easter-egg-trigger:hover {
  opacity: 1;
  filter: grayscale(0%);
  transform: scale(1.1);
  box-shadow: 0 0 20px rgba(255, 215, 0, 0.8);
}

/* Found state */
.easter-egg-trigger.found {
  opacity: 0.5;
  pointer-events: none;
}

/* Subtle pulse animation for unfound eggs */
.easter-egg-trigger:not(.found) {
  animation: eggPulse 3s infinite;
}

@keyframes eggPulse {
  0%, 100% { opacity: 0.1; }
  50% { opacity: 0.3; }
}
```

**HTML Structure**:
```html
<div class="room" data-room="lilith-room">
  <!-- Room background -->
  <div class="room-background"></div>

  <!-- Hidden easter egg triggers -->
  <div class="easter-egg-trigger"
       data-egg="meditation"
       style="top: 15%; left: 30%; width: 80px; height: 120px;">
    <img src="/static/easter-egg-lilit-meditation.png" alt="Easter Egg">
  </div>

  <div class="easter-egg-trigger"
       data-egg="organizing"
       style="top: 60%; left: 50%; width: 100px; height: 80px;">
    <img src="/static/easter-egg-lilit-organizing.png" alt="Easter Egg">
  </div>

  <!-- Room widgets -->
  <div class="room-widgets">
    <!-- ... -->
  </div>
</div>
```

**JavaScript Discovery**:
```javascript
document.querySelectorAll('.easter-egg-trigger').forEach(trigger => {
  trigger.addEventListener('click', function() {
    const eggId = this.dataset.egg;

    if (easterEggManager.findEasterEgg(eggId)) {
      // Mark as found
      this.classList.add('found');

      // Play animation
      this.style.animation = 'eggCollect 0.6s ease forwards';
    }
  });
});

// Collect animation
const style = document.createElement('style');
style.textContent = `
  @keyframes eggCollect {
    0% { transform: scale(1); opacity: 1; }
    50% { transform: scale(1.5) rotate(360deg); opacity: 1; }
    100% { transform: scale(0); opacity: 0; }
  }
`;
document.head.appendChild(style);
```

### Discovery Mechanics

**Proximity Detection**:
```javascript
class EasterEggProximity {
  constructor() {
    this.eggs = document.querySelectorAll('.easter-egg-trigger');
    this.proximityRadius = 100; // pixels
    this.init();
  }

  init() {
    document.addEventListener('mousemove', (e) => {
      this.checkProximity(e.clientX, e.clientY);
    });
  }

  checkProximity(mouseX, mouseY) {
    this.eggs.forEach(egg => {
      if (egg.classList.contains('found')) return;

      const rect = egg.getBoundingClientRect();
      const eggX = rect.left + rect.width / 2;
      const eggY = rect.top + rect.height / 2;

      const distance = Math.sqrt(
        Math.pow(mouseX - eggX, 2) + Math.pow(mouseY - eggY, 2)
      );

      if (distance < this.proximityRadius) {
        // Show hint
        this.showProximityHint(egg, distance);
      }
    });
  }

  showProximityHint(egg, distance) {
    // Increase opacity based on proximity
    const opacity = 1 - (distance / this.proximityRadius);
    egg.style.opacity = Math.max(0.1, opacity);

    // Play subtle sound if very close
    if (distance < 30 && !egg.dataset.soundPlayed) {
      audio.playSound('egg-nearby', 0.2);
      egg.dataset.soundPlayed = 'true';
    }
  }
}

const proximity = new EasterEggProximity();
```

### Achievement Systems

**Achievement Tracker**:
```javascript
class AchievementSystem {
  constructor() {
    this.achievements = [
      {
        id: 'first-egg',
        title: 'First Discovery',
        description: 'Find your first easter egg',
        icon: '🥚',
        condition: () => easterEggManager.getFoundCount() >= 1
      },
      {
        id: 'half-way',
        title: 'Detective',
        description: 'Find 5 easter eggs',
        icon: '🔍',
        condition: () => easterEggManager.getFoundCount() >= 5
      },
      {
        id: 'completionist',
        title: 'Master Explorer',
        description: 'Find all 9 easter eggs',
        icon: '🏆',
        condition: () => easterEggManager.getFoundCount() === 9
      },
      {
        id: 'room-explorer',
        title: 'Room Explorer',
        description: 'Visit all 25 rooms',
        icon: '🏠',
        condition: () => this.getVisitedRoomsCount() === 25
      },
      {
        id: 'speed-runner',
        title: 'Speed Runner',
        description: 'Find all eggs in under 15 minutes',
        icon: '⚡',
        condition: () => this.checkSpeedRun()
      }
    ];

    this.unlocked = JSON.parse(localStorage.getItem('achievements') || '[]');
  }

  check() {
    this.achievements.forEach(achievement => {
      if (!this.unlocked.includes(achievement.id) && achievement.condition()) {
        this.unlock(achievement);
      }
    });
  }

  unlock(achievement) {
    this.unlocked.push(achievement.id);
    localStorage.setItem('achievements', JSON.stringify(this.unlocked));

    // Show achievement notification
    this.showAchievementUnlocked(achievement);
  }

  showAchievementUnlocked(achievement) {
    const notification = document.createElement('div');
    notification.className = 'achievement-unlocked';
    notification.innerHTML = `
      <div class="achievement-content">
        <div class="achievement-icon">${achievement.icon}</div>
        <div class="achievement-text">
          <h3>Achievement Unlocked!</h3>
          <p class="achievement-title">${achievement.title}</p>
          <p class="achievement-desc">${achievement.description}</p>
        </div>
      </div>
    `;
    document.body.appendChild(notification);

    // Play sound
    audio.playSound('achievement-unlocked');

    // Slide in animation
    setTimeout(() => notification.classList.add('active'), 100);

    // Remove after 5 seconds
    setTimeout(() => {
      notification.classList.remove('active');
      setTimeout(() => notification.remove(), 300);
    }, 5000);
  }

  getVisitedRoomsCount() {
    const visited = JSON.parse(localStorage.getItem('visited_rooms') || '[]');
    return visited.length;
  }

  checkSpeedRun() {
    const startTime = localStorage.getItem('exploration_start_time');
    if (!startTime) return false;

    const elapsed = Date.now() - parseInt(startTime);
    return elapsed < 15 * 60 * 1000 && easterEggManager.getFoundCount() === 9;
  }
}

const achievementSystem = new AchievementSystem();

// Check achievements after every easter egg found
document.addEventListener('easteregg:found', () => {
  achievementSystem.check();
});
```

**Achievement UI**:
```css
.achievement-unlocked {
  position: fixed;
  top: 20px;
  right: -400px;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  border: 2px solid #ffd700;
  border-radius: 15px;
  padding: 20px;
  width: 350px;
  z-index: 10001;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
  transition: right 0.4s ease;
}

.achievement-unlocked.active {
  right: 20px;
}

.achievement-content {
  display: flex;
  gap: 15px;
  align-items: center;
}

.achievement-icon {
  font-size: 48px;
  flex-shrink: 0;
}

.achievement-text h3 {
  color: #ffd700;
  font-size: 16px;
  margin: 0 0 5px 0;
  text-transform: uppercase;
}

.achievement-title {
  color: white;
  font-size: 18px;
  font-weight: 700;
  margin: 0 0 5px 0;
}

.achievement-desc {
  color: #ccc;
  font-size: 14px;
  margin: 0;
}
```

---

## 9. Image Generation for Room Backgrounds

### AI Image Generation

**Recommended Services**:
1. **Midjourney** (Best quality, paid)
2. **DALL-E 3** (OpenAI, good for specific styles)
3. **Stable Diffusion** (Open source, free)
4. **Leonardo.AI** (Game assets focused)

**Prompt Engineering for Isometric Rooms**:

```text
TEMPLATE:
[ROOM TYPE], isometric perspective, pixel art style, cozy anime aesthetics,
warm lighting, detailed interior, soft shadows, kawaii vibes,
pastel color palette, high detail, 4K resolution,
--ar 1:1 --style anime --quality 2
```

**Example Prompts**:

```text
1. Lilith's Room:
"Teenage girl's bedroom, isometric view, anime style, pink and purple color scheme,
desk with computer, bookshelf with manga, bed with plushies, window with city view,
fairy lights, posters on wall, cozy atmosphere, soft ambient lighting,
pixel art details, kawaii aesthetic, --ar 1:1 --style anime"

2. Parents' Room:
"Adult bedroom, isometric perspective, warm and cozy, double bed with two people
sleeping peacefully, family photos on nightstand, soft blue lighting, peaceful
atmosphere, window with moonlight, realistic anime style, intimate and loving vibes,
--ar 1:1 --style anime --quality 2"

3. Kitchen:
"Modern kitchen, isometric view, bright and clean, cooking utensils on counter,
refrigerator with magnets, dining table, plants on windowsill, warm yellow lighting,
homey atmosphere, anime style interior, detailed appliances, cozy family kitchen,
--ar 1:1 --style anime"

4. Sauna:
"Finnish sauna interior, isometric perspective, wooden benches, steam rising,
warm amber lighting, water bucket and ladle, peaceful atmosphere, hyper-realistic
anime style, cozy and relaxing vibes, detailed wood textures,
--ar 1:1 --quality 2"

5. Pool:
"Indoor swimming pool, isometric view, crystal clear blue water, tiles reflecting
light, pool toys floating, tropical plants around edges, large windows showing sky,
bright daylight, luxury resort aesthetic, anime style architecture,
--ar 1:1 --style anime --quality 2"

6. Garden:
"Rooftop garden, isometric perspective, raised vegetable beds with tomatoes,
strawberries, watermelon vines, mandarin trees, garden path, watering can,
greenhouse in corner, sunny day, vibrant green colors, anime cottage core aesthetic,
--ar 1:1 --style anime"

7. Mall Entrance:
"Modern shopping mall entrance, isometric view, glass doors, PingoDolceGabana
signage, people walking, decorative plants, bright commercial lighting, luxury
fashion district, anime urban architecture, detailed storefront,
--ar 1:1 --style anime --quality 2"
```

**Batch Generation Script** (Python + Stable Diffusion):
```python
from diffusers import StableDiffusionPipeline
import torch

model_id = "stabilityai/stable-diffusion-2-1"
pipe = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.float16)
pipe = pipe.to("cuda")

rooms = [
    {
        "name": "lilith-room",
        "prompt": "Teenage girl's bedroom, isometric view, anime style, pink theme, desk with computer, bookshelf, bed with plushies, cozy"
    },
    {
        "name": "parents-room",
        "prompt": "Adult bedroom, isometric view, double bed, warm lighting, family photos, peaceful atmosphere, anime style"
    },
    # ... add all 25 rooms
]

for room in rooms:
    image = pipe(
        room["prompt"],
        num_inference_steps=50,
        guidance_scale=7.5,
        width=1024,
        height=1024
    ).images[0]

    image.save(f"/static/rooms/{room['name']}.png")
    print(f"Generated: {room['name']}")
```

### Prompt Engineering for Consistent Style

**Style Consistency Tips**:
1. **Use same style keywords**: "anime style", "isometric view", "soft lighting"
2. **Reference images**: Upload first generated room as style reference
3. **Fixed parameters**: Keep `--ar 1:1 --quality 2` consistent
4. **Color palette**: Define palette upfront (warm/cool/pastel)
5. **Artist references**: "in the style of Studio Ghibli", "Makoto Shinkai lighting"

**Advanced Prompt Formula**:
```text
[SUBJECT] + [PERSPECTIVE] + [ART STYLE] + [LIGHTING] + [MOOD] + [DETAILS] + [TECHNICAL]

Example:
Modern kitchen (SUBJECT)
+ isometric view (PERSPECTIVE)
+ anime pixel art style (ART STYLE)
+ warm yellow lighting (LIGHTING)
+ cozy family atmosphere (MOOD)
+ appliances, plants, dining table (DETAILS)
+ 4K, high detail, --ar 1:1 (TECHNICAL)
```

### Image Optimization Techniques

**Compression Workflow**:
```bash
# ImageMagick for batch processing
convert input.png -strip -quality 85 -resize 1024x1024 output.jpg

# Modern WebP format (better compression)
cwebp -q 80 input.png -o output.webp

# AVIF format (best compression, 2025 standard)
avifenc -s 6 -y 420 input.png output.avif
```

**Responsive Image Loading**:
```html
<picture>
  <source srcset="/static/rooms/lilith-room.avif" type="image/avif">
  <source srcset="/static/rooms/lilith-room.webp" type="image/webp">
  <img src="/static/rooms/lilith-room.jpg" alt="Lilith's Room" loading="lazy">
</picture>
```

**JavaScript Compression**:
```javascript
async function compressImage(file, maxWidth = 1024, quality = 0.8) {
  return new Promise((resolve) => {
    const img = new Image();
    img.onload = () => {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');

      let width = img.width;
      let height = img.height;

      if (width > maxWidth) {
        height = (height * maxWidth) / width;
        width = maxWidth;
      }

      canvas.width = width;
      canvas.height = height;

      ctx.drawImage(img, 0, 0, width, height);

      canvas.toBlob((blob) => {
        resolve(blob);
      }, 'image/webp', quality);
    };
    img.src = URL.createObjectURL(file);
  });
}
```

**Optimization Checklist**:
- [ ] Convert to WebP/AVIF
- [ ] Resize to 1024x1024 max
- [ ] Strip metadata (EXIF, etc.)
- [ ] Target file size: <300KB per room
- [ ] Use progressive JPEGs
- [ ] Lazy load off-screen images
- [ ] Preload first 3 rooms
- [ ] Use CDN for serving (Cloudflare, etc.)

### Responsive Image Loading

**Progressive Loading Strategy**:
```javascript
class ProgressiveImageLoader {
  constructor() {
    this.lowResCache = new Map();
    this.highResCache = new Map();
  }

  async loadRoom(roomId) {
    // Load low-res placeholder first
    const lowRes = await this.loadLowRes(roomId);
    this.displayImage(roomId, lowRes);

    // Then load high-res
    const highRes = await this.loadHighRes(roomId);
    this.displayImage(roomId, highRes);
  }

  async loadLowRes(roomId) {
    if (this.lowResCache.has(roomId)) {
      return this.lowResCache.get(roomId);
    }

    const response = await fetch(`/static/rooms/${roomId}-thumb.webp`);
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);

    this.lowResCache.set(roomId, url);
    return url;
  }

  async loadHighRes(roomId) {
    if (this.highResCache.has(roomId)) {
      return this.highResCache.get(roomId);
    }

    const response = await fetch(`/static/rooms/${roomId}.webp`);
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);

    this.highResCache.set(roomId, url);
    return url;
  }

  displayImage(roomId, imageUrl) {
    const room = document.querySelector(`[data-room="${roomId}"]`);
    const background = room.querySelector('.room-background');

    background.style.backgroundImage = `url('${imageUrl}')`;
  }
}

const imageLoader = new ProgressiveImageLoader();
```

**CSS Blur-Up Effect**:
```css
.room-background {
  background-size: cover;
  background-position: center;
  filter: blur(20px);
  transition: filter 0.3s ease;
}

.room-background.loaded {
  filter: blur(0);
}
```

---

## 10. Performance Optimization

### Lazy Loading Images

**Native Lazy Loading**:
```html
<img src="/static/rooms/room-1.webp" loading="lazy" alt="Room 1">
```

**Intersection Observer**:
```javascript
const imageObserver = new IntersectionObserver((entries, observer) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const img = entry.target;

      // Load image
      if (img.dataset.src) {
        img.src = img.dataset.src;
        img.classList.add('loaded');
        observer.unobserve(img);
      }
    }
  });
}, {
  rootMargin: '50px' // Start loading 50px before visible
});

// Observe all lazy images
document.querySelectorAll('img[data-src]').forEach(img => {
  imageObserver.observe(img);
});
```

### Virtual Scrolling for 25 Rooms

**Efficient Room Rendering**:
```javascript
class VirtualRoomScroller {
  constructor() {
    this.totalRooms = 25;
    this.roomHeight = window.innerHeight;
    this.visibleRooms = 3;
    this.currentIndex = 0;
    this.rooms = [];
    this.container = document.querySelector('.rooms-container');

    this.init();
  }

  init() {
    // Create room pool (only render 3 at a time)
    for (let i = 0; i < this.visibleRooms; i++) {
      const room = this.createRoomElement(i);
      this.rooms.push(room);
      this.container.appendChild(room);
    }

    // Set container height for scrollbar
    this.container.style.height = `${this.totalRooms * this.roomHeight}px`;

    // Listen for scroll
    window.addEventListener('scroll', () => this.onScroll());
  }

  onScroll() {
    const scrollY = window.scrollY;
    const newIndex = Math.floor(scrollY / this.roomHeight);

    if (newIndex !== this.currentIndex) {
      this.currentIndex = newIndex;
      this.updateVisibleRooms();
    }
  }

  updateVisibleRooms() {
    const startIndex = Math.max(0, this.currentIndex - 1);
    const endIndex = Math.min(this.totalRooms - 1, this.currentIndex + this.visibleRooms - 1);

    // Update room pool
    this.rooms.forEach((room, poolIndex) => {
      const roomIndex = startIndex + poolIndex;

      if (roomIndex <= endIndex) {
        // Update room content
        this.updateRoomContent(room, roomIndex);
        room.style.display = 'block';
        room.style.transform = `translateY(${roomIndex * this.roomHeight}px)`;
      } else {
        room.style.display = 'none';
      }
    });
  }

  updateRoomContent(roomElement, roomIndex) {
    roomElement.dataset.room = roomIndex;
    roomElement.innerHTML = this.getRoomHTML(roomIndex);
  }

  getRoomHTML(roomIndex) {
    return `
      <div class="room-background" style="background-image: url('/static/rooms/room-${roomIndex}.webp')"></div>
      <div class="room-widgets">
        <!-- Generate widgets for this room -->
      </div>
    `;
  }

  createRoomElement(index) {
    const room = document.createElement('div');
    room.className = 'room';
    room.style.position = 'absolute';
    room.style.top = '0';
    room.style.left = '0';
    room.style.width = '100%';
    room.style.height = `${this.roomHeight}px`;
    return room;
  }
}

const virtualScroller = new VirtualRoomScroller();
```

### Asset Compression

**Build-Time Compression Script**:
```javascript
// compress-assets.js
const sharp = require('sharp');
const fs = require('fs');
const path = require('path');

async function compressImages(inputDir, outputDir) {
  const files = fs.readdirSync(inputDir);

  for (const file of files) {
    if (!file.match(/\.(jpg|jpeg|png)$/)) continue;

    const inputPath = path.join(inputDir, file);
    const outputName = file.replace(/\.(jpg|jpeg|png)$/, '.webp');
    const outputPath = path.join(outputDir, outputName);

    await sharp(inputPath)
      .resize(1024, 1024, { fit: 'cover' })
      .webp({ quality: 80 })
      .toFile(outputPath);

    console.log(`Compressed: ${file} -> ${outputName}`);
  }
}

compressImages('./static/rooms', './static/rooms/compressed');
```

**Audio Compression**:
```bash
# MP3 compression
ffmpeg -i input.mp3 -b:a 128k -ar 44100 output.mp3

# OGG compression (better quality at same bitrate)
ffmpeg -i input.mp3 -c:a libvorbis -q:a 4 output.ogg
```

**Gzip/Brotli Compression** (Server-side):
```python
# FastAPI middleware
from starlette.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Or use Brotli (better compression)
from starlette.middleware.compression import BrotliMiddleware

app.add_middleware(BrotliMiddleware, minimum_size=1000)
```

### Mobile Performance Considerations

**Mobile Detection**:
```javascript
const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);

if (isMobile) {
  // Load smaller images
  // Disable parallax
  // Reduce particle effects
  // Simplify animations
}
```

**Mobile Optimization Checklist**:
```javascript
class MobileOptimizer {
  constructor() {
    this.isMobile = this.detectMobile();

    if (this.isMobile) {
      this.applyOptimizations();
    }
  }

  detectMobile() {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
  }

  applyOptimizations() {
    // Reduce image quality
    this.useSmallImages();

    // Disable expensive effects
    this.disableParallax();
    this.reduceAnimations();

    // Adjust audio settings
    this.reduceSoundQuality();

    // Simplify UI
    this.simplifyNavigation();
  }

  useSmallImages() {
    document.querySelectorAll('img[data-src]').forEach(img => {
      const src = img.dataset.src;
      img.dataset.src = src.replace('.webp', '-mobile.webp');
    });
  }

  disableParallax() {
    document.querySelectorAll('.parallax-layer').forEach(layer => {
      layer.style.transform = 'none';
    });
  }

  reduceAnimations() {
    document.documentElement.style.setProperty('--animation-duration', '0.15s');
  }

  reduceSoundQuality() {
    audio.setMusicVolume(0.2); // Lower volume
  }

  simplifyNavigation() {
    // Use bottom bar instead of side navigation
    document.querySelector('.layer-switcher').classList.add('mobile-mode');
  }
}

const mobileOptimizer = new MobileOptimizer();
```

**Touch Optimization**:
```css
/* Larger tap targets for mobile */
@media (max-width: 768px) {
  .widget {
    min-width: 80px;
    min-height: 80px;
  }

  .modal-close {
    width: 60px;
    height: 60px;
    font-size: 40px;
  }

  /* Prevent double-tap zoom */
  * {
    touch-action: manipulation;
  }
}
```

**Service Worker for Offline Support**:
```javascript
// sw.js
const CACHE_NAME = 'dcmaidbot-v1';
const urlsToCache = [
  '/',
  '/static/styles.css',
  '/static/app.js',
  '/static/rooms/room-1.webp',
  '/static/sounds/bgm.mp3'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => response || fetch(event.request))
  );
});
```

---

## Summary & Recommendations

### Priority Libraries
1. **GSAP + ScrollTrigger** - Best smooth scroll solution
2. **Web Audio API** - Native, no dependencies
3. **Intersection Observer** - Native, lazy loading

### Key Performance Tips
- Virtual scroll for 25 rooms (render 3 at a time)
- WebP/AVIF images < 300KB each
- Lazy load everything except first room
- Preload audio files
- Use CSS transforms over position changes
- Debounce scroll/hover events

### Mobile Optimization
- Detect mobile: Load smaller assets
- Touch-friendly: 44px minimum tap targets
- Simplified animations: Shorter durations
- Service Worker: Offline support

### Accessibility
- Focus trap in modals
- ARIA attributes
- Keyboard navigation
- Alt text for images
- Screen reader announcements for discoveries

### Development Workflow
1. Generate room images with AI (Midjourney/Stable Diffusion)
2. Optimize images (WebP, <300KB)
3. Build HTML structure with virtual scroller
4. Add CSS animations and effects
5. Implement audio system
6. Add easter egg mechanics
7. Test on mobile devices
8. Performance audit with Lighthouse

---

## Resources & Links

### Design Inspiration
- Awwwards.com - Award-winning web designs
- Dribbble.com - UI/UX inspiration
- Codrops - Creative web experiments

### Libraries
- GSAP: https://greensock.com/gsap/
- Locomotive Scroll: https://locomotivemtl.github.io/locomotive-scroll/
- Particles.js: https://vincentgarreau.com/particles.js/

### Music Sources
- Pixabay Audio: https://pixabay.com/music/
- FreePD: https://freepd.com/
- Incompetech: https://incompetech.com/music/

### Image Optimization
- Squoosh.app - Google's image optimizer
- TinyPNG.com - PNG/JPG compression
- ImageOptim - Mac desktop app

### Performance Testing
- Lighthouse - Chrome DevTools
- WebPageTest.org - Detailed performance analysis
- PageSpeed Insights - Google's tool

---

**End of Research Document**

**Next Steps**: Begin implementation of Phase 1 (Welcome Modal + Music System)
