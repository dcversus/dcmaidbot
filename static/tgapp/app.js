// 🎮 DC Maidbot Game Creator - Webapp JavaScript
// Event emitter and Telegram Web Apps SDK integration

class GameCreatorApp {
    constructor() {
        this.telegram = null;
        this.isAuthenticated = false;
        this.authToken = null;
        this.apiBaseUrl = window.location.origin + '/api';

        this.init();
    }

    async init() {
        console.log('🚀 Initializing DC Maidbot Game Creator...');

        // Initialize Telegram Web App
        this.initTelegram();

        // Set up event listeners
        this.setupEventListeners();

        // Check for stored auth token
        this.checkStoredAuth();

        console.log('✅ App initialized successfully!');
    }

    initTelegram() {
        // Initialize Telegram Web App if available
        if (window.Telegram && window.Telegram.WebApp) {
            this.telegram = window.Telegram.WebApp;
            this.telegram.ready();
            this.telegram.expand();

            console.log('📱 Telegram Web App initialized');

            // Set theme colors
            this.telegram.setHeaderColor('#FF6B9D');
            this.telegram.setBackgroundColor('#F8F9FA');

            // Enable haptic feedback
            this.telegram.enableClosingConfirmation();

            // Update status
            this.updateStatus('connection', '📱 Telegram connected');

            // Get user info if available
            if (this.telegram.initDataUnsafe && this.telegram.initDataUnsafe.user) {
                const user = this.telegram.initDataUnsafe.user;
                this.updateStatus('user', `👤 ${user.first_name}`);
                console.log('👤 Telegram user:', user);
            }
        } else {
            console.warn('⚠️ Telegram Web App not available, running in standalone mode');
            this.updateStatus('connection', '🌐 Standalone mode');
            this.updateStatus('user', '👤 Demo User');
        }
    }

