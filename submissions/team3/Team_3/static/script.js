/**
 * MetaKGP Bot Frontend - Enhanced JavaScript
 * Handles all frontend logic and API communication
 */

// Global state
const appState = {
    isLoading: false,
    apiUrl: '/api',
    detailLevel: 'normal',
    conversationHistory: []
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Initializing MetaKGP Bot...');
    initializeEventListeners();
    checkApiStatus();
    loadSettings();
    setInterval(checkApiStatus, 30000);
});

/**
 * Initialize all event listeners
 */
function initializeEventListeners() {
    // Chat form
    const chatForm = document.getElementById('chatForm');
    if (chatForm) {
        chatForm.addEventListener('submit', sendMessage);
    }
    
    // Auto-resize textarea
    const messageInput = document.getElementById('messageInput');
    if (messageInput) {
        messageInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 120) + 'px';
        });
        
        // Handle Shift+Enter for new line, Enter for send
        messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                chatForm.dispatchEvent(new Event('submit'));
            }
        });
    }
    
    // Sidebar buttons
    const newChatBtn = document.getElementById('newChatBtn');
    const historyBtn = document.getElementById('historyBtn');
    const settingsBtn = document.getElementById('settingsBtn');
    
    if (newChatBtn) newChatBtn.addEventListener('click', startNewChat);
    if (historyBtn) historyBtn.addEventListener('click', openHistoryModal);
    if (settingsBtn) settingsBtn.addEventListener('click', openSettingsModal);
    
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
    
    // Store in history
    appState.conversationHistory.push({
        role: 'user',
        content: message,
        timestamp: new Date()
    });
    
    // Show typing indicator
    appState.isLoading = true;
    showTypingIndicator();
    document.getElementById('sendBtn').disabled = true;
    
    try {
        console.log('📤 Sending message to API:', message);
        
        // Call API
        const response = await fetch(`${appState.apiUrl}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message })
        });
        
        console.log('📥 API Response status:', response.status);
        
        if (!response.ok) {
            throw new Error(`API error: ${response.status} ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('📊 API Response data:', data);
        
        // Hide typing indicator
        hideTypingIndicator();
        
        if (data.success || data.response) {
            // Add bot response
            const botResponse = data.response || data.message || 'No response received';
            appendMessage('bot', botResponse);
            
            // Store in history
            appState.conversationHistory.push({
                role: 'bot',
                content: botResponse,
                timestamp: new Date()
            });
            
            // Update status
            updateStatus(true);
        } else {
            const errorMsg = data.error || data.message || 'Unknown error occurred';
            appendMessage('bot', `❌ Error: ${errorMsg}`);
        }
    } catch (error) {
        console.error('❌ Error:', error);
        hideTypingIndicator();
        appendMessage('bot', `❌ Connection Error\n\n${error.message}\n\nMake sure the bot server is running on http://127.0.0.1:5000`);
        updateStatus(false);
    } finally {
        appState.isLoading = false;
        const sendBtn = document.getElementById('sendBtn');
        if (sendBtn) sendBtn.disabled = false;
        messageInput.focus();
    }
}

/**
 * Append message to chat
 */
function appendMessage(sender, text) {
    const messagesArea = document.getElementById('messagesArea');
    if (!messagesArea) return;
    
    // Remove welcome message if first real message
    const welcomeMsg = messagesArea.querySelector('.welcome-message');
    if (welcomeMsg && (sender === 'user' || sender === 'bot')) {
        welcomeMsg.remove();
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    
    // Format text - preserve line breaks and escape HTML
    const formattedText = escapeHtml(text);
    bubble.innerHTML = formattedText.replace(/\n/g, '<br>');
    
    messageDiv.appendChild(bubble);
    
    // Add timestamp
    const time = new Date().toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit',
        hour12: true
    });
    const metaDiv = document.createElement('div');
    metaDiv.className = 'message-meta';
    metaDiv.textContent = time;
    messageDiv.appendChild(metaDiv);
    
    // Add verification badge for bot messages
    if (sender === 'bot') {
        const badge = document.createElement('div');
        badge.className = 'verification-badge verified';
        badge.innerHTML = '✓ Verified';
        badge.style.marginTop = '0.5rem';
        badge.style.fontSize = '0.75rem';
        badge.style.color = 'var(--success)';
        badge.style.fontWeight = '500';
        messageDiv.appendChild(badge);
    }
    
    messagesArea.appendChild(messageDiv);
    
    // Scroll to bottom
    setTimeout(() => {
        messagesArea.scrollTop = messagesArea.scrollHeight;
    }, 100);
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Show typing indicator
 */
function showTypingIndicator() {
    const typingDiv = document.getElementById('typingIndicator');
    if (typingDiv) {
        typingDiv.style.display = 'flex';
        const messagesArea = document.getElementById('messagesArea');
        if (messagesArea && !messagesArea.contains(typingDiv)) {
            messagesArea.appendChild(typingDiv);
        }
        messagesArea.scrollTop = messagesArea.scrollHeight;
    }
}

/**
 * Hide typing indicator
 */
function hideTypingIndicator() {
    const typingDiv = document.getElementById('typingIndicator');
    if (typingDiv) {
        typingDiv.style.display = 'none';
    }
}

/**
 * Start new chat
 */
