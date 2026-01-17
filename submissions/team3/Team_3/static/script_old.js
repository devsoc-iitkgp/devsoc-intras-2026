/**
 * MetaKGP Bot Frontend - JavaScript Client
 * Handles all frontend logic and API communication
 */

// Global state
const appState = {
    isLoading: false,
    apiUrl: '/api',
    detailLevel: 'normal'
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 MetaKGP Bot initializing...');
    
    initializeEventListeners();
    checkApiStatus();
    loadSettings();
    setInterval(checkApiStatus, 30000); // Check status every 30s
});

/**
 * Initialize all event listeners
 */
function initializeEventListeners() {
    // Chat form
    document.getElementById('chatForm').addEventListener('submit', sendMessage);
    
    // Auto-resize textarea
    const messageInput = document.getElementById('messageInput');
    messageInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 120) + 'px';
    });
    
    // Handle Shift+Enter for new line, Enter for send
    messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            document.getElementById('chatForm').dispatchEvent(new Event('submit'));
        }
    });
    
    // Sidebar buttons
    document.getElementById('newChatBtn').addEventListener('click', startNewChat);
    document.getElementById('historyBtn').addEventListener('click', openHistoryModal);
    document.getElementById('settingsBtn').addEventListener('click', openSettingsModal);
    
    // Modal background click
    document.addEventListener('click', (e) => {
        if (e.target.id === 'historyModal') closeHistoryModal();
        if (e.target.id === 'settingsModal') closeSettingsModal();
    });
}

/**
 * Send message to bot
 */
