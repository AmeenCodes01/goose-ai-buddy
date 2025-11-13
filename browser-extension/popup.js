/**
 * Productivity Buddy - Popup Script
 * Handles the popup UI and user interactions
 */

// DOM elements
const statusIcon = document.getElementById('statusIcon');
const statusText = document.getElementById('statusText');
const timer = document.getElementById('timer');
const focusBtn = document.getElementById('focusBtn');
const breakBtn = document.getElementById('breakBtn');
const stopBtn = document.getElementById('stopBtn');
const focusTime = document.getElementById('focusTime');
const sessionCount = document.getElementById('sessionCount');
const distractionsBlocked = document.getElementById('distractionsBlocked');
const connectionDot = document.getElementById('connectionDot');
const connectionText = document.getElementById('connectionText');

// Current session state
let currentSession = null;
let timerInterval = null;

// Initialize popup
document.addEventListener('DOMContentLoaded', () => {
    console.log('🤖 Productivity Buddy popup loaded');
    
    // Setup event listeners
    focusBtn.addEventListener('click', () => startFocusSession());
    breakBtn.addEventListener('click', () => startBreakSession());
    stopBtn.addEventListener('click', () => endSession());
    
    // Load initial data
    updateSessionStatus();
    updateStats();
    checkConnection();
    
    // Update every second
    setInterval(() => {
        updateSessionStatus();
        updateTimer();
    }, 1000);
    
    // Check connection every 10 seconds
    setInterval(checkConnection, 10000);
});

/**
 * Session Management
 */
async function startFocusSession() {
    console.log('🎯 Starting focus session');
    
    try {
        const response = await sendMessage({
            action: 'startFocusSession',
            duration: 25
        });
        
        if (response.success) {
            updateUI('focus');
            showNotification('Focus session started! 🎯');
        } else {
            showError('Failed to start focus session');
        }
    } catch (error) {
        console.error('❌ Error starting focus session:', error);
        showError('Could not connect to service');
    }
}

async function startBreakSession() {
    console.log('☕ Starting break session');
    
    try {
        const response = await sendMessage({
            action: 'startBreakSession',
            duration: 5
        });
        
        if (response.success) {
            updateUI('break');
            showNotification('Break time! ☕');
        } else {
            showError('Failed to start break session');
        }
    } catch (error) {
        console.error('❌ Error starting break session:', error);
        showError('Could not connect to service');
    }
}

async function endSession() {
    console.log('⏹️ Ending session');
    
    try {
        const response = await sendMessage({
            action: 'endSession'
        });
        
        if (response.success) {
            updateUI('idle');
            showNotification('Session ended');
        } else {
            showError('Failed to end session');
        }
    } catch (error) {
        console.error('❌ Error ending session:', error);
        showError('Could not connect to service');
    }
}

/**
 * UI Updates
 */
function updateUI(state) {
    switch (state) {
        case 'focus':
            statusIcon.textContent = '🎯';
            statusText.textContent = 'Focus Mode Active';
            focusBtn.disabled = true;
            breakBtn.disabled = false;
            stopBtn.disabled = false;
            break;
            
        case 'break':
            statusIcon.textContent = '☕';
            statusText.textContent = 'Break Time';
            focusBtn.disabled = false;
            breakBtn.disabled = true;
            stopBtn.disabled = false;
            break;
            
        case 'idle':
        default:
            statusIcon.textContent = '🏠';
            statusText.textContent = 'Ready to focus';
            focusBtn.disabled = false;
            breakBtn.disabled = false;
            stopBtn.disabled = true;
            break;
    }
}

function updateTimer() {
    if (!currentSession || currentSession.state === 'idle') {
        timer.textContent = '00:00';
        return;
    }
    
    const now = Date.now();
    const elapsed = Math.floor((now - currentSession.startTime) / 1000);
    const remaining = Math.max(0, (currentSession.duration * 60) - elapsed);
    
    const minutes = Math.floor(remaining / 60);
    const seconds = remaining % 60;
    
    timer.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
}

async function updateSessionStatus() {
    try {
        const response = await sendMessage({ action: 'getSessionStatus' });
        
        if (response.success && response.session) {
            currentSession = response.session;
            updateUI(currentSession.state);
        }
    } catch (error) {
        console.warn('⚠️ Could not get session status:', error);
    }
}

async function updateStats() {
    try {
        // For now, we'll use dummy data. In a real implementation,
        // this would come from the Python service
        focusTime.textContent = '0 min';
        sessionCount.textContent = '0';
        distractionsBlocked.textContent = '0';
        
        // TODO: Get real stats from background script/Python service
    } catch (error) {
        console.warn('⚠️ Could not update stats:', error);
    }
}

async function checkConnection() {
    try {
        // Try to communicate with background script
        const response = await sendMessage({ action: 'getSessionStatus' });
        
        if (response.success) {
            connectionDot.className = 'status-dot';
            connectionText.textContent = 'Connected to Python service';
        } else {
            connectionDot.className = 'status-dot disconnected';
            connectionText.textContent = 'Python service not responding';
        }
    } catch (error) {
        connectionDot.className = 'status-dot disconnected';
        connectionText.textContent = 'Service offline - start Python script';
    }
}

/**
 * Utility Functions
 */
function sendMessage(message) {
    return new Promise((resolve, reject) => {
        chrome.runtime.sendMessage(message, (response) => {
            if (chrome.runtime.lastError) {
                reject(chrome.runtime.lastError);
            } else {
                resolve(response || {});
            }
        });
    });
}

function showNotification(message) {
    // Create a simple notification in the popup
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 10px;
        right: 10px;
        background: rgba(76, 175, 80, 0.9);
        color: white;
        padding: 10px;
        border-radius: 5px;
        font-size: 12px;
        z-index: 1000;
    `;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        document.body.removeChild(notification);
    }, 3000);
}

function showError(message) {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 10px;
        right: 10px;
        background: rgba(244, 67, 54, 0.9);
        color: white;
        padding: 10px;
        border-radius: 5px;
        font-size: 12px;
        z-index: 1000;
    `;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        document.body.removeChild(notification);
    }, 3000);
}
