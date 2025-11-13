/**
 * Simple Productivity Buddy - Background Script
 * Just sends URL to Python service when user switches tabs
 */

const PYTHON_SERVICE_URL = 'http://localhost:5000';

console.log('🤖 Simple Productivity Buddy loaded!');

// Send URL to Python service
async function sendUrlToServer(url, title) {
    try {
        const response = await fetch(`${PYTHON_SERVICE_URL}/log/url`, {
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
            console.log('✅ URL logged:', result);
        } else {
            console.error('❌ Failed to log URL:', response.status);
        }
        
    } catch (error) {
        console.error('❌ Error sending URL to server:', error);
    }
}

// Listen for tab activation (user switches to a tab)
chrome.tabs.onActivated.addListener(async (activeInfo) => {
    try {
        // Get tab details
        setTimeout(async ()=>{

            const tab = await chrome.tabs.get(activeInfo.tabId);
            
            
            // Skip YouTube - let onUpdated handle it
            if (tab.url && tab.url.includes('youtube.com')) {
                return;
            }
            // Only process valid URLs (skip chrome:// pages, extensions, etc.)
            if (tab.url && !tab.url.startsWith('chrome://') && !tab.url.startsWith('chrome-extension://')) {
                console.log(`🎯 Tab switched to: ${tab.url}`);
                await sendUrlToServer(tab.url, tab.title || 'No title');
            }

        },5000)
    } catch (errr) {
        console.error('❌ Error handling tab activation:', error);
    }
});

// Also listen for tab updates (when URL changes in same tab)
chrome.tabs.onUpdated.addListener(async (tabId, changeInfo) => {
    // Only process when the tab is complete and URL has changed
    setTimeout(async()=>{

        const tab = await chrome.tabs.get(chan.tabId);

        if (changeInfo.status === 'complete' && tab.active && tab.url) {
            // Skip internal pages
            if (!tab.url.startsWith('chrome://') && !tab.url.startsWith('chrome-extension://')) {
                console.log(`🔄 Active tab updated: ${tab.url}`);
                await sendUrlToServer(tab.url, tab.title || 'No title');
            }
        }
    },5000)
});

console.log('✅ Simple URL logging is active!');