    setupEventListeners() {
        // Authentication
        const unlockBtn = document.getElementById('unlock-btn');
        const tokenInput = document.getElementById('token-input');

        if (unlockBtn) {
            unlockBtn.addEventListener('click', () => this.handleAuth());
        }

        if (tokenInput) {
            tokenInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.handleAuth();
                }
            });
        }

        // Game buttons
        document.querySelectorAll('[data-action]').forEach(button => {
            button.addEventListener('click', (e) => {
                const action = e.target.dataset.action;
                this.handleGameAction(action);
            });
        });

        // File editor
        const loadFileBtn = document.getElementById('load-file-btn');
        const saveFileBtn = document.getElementById('save-file-btn');

        if (loadFileBtn) {
            loadFileBtn.addEventListener('click', () => this.loadFile());
        }

        if (saveFileBtn) {
            saveFileBtn.addEventListener('click', () => this.saveFile());
        }

        // Links
        const docsLink = document.getElementById('docs-link');
        const siteLink = document.getElementById('site-link');

        if (docsLink) {
            docsLink.addEventListener('click', (e) => {
                e.preventDefault();
                this.openLink('https://docs.dcmaidbot.com');
            });
        }

        if (siteLink) {
            siteLink.addEventListener('click', (e) => {
                e.preventDefault();
                this.openLink('https://dcmaidbot.com');
            });
        }
    }

    async handleAuth() {
        const tokenInput = document.getElementById('token-input');
        const token = tokenInput.value.trim();
        const errorDiv = document.getElementById('auth-error');

        if (!token) {
            this.showError('auth-error', '🔑 Please enter a token!');
            return;
        }

        this.showLoading(true);

        try {
            // Send authentication event
            await this.emitEvent('auth_attempt', {
                token: token.substring(0, 8) + '...' // Only send prefix for security
            });

            // Validate token with server
            const response = await this.apiCall('/auth/validate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.success) {
                this.authToken = token;
                this.isAuthenticated = true;
                localStorage.setItem('authToken', token);

                // Hide auth section, show workshop
                this.showSection('workshop-section');
                this.hideSection('auth-section');

                // Send successful auth event
                await this.emitEvent('auth_success', {
                    admin_id: response.admin_id,
                    timestamp: Date.now()
                });

                this.hapticFeedback('success');
                console.log('🔐 Authentication successful!');

            } else {
                throw new Error(response.message || 'Authentication failed');
            }

        } catch (error) {
            console.error('❌ Authentication failed:', error);
            this.showError('auth-error', '😔 That key doesn\'t work! Try again!');
            this.hapticFeedback('error');

            // Send failed auth event
            await this.emitEvent('auth_failed', {
                error: error.message,
                timestamp: Date.now()
            });

        } finally {
            this.showLoading(false);
        }
    }

    async handleGameAction(action) {
        console.log(`🎮 Game action: ${action}`);

        this.hapticFeedback('light');

        // Emit event for the action
        await this.emitEvent('game_action', {
            action: action,
            timestamp: Date.now(),
            user_agent: navigator.userAgent
        });

        // Handle specific actions
        switch (action) {
            case 'domik_tool':
                this.toggleFileEditor();
                break;

            case 'create_quiz':
                this.showFileEditor('games/new_quiz.json', this.getQuizTemplate());
                break;

            case 'create_story':
                this.showFileEditor('games/new_story.json', this.getStoryTemplate());
                break;

            case 'create_puzzle':
                this.showFileEditor('games/new_puzzle.json', this.getPuzzleTemplate());
                break;

            case 'create_adventure':
                this.showFileEditor('games/new_adventure.json', this.getAdventureTemplate());
                break;

            case 'test_game':
                this.testCurrentGame();
                break;

            case 'list_files':
                this.listFiles();
                break;

            case 'create_folder':
                this.createFolder();
                break;

            case 'show_help':
                this.showHelp();
                break;

            case 'open_docs':
                this.openLink('https://docs.dcmaidbot.com');
                break;

            default:
                console.log(`Unknown action: ${action}`);
        }
    }

    toggleFileEditor() {
        const editor = document.getElementById('file-editor');
        editor.classList.toggle('hidden');

        if (!editor.classList.contains('hidden')) {
            editor.classList.add('fade-in');
        }
    }

    showFileEditor(path, content = '') {
        const editor = document.getElementById('file-editor');
        const pathInput = document.getElementById('file-path');
        const contentArea = document.getElementById('file-content');

        pathInput.value = path;
        contentArea.value = content;
        editor.classList.remove('hidden');
        editor.classList.add('fade-in');

        // Focus the content area
        setTimeout(() => contentArea.focus(), 100);
    }

    async loadFile() {
        const pathInput = document.getElementById('file-path');
        const contentArea = document.getElementById('file-content');
        const statusDiv = document.getElementById('file-status');
        const path = pathInput.value.trim();

        if (!path) {
            this.showStatus('file-status', 'error', '📂 Please enter a file path!');
            return;
        }

        this.showLoading(true);

        try {
            // Emit file load event
            await this.emitEvent('file_load_attempt', { path });

            const response = await this.apiCall('/files/read', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.authToken}`
                },
                body: JSON.stringify({ path })
            });

            if (response.success) {
                contentArea.value = response.content;
                this.showStatus('file-status', 'success', `✅ File loaded: ${path}`);

                // Emit successful load event
                await this.emitEvent('file_loaded', {
                    path,
                    size: response.content.length,
                    timestamp: Date.now()
                });

            } else {
                throw new Error(response.message || 'Failed to load file');
            }

        } catch (error) {
            console.error('❌ Failed to load file:', error);
            this.showStatus('file-status', 'error', `❌ Error: ${error.message}`);
        } finally {
            this.showLoading(false);
        }
    }

    async saveFile() {
        const pathInput = document.getElementById('file-path');
        const contentArea = document.getElementById('file-content');
        const path = pathInput.value.trim();
        const content = contentArea.value;

        if (!path) {
            this.showStatus('file-status', 'error', '📂 Please enter a file path!');
            return;
        }

        this.showLoading(true);

        try {
            // Emit file save event
            await this.emitEvent('file_save_attempt', {
                path,
                size: content.length
            });

            const response = await this.apiCall('/files/write', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.authToken}`
                },
                body: JSON.stringify({ path, content })
            });

            if (response.success) {
                this.showStatus('file-status', 'success', `💾 File saved: ${path}`);

                // Emit successful save event
                await this.emitEvent('file_saved', {
                    path,
                    size: content.length,
                    timestamp: Date.now()
                });

                this.hapticFeedback('success');

            } else {
                throw new Error(response.message || 'Failed to save file');
            }

        } catch (error) {
            console.error('❌ Failed to save file:', error);
            this.showStatus('file-status', 'error', `❌ Error: ${error.message}`);
            this.hapticFeedback('error');
        } finally {
            this.showLoading(false);
        }
    }

    async testCurrentGame() {
        const pathInput = document.getElementById('file-path');
        const path = pathInput.value.trim();

        if (!path) {
            this.showStatus('file-status', 'error', '📂 Please enter a game file path!');
            return;
        }

        await this.emitEvent('game_test', { path });
        this.showStatus('file-status', 'info', `🎮 Testing game: ${path}`);
    }

    async listFiles() {
        await this.emitEvent('list_files_request', {});
        this.showStatus('file-status', 'info', '📋 Requesting file list...');
    }

    async createFolder() {
        const folderName = prompt('📁 Enter folder name:');
        if (folderName) {
            await this.emitEvent('create_folder', { name: folderName });
            this.showStatus('file-status', 'info', `📁 Creating folder: ${folderName}`);
        }
    }

    showHelp() {
        const helpText = `
🎮 DC Maidbot Game Creator Help!

🔐 Authentication: Use your admin token to access the workshop

🛠️ Game Creation:
• Click any game button to create a new game
• Use the Domik tool to edit files directly
• Games are saved as JSON files

📁 File Operations:
• Load: Read existing game files
• Save: Write your game files
• All files are stored securely

🎯 Quick Actions:
• List Files: See all your games
• Create Folder: Organize your games
• Documentation: Get detailed help

Need more help? Check the docs! 📚
        `;

        alert(helpText.trim());
        this.emitEvent('help_shown', {});
    }

    // Event emission
    async emitEvent(type, data) {
        const event = {
            id: this.generateEventId(),
            type: type,
            data: data,
            timestamp: Date.now(),
            user_agent: navigator.userAgent,
            session_id: this.getSessionId()
        };

        try {
            const response = await fetch(`${this.apiBaseUrl}/events`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.authToken || 'anonymous'}`
                },
                body: JSON.stringify(event)
            });

            if (!response.ok) {
                console.warn('⚠️ Failed to emit event:', response.status);
            } else {
                console.log('✅ Event emitted:', type);
            }

        } catch (error) {
            console.error('❌ Error emitting event:', error);
        }
    }

    // Utility methods
    generateEventId() {
        return `event_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    getSessionId() {
        let sessionId = sessionStorage.getItem('sessionId');
        if (!sessionId) {
            sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
            sessionStorage.setItem('sessionId', sessionId);
        }
        return sessionId;
    }

    checkStoredAuth() {
        const storedToken = localStorage.getItem('authToken');
        if (storedToken) {
            this.authToken = storedToken;
            this.isAuthenticated = true;
            this.showSection('workshop-section');
            this.hideSection('auth-section');
            console.log('🔐 Auto-authenticated with stored token');
        }
    }

    async apiCall(endpoint, options = {}) {
        const url = `${this.apiBaseUrl}${endpoint}`;
        const response = await fetch(url, options);
        return await response.json();
    }

    showSection(sectionId) {
        document.getElementById(sectionId).classList.remove('hidden');
    }

    hideSection(sectionId) {
        document.getElementById(sectionId).classList.add('hidden');
    }

    showError(elementId, message) {
        const element = document.getElementById(elementId);
        element.textContent = message;
        element.classList.remove('hidden');
        element.classList.add('fade-in');

        setTimeout(() => {
            element.classList.add('hidden');
        }, 5000);
    }

    showStatus(elementId, type, message) {
        const element = document.getElementById(elementId);
        element.textContent = message;
        element.className = `status-message ${type} fade-in`;

        setTimeout(() => {
            element.textContent = '';
            element.className = 'status-message';
        }, 3000);
    }

    showLoading(show) {
        const overlay = document.getElementById('loading-overlay');
        if (show) {
            overlay.classList.remove('hidden');
        } else {
            overlay.classList.add('hidden');
        }
    }

    updateStatus(type, message) {
        const element = document.getElementById(`${type}-status`);
        if (element) {
            element.textContent = message;
        }
    }

    hapticFeedback(type) {
        if (this.telegram && this.telegram.HapticFeedback) {
            try {
                switch (type) {
                    case 'light':
                        this.telegram.HapticFeedback.impactOccurred('light');
                        break;
                    case 'medium':
                        this.telegram.HapticFeedback.impactOccurred('medium');
                        break;
                    case 'heavy':
                        this.telegram.HapticFeedback.impactOccurred('heavy');
                        break;
                    case 'success':
                        this.telegram.HapticFeedback.notificationOccurred('success');
                        break;
                    case 'error':
                        this.telegram.HapticFeedback.notificationOccurred('error');
                        break;
                    case 'warning':
                        this.telegram.HapticFeedback.notificationOccurred('warning');
                        break;
                }
            } catch (error) {
                console.log('🔕 Haptic feedback not available');
            }
        }
    }

    openLink(url) {
        if (this.telegram) {
            this.telegram.openLink(url);
        } else {
            window.open(url, '_blank');
        }

        this.emitEvent('link_opened', { url });
    }

    // Game templates
    getQuizTemplate() {
        return JSON.stringify({
            type: "quiz",
            title: "My Awesome Quiz",
            description: "A fun quiz game!",
            questions: [
                {
                    question: "What is 2 + 2?",
                    options: ["3", "4", "5", "6"],
                    correct: 1,
                    points: 10
                }
            ],
            settings: {
                time_limit: 30,
                shuffle_questions: false,
                show_correct_answers: true
            }
        }, null, 2);
    }

    getStoryTemplate() {
        return JSON.stringify({
            type: "story",
            title: "My Adventure Story",
            description: "An interactive story!",
            start_scene: "beginning",
            scenes: {
                "beginning": {
                    text: "You are at the beginning of an adventure...",
                    choices: [
                        { text: "Go left", next_scene: "left_path" },
                        { text: "Go right", next_scene: "right_path" }
                    ]
                }
            }
        }, null, 2);
    }

    getPuzzleTemplate() {
        return JSON.stringify({
            type: "puzzle",
            title: "My Fun Puzzle",
            description: "A challenging puzzle game!",
            difficulty: "medium",
            puzzle_type: "pattern",
            grid_size: [4, 4],
            solution: [[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 0]]
        }, null, 2);
    }

    getAdventureTemplate() {
        return JSON.stringify({
            type: "adventure",
            title: "My Great Adventure",
            description: "An epic adventure game!",
            start_location: "village",
            player: {
                name: "Hero",
                health: 100,
                inventory: []
            },
            locations: {
                "village": {
                    description: "A peaceful village.",
                    exits: { north: "forest", east: "mountains" },
                    items: ["sword", "potion"]
                }
            }
        }, null, 2);
    }
}

// Initialize the app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.gameCreatorApp = new GameCreatorApp();
});

// Page visibility change handling
document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible' && window.gameCreatorApp) {
        console.log('👁️ Page became visible');
        window.gameCreatorApp.emitEvent('page_visible', { timestamp: Date.now() });
    }
});

// Handle page unload
window.addEventListener('beforeunload', () => {
    if (window.gameCreatorApp) {
        window.gameCreatorApp.emitEvent('page_unload', { timestamp: Date.now() });
    }
});

console.log('🎮 DC Maidbot Game Creator loaded successfully!');
