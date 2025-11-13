/**
 * Simple Productivity Buddy - Background Script with 1-Minute Timer and URL Redirection
 * Analyzes URLs after user spends 1 minute on the tab. Redirects distracting tabs.
 */

const PYTHON_SERVICE_URL = 'http://localhost:5000';

// Single timer management - reset on every tab switch
let activeTimer = null;
let currentTabId = null;
let lastKnownGoodUrl = 'chrome://newtab/'; // Track last non-distracting URL

console.log('🤖 Simple Productivity Buddy with 1-minute timer and redirection loaded!');

// Helper function to clear the current timer
function clearCurrentTimer() {
    if (activeTimer) {
        clearTimeout(activeTimer);
        activeTimer = null;
        console.log('⏰ Timer cleared');
    }
}

// Helper function to start 1-minute timer for current tab
function startTimer(tabId, url, title) {
    // Clear any existing timer for this tab
    clearCurrentTimer();
    
    currentTabId = tabId;
    console.log(`⏰ Starting 1-minute timer for: ${url}`);
    
    activeTimer = setTimeout(async () => {
        try {
            // Only analyze if this tab is still active
            if (currentTabId === tabId) {
                console.log(`✅ 1 minute completed! Analyzing: ${url}`);
                await analyzeUrlForDistraction(url, title, tabId);
            } else {
                console.log('❌ Tab changed during timer, skipping analysis');
            }
        } catch (error) {
            console.error('❌ Timer error:', error);
        } finally {
            activeTimer = null;
        }
    }, 10000); // 1 minute = 60000ms
}

// Send URL to Python service for distraction analysis
async function analyzeUrlForDistraction(url, title, tabId) {
    try {
        console.log(`🧠 Analyzing URL: ${url}`);
        
        const response = await fetch(`${PYTHON_SERVICE_URL}/analyze-distraction`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                url: url,
                title: title,
                timestamp: new Date().toISOString()
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            console.log('🧠 Analysis result:', result);
            
            // If it's a distraction, redirect the tab
            if (result.action === 'close_tab') { // Server still sends 'close_tab' but we interpret as redirect
                console.log('🚫 DISTRACTION DETECTED! Redirecting tab to last known good URL:', lastKnownGoodUrl);
                try {
                    await chrome.tabs.update(tabId, {url: lastKnownGoodUrl});
                    console.log('✅ Tab redirected successfully');
                } catch (redirectError) {
                    console.error('❌ Failed to redirect tab:', redirectError);
                }
            } else {
                console.log('✅ URL allowed:', url);
                lastKnownGoodUrl = url; // Update last known good URL
            }
        } else {
            console.error('❌ Failed to analyze URL:', response.status);
        }
        
    } catch (error) {
        console.error('❌ Error analyzing URL:', error);
    }
}

// Listen for tab activation (user switches to a tab)
chrome.tabs.onActivated.addListener(async (activeInfo) => {
    try {
        const tab = await chrome.tabs.get(activeInfo.tabId);
        
        // Skip YouTube - let onUpdated handle it
        if (tab.url && tab.url.includes('youtube.com')) {
            console.log('⏭️ Skipping YouTube tab - will handle on URL update');
            clearCurrentTimer(); // Still clear timer for any other active tab
            return;
        }
        
        // Only process valid URLs (skip chrome:// pages, extensions, etc.)
        if (tab.url && !tab.url.startsWith('chrome://') && !tab.url.startsWith('chrome-extension://')) {
            console.log(`🎯 Tab switched to: ${tab.url}`);
            startTimer(activeInfo.tabId, tab.url, tab.title || 'No title');
        } else {
            clearCurrentTimer(); // Clear timer for invalid URLs
        }
    } catch (error) {
        console.error('❌ Error handling tab activation:', error);
    }
});

// Listen for tab updates (when URL changes in same tab)
chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
    // Only process when tab is complete, active, and URL changed
    if (changeInfo.status === 'complete' && tab.active && tab.url) {
        // Skip internal pages
        if (!tab.url.startsWith('chrome://') && !tab.url.startsWith('chrome-extension://')) {
            console.log(`🔄 Active tab URL updated: ${tab.url}`);
            startTimer(tabId, tab.url, tab.title || 'No title');
        }
    }
});

// Clean up timer when tab is closed
chrome.tabs.onRemoved.addListener((tabId, removeInfo) => {
    if (currentTabId === tabId) {
        console.log(`🗑️ Active tab ${tabId} was closed, clearing timer`);
        clearCurrentTimer();
    }
});

console.log('✅ 1-minute timer and redirection system active!');
