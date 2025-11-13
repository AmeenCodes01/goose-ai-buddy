/**
 * Simple Content Script - Does Nothing For Now
 * Placeholder for future functionality
 */

console.log('📄 Simple content script loaded on:', window.location.href);

// Listen for messages from background script (if needed later)
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    console.log('📨 Content script received message:', request);
    
    // For now, just acknowledge
    sendResponse({ status: 'received' });
});

// Future: Could extract page content, inject UI, etc.
// But for URL logging, background script handles everything!
