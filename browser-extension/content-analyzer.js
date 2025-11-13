/**
 * Content Analyzer Extension for Background Script
 * Add this to the existing message handlers
 */

// Add these cases to the existing chrome.runtime.onMessage.addListener switch statement:

/*
    case 'getCurrentTabId':
      chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        sendResponse({ tabId: tabs[0]?.id });
      });
      return true;
      
    case 'closeCurrentTab':
      chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        if (tabs[0]) {
          chrome.tabs.remove(tabs[0].id);
          console.log(`🚫 Closed distracting tab: ${tabs[0].url}`);
        }
      });
      sendResponse({ success: true });
      break;
*/

// For now, we'll add these handlers separately
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'getCurrentTabId') {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      sendResponse({ tabId: tabs[0]?.id });
    });
    return true;
  }
  
  if (request.action === 'closeCurrentTab') {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (tabs[0]) {
        chrome.tabs.remove(tabs[0].id);
        console.log(`🚫 Closed distracting tab: ${tabs[0].url}`);
      }
    });
    sendResponse({ success: true });
    return false;
  }
});

console.log('📊 Content analyzer handlers loaded');