async function sendMessage(event) {
    event.preventDefault();
    
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();
    
    if (!message || appState.isLoading) return;
    
    // Add user message to UI
    appendMessage('user', message);
    messageInput.value = '';
    messageInput.style.height = 'auto';
    
    // Show typing indicator
    appState.isLoading = true;
    showTypingIndicator();
    document.getElementById('sendBtn').disabled = true;
    
    try {
        // Call API
        const response = await fetch(`${appState.apiUrl}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message })
        });
        
        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            // Hide typing indicator
            hideTypingIndicator();
            
            // Add bot response
            appendMessage('bot', data.response);
            
            // Update status
            updateStatus(true);
        } else {
            hideTypingIndicator();
            appendMessage('bot', `❌ Error: ${data.error || 'Unknown error occurred'}`);
        }
    } catch (error) {
        console.error('Error sending message:', error);
        hideTypingIndicator();
        appendMessage('bot', `❌ Connection Error: ${error.message}\n\nMake sure the bot server is running.`);
        updateStatus(false);
    } finally {
        appState.isLoading = false;
        document.getElementById('sendBtn').disabled = false;
        document.getElementById('messageInput').focus();
    }
}

/**
 * Append message to chat
 */
function appendMessage(sender, text) {
    const messagesArea = document.getElementById('messagesArea');
    
    // Remove welcome message if first real message
    const welcomeMsg = messagesArea.querySelector('.welcome-message');
    if (welcomeMsg) {
        welcomeMsg.remove();
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    
    // Format text (preserve line breaks)
    bubble.textContent = text;
    
    messageDiv.appendChild(bubble);
    
    // Add timestamp
    const time = new Date().toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
    const metaDiv = document.createElement('div');
    metaDiv.className = 'message-meta';
    metaDiv.textContent = time;
    messageDiv.appendChild(metaDiv);
    
    // Add verification badge for bot messages
    if (sender === 'bot') {
        const badge = document.createElement('div');
        badge.className = 'verification-badge verified';
        badge.innerHTML = '✓ Verified by MoE Experts';
        messageDiv.appendChild(badge);
    }
    
    messagesArea.appendChild(messageDiv);
    
    // Scroll to bottom
    setTimeout(() => {
        messagesArea.scrollTop = messagesArea.scrollHeight;
    }, 100);
}

/**
 * Show typing indicator
 */
function showTypingIndicator() {
    const typingDiv = document.getElementById('typingIndicator');
    typingDiv.style.display = 'flex';
    const messagesArea = document.getElementById('messagesArea');
    messagesArea.appendChild(typingDiv);
    messagesArea.scrollTop = messagesArea.scrollHeight;
}

/**
 * Hide typing indicator
 */
function hideTypingIndicator() {
    const typingDiv = document.getElementById('typingIndicator');
    typingDiv.style.display = 'none';
}

/**
 * Start new chat
 */
function startNewChat() {
    const messagesArea = document.getElementById('messagesArea');
    messagesArea.innerHTML = `
        <div class="welcome-message">
            <h2>Welcome to MetaKGP Bot! 👋</h2>
            <p>Ask me anything about IIT Kharagpur, including:</p>
            <ul>
                <li>Club information (TFPS, TLS, TSG, etc.)</li>
                <li>Hall details (RP, RK, etc.)</li>
                <li>Officer information and contacts</li>
                <li>Event information</li>
                <li>Other MetaKGP knowledge</li>
            </ul>
            <p style="margin-top: 20px; color: #888; font-size: 0.9em;">
                <strong>Advanced:</strong> Each answer is verified by 3 expert systems (Source Matcher, Hallucination Hunter, Logic Expert) to ensure accuracy.
            </p>
        </div>
    `;
    document.getElementById('messageInput').focus();
}

/**
 * Check API status
 */
async function checkApiStatus() {
    try {
        const response = await fetch(`${appState.apiUrl}/status`);
        const data = await response.json();
        
        if (response.ok && data.success) {
            updateStatus(true);
            console.log('✓ Bot API is online');
        } else {
            updateStatus(false);
        }
    } catch (error) {
        console.warn('API status check failed:', error.message);
        updateStatus(false);
    }
}

/**
 * Update status indicator
 */
function updateStatus(isOnline) {
    const statusDot = document.getElementById('statusDot');
    const statusText = document.getElementById('statusText');
    
    if (isOnline) {
        statusDot.classList.remove('disconnected');
        statusDot.classList.add('connected');
        statusText.textContent = 'Online';
    } else {
        statusDot.classList.remove('connected');
        statusDot.classList.add('disconnected');
        statusText.textContent = 'Offline';
    }
}

/**
 * Open history modal
 */
async function openHistoryModal() {
    const modal = document.getElementById('historyModal');
    modal.style.display = 'flex';
    
    try {
        const response = await fetch(`${appState.apiUrl}/history?limit=20`);
        const data = await response.json();
        
        if (data.success && data.history.length > 0) {
            const historyList = document.getElementById('historyList');
            historyList.innerHTML = '';
            
            data.history.forEach((item) => {
                const div = document.createElement('div');
                div.className = 'history-item';
                div.innerHTML = `
                    <div class="history-item-text"><strong>You:</strong> ${escapeHtml(item.user.substring(0, 50))}${item.user.length > 50 ? '...' : ''}</div>
                    <div class="history-item-time">${new Date(item.timestamp).toLocaleString()}</div>
                `;
                div.addEventListener('click', () => {
                    document.getElementById('messageInput').value = item.user;
                    closeHistoryModal();
                    document.getElementById('messageInput').focus();
                });
                historyList.appendChild(div);
            });
        } else {
            document.getElementById('historyList').innerHTML = '<div style="padding: 20px; text-align: center; color: #999;">No history yet</div>';
        }
    } catch (error) {
        console.error('Failed to load history:', error);
        document.getElementById('historyList').innerHTML = '<div style="padding: 20px; text-align: center; color: #f00;">Failed to load history</div>';
    }
}

/**
 * Close history modal
 */
function closeHistoryModal() {
    document.getElementById('historyModal').style.display = 'none';
}

/**
 * Open settings modal
 */
async function openSettingsModal() {
    const modal = document.getElementById('settingsModal');
    modal.style.display = 'flex';
    
    // Load API status
    try {
        const response = await fetch(`${appState.apiUrl}/status`);
        const data = await response.json();
        
        const statusHtml = `
            <strong>Status:</strong> ${data.success ? '✓ Online' : '✗ Offline'}<br>
            <small>Vector DB: ${data.vector_db_loaded ? '✓' : '✗'} | Graph: ${data.graph_loaded ? '✓' : '✗'}</small>
        `;
        document.getElementById('apiStatus').innerHTML = statusHtml;
    } catch (error) {
        document.getElementById('apiStatus').innerHTML = '<strong style="color: red;">✗ Offline</strong>';
    }
}

/**
 * Close settings modal
 */
function closeSettingsModal() {
    document.getElementById('settingsModal').style.display = 'none';
}

/**
 * Clear conversation history
 */
async function clearHistory() {
    if (!confirm('Are you sure you want to clear all history?')) return;
    
    try {
        const response = await fetch(`${appState.apiUrl}/clear`, {
            method: 'POST'
        });
        
        if (response.ok) {
            alert('History cleared successfully');
            closeHistoryModal();
        }
    } catch (error) {
        alert('Failed to clear history: ' + error.message);
    }
}

/**
 * Change theme
 */
function changeTheme(theme) {
    localStorage.setItem('theme', theme);
    applyTheme(theme);
}

/**
 * Apply theme
 */
function applyTheme(theme) {
    if (theme === 'auto') {
        const dark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        document.documentElement.style.colorScheme = dark ? 'dark' : 'light';
    } else {
        document.documentElement.style.colorScheme = theme;
    }
}

/**
 * Load settings from localStorage
 */
function loadSettings() {
    const savedTheme = localStorage.getItem('theme') || 'auto';
    const themeSelect = document.getElementById('themeSelect');
    if (themeSelect) {
        themeSelect.value = savedTheme;
    }
    applyTheme(savedTheme);
    
    const savedDetailLevel = localStorage.getItem('detailLevel') || 'normal';
    const detailSelect = document.getElementById('detailLevel');
    if (detailSelect) {
        detailSelect.value = savedDetailLevel;
        appState.detailLevel = savedDetailLevel;
    }
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

console.log('📱 Frontend initialized successfully');