function startNewChat() {
    const messagesArea = document.getElementById('messagesArea');
    if (!messagesArea) return;
    
    appState.conversationHistory = [];
    
    messagesArea.innerHTML = `
        <div class="welcome-message">
            <div class="welcome-content">
                <h2>🎓 Welcome to MetaKGP Bot!</h2>
                <p>Your intelligent assistant for all things IIT Kharagpur</p>
                
                <div class="welcome-examples">
                    <p><strong>Try asking:</strong></p>
                    <div class="example-pills">
                        <div class="pill" onclick="document.getElementById('messageInput').value = 'Who is the VP of TFPS?'; document.getElementById('chatForm').dispatchEvent(new Event('submit'));">Who is the VP of TFPS?</div>
                        <div class="pill" onclick="document.getElementById('messageInput').value = 'Tell me about RP Hall'; document.getElementById('chatForm').dispatchEvent(new Event('submit'));">Tell me about RP Hall</div>
                        <div class="pill" onclick="document.getElementById('messageInput').value = 'What clubs are there?'; document.getElementById('chatForm').dispatchEvent(new Event('submit'));">What clubs are there?</div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    console.log('✨ New chat started');
}

/**
 * Open history modal
 */
function openHistoryModal() {
    const modal = document.getElementById('historyModal');
    const historyList = document.getElementById('historyList');
    
    if (!modal || !historyList) return;
    
    if (appState.conversationHistory.length === 0) {
        historyList.innerHTML = '<p class="empty-state">No messages yet. Start a conversation!</p>';
    } else {
        let html = '';
        appState.conversationHistory.forEach((msg, idx) => {
            const time = new Date(msg.timestamp).toLocaleTimeString('en-US', {
                hour: '2-digit',
                minute: '2-digit'
            });
            const preview = msg.content.substring(0, 50) + (msg.content.length > 50 ? '...' : '');
            html += `
                <div class="history-item">
                    <div style="font-weight: 600; color: ${msg.role === 'user' ? 'var(--primary)' : 'var(--text-primary)'}">
                        ${msg.role === 'user' ? '👤 You' : '🤖 Bot'}
                    </div>
                    <div style="font-size: 0.875rem; color: var(--text-secondary); margin: 0.25rem 0;">
                        ${preview}
                    </div>
                    <div style="font-size: 0.75rem; color: var(--text-tertiary);">
                        ${time}
                    </div>
                </div>
            `;
        });
        historyList.innerHTML = html;
    }
    
    modal.classList.add('active');
}

/**
 * Close history modal
 */
function closeHistoryModal() {
    const modal = document.getElementById('historyModal');
    if (modal) {
        modal.classList.remove('active');
    }
}

/**
 * Open settings modal
 */
function openSettingsModal() {
    const modal = document.getElementById('settingsModal');
    if (modal) {
        modal.classList.add('active');
        updateApiStatus();
    }
}

/**
 * Close settings modal
 */
function closeSettingsModal() {
    const modal = document.getElementById('settingsModal');
    if (modal) {
        modal.classList.remove('active');
    }
}

/**
 * Check API status
 */
async function checkApiStatus() {
    try {
        const response = await fetch(`${appState.apiUrl}/health`);
        const isOnline = response.ok;
        updateStatus(isOnline);
    } catch (error) {
        console.warn('⚠️ API status check failed:', error.message);
        updateStatus(false);
    }
}

/**
 * Update API status
 */
async function updateApiStatus() {
    const apiStatus = document.getElementById('apiStatus');
    if (!apiStatus) return;
    
    try {
        const response = await fetch(`${appState.apiUrl}/status`);
        if (response.ok) {
            const data = await response.json();
            apiStatus.innerHTML = `
                <span class="status-dot"></span>
                <span class="status-text">🟢 Online - Vector DB: ${data.vector_db_loaded ? '✓' : '✗'}, Graph: ${data.graph_loaded ? '✓' : '✗'}</span>
            `;
        } else {
            apiStatus.innerHTML = `<span class="status-dot offline"></span><span class="status-text">🔴 Offline</span>`;
        }
    } catch (error) {
        apiStatus.innerHTML = `<span class="status-dot offline"></span><span class="status-text">🔴 Connection Error</span>`;
    }
}

/**
 * Update status indicator
 */
function updateStatus(isOnline) {
    const indicator = document.getElementById('statusIndicator');
    if (!indicator) return;
    
    const dot = indicator.querySelector('.status-dot');
    const text = indicator.querySelector('.status-text');
    
    if (isOnline) {
        dot.classList.remove('offline');
        text.textContent = '🟢 Online';
    } else {
        dot.classList.add('offline');
        text.textContent = '🔴 Offline';
    }
}

/**
 * Change theme
 */
function changeTheme(theme) {
    localStorage.setItem('metakgp-theme', theme);
    applyTheme(theme);
}

/**
 * Apply theme
 */
function applyTheme(theme) {
    if (theme === 'auto') {
        document.documentElement.style.colorScheme = 'light dark';
        localStorage.setItem('metakgp-theme', 'auto');
    } else {
        document.documentElement.style.colorScheme = theme;
        localStorage.setItem('metakgp-theme', theme);
    }
}

/**
 * Change detail level
 */
function changeDetailLevel(level) {
    appState.detailLevel = level;
    localStorage.setItem('metakgp-detail-level', level);
    console.log('📊 Detail level changed to:', level);
}

/**
 * Load settings from localStorage
 */
function loadSettings() {
    const theme = localStorage.getItem('metakgp-theme') || 'auto';
    const detailLevel = localStorage.getItem('metakgp-detail-level') || 'normal';
    
    const themeSelect = document.getElementById('themeSelect');
    const detailSelect = document.getElementById('detailSelect');
    
    if (themeSelect) themeSelect.value = theme;
    if (detailSelect) detailSelect.value = detailLevel;
    
    applyTheme(theme);
    appState.detailLevel = detailLevel;
}
