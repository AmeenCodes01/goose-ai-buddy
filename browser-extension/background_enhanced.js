/**
 * Productivity Buddy - Enhanced Background Script
 * Handles communication with Python service and manages browser automation
 * WITH PERSISTENT SESSION STATE MANAGEMENT
 */

const PYTHON_SERVICE_URL = 'http://localhost:5000';
const BLOCKED_SITES_KEY = 'blockedSites';
const SESSION_STATE_KEY = 'sessionState';

// Current session state
let currentSession = {
  state: 'idle', // idle, focus, break
  startTime: null,
  duration: 0
};

// Blocked sites list
let blockedSites = new Set();

// Session broadcasting interval for persistence
let sessionBroadcastInterval = null;

// Initialize extension
chrome.runtime.onInstalled.addListener(() => {
  console.log('🤖 Productivity Buddy installed!');
  loadBlockedSites();
  startHealthMonitoring();
});

// Enhanced tab lifecycle management for persistent session state
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'loading' && tab.url) {
    checkAndBlockSite(tabId, tab.url);
  }
  
  // Inject session state when tab finishes loading
  if (changeInfo.status === 'complete' && tab.url && !tab.url.startsWith('chrome://')) {
    console.log(`📋 Tab ${tabId} loaded, injecting session state`);
    injectSessionStateToTab(tabId);
  }
});

chrome.tabs.onCreated.addListener((tab) => {
  console.log(`📝 New tab created: ${tab.id}`);
});

chrome.tabs.onActivated.addListener((activeInfo) => {
  console.log(`🎯 Tab ${activeInfo.tabId} activated`);
  setTimeout(() => {
    injectSessionStateToTab(activeInfo.tabId);
  }, 100);
});

chrome.tabs.onRemoved.addListener((tabId, removeInfo) => {
  console.log(`🗑️ Tab ${tabId} removed`);
  if (currentSession.state !== 'idle') {
    setTimeout(broadcastSessionStateToAllTabs, 500);
  }
});

// Listen for messages from popup and content scripts
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('📨 Received message:', request);
  
  switch (request.action) {
    case 'getSessionStatus':
      getSessionStatus().then(sendResponse);
      return true;
      
    case 'startFocusSession':
      startFocusSession(request.duration).then(sendResponse);
      return true;
      
    case 'startBreakSession':
      startBreakSession(request.duration).then(sendResponse);
      return true;
      
    case 'endSession':
      endSession().then(sendResponse);
      return true;
      
    case 'getBlockedSites':
      sendResponse({ sites: Array.from(blockedSites) });
      break;
      
    case 'addBlockedSite':
      addBlockedSite(request.site);
      sendResponse({ success: true });
      break;
      
    case 'removeBlockedSite':
      removeBlockedSite(request.site);
      sendResponse({ success: true });
      break;
      
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
  }
});

/**
 * Communication with Python Service
 */
async function callPythonService(endpoint, method = 'GET', data = null) {
  try {
    const options = {
      method: method,
      headers: {
        'Content-Type': 'application/json',
      }
    };
    
    if (data) {
      options.body = JSON.stringify(data);
    }
    
    const response = await fetch(`${PYTHON_SERVICE_URL}${endpoint}`, options);
    return await response.json();
  } catch (error) {
    console.error(`❌ Python service error (${endpoint}):`, error);
    throw error;
  }
}

/**
 * Session Management with Persistent State
 */
async function startFocusSession(duration = 25) {
  try {
    const response = await callPythonService('/session/start', 'POST', { duration });
    
    currentSession = {
      state: 'focus',
      startTime: Date.now(),
      duration: duration
    };
    
    // Update all tabs to show focus mode
    await updateAllTabsForFocusMode();
    startSessionBroadcasting();
    
    // Set alarm for session end
    chrome.alarms.create('sessionEnd', { delayInMinutes: duration });
    
    // Show notification
    chrome.notifications.create({
      type: 'basic',
      iconUrl: 'icons/icon48.png',
      title: 'Focus Session Started',
      message: `${duration} minute focus session has begun!`
    });
    
    console.log(`🎯 Focus session started for ${duration} minutes`);
    return { success: true, session: currentSession };
    
  } catch (error) {
    console.error('❌ Failed to start focus session:', error);
    return { success: false, error: error.message };
  }
}

async function startBreakSession(duration = 5) {
  try {
    const response = await callPythonService('/session/break', 'POST', { duration });
    
    currentSession = {
      state: 'break',
      startTime: Date.now(),
      duration: duration
    };
    
    // Update all tabs to show break mode
    await updateAllTabsForBreakMode();
    startSessionBroadcasting();
    
    // Set alarm for break end
    chrome.alarms.create('sessionEnd', { delayInMinutes: duration });
    
    // Show notification
    chrome.notifications.create({
      type: 'basic',
      iconUrl: 'icons/icon48.png',
      title: 'Break Time!',
      message: `Enjoy your ${duration} minute break!`
    });
    
    console.log(`☕ Break session started for ${duration} minutes`);
    return { success: true, session: currentSession };
    
  } catch (error) {
    console.error('❌ Failed to start break session:', error);
    return { success: false, error: error.message };
  }
}

async function endSession() {
  try {
    currentSession = {
      state: 'idle',
      startTime: null,
      duration: 0
    };
    
    // Clear alarms
    chrome.alarms.clear('sessionEnd');
    
    // Update all tabs to normal mode
    await updateAllTabsForNormalMode();
    stopSessionBroadcasting();
    
    console.log('🏠 Session ended, returning to normal mode');
    return { success: true, session: currentSession };
    
  } catch (error) {
    console.error('❌ Failed to end session:', error);
    return { success: false, error: error.message };
  }
}

async function getSessionStatus() {
  try {
    // Try to get status from Python service
    const response = await callPythonService('/session/status');
    return { success: true, session: response };
  } catch (error) {
    // Fallback to local state
    return { success: true, session: currentSession };
  }
}

/**
 * Persistent Session State Management
 */
async function injectSessionStateToTab(tabId) {
  if (currentSession.state === 'idle') return;
  
  try {
    const message = currentSession.state === 'focus' 
      ? { action: 'enterFocusMode', session: currentSession }
      : { action: 'enterBreakMode', session: currentSession };
    
    await chrome.tabs.sendMessage(tabId, message);
    console.log(`✅ Injected ${currentSession.state} state to tab ${tabId}`);
  } catch (error) {
    console.log(`⚠️ Could not inject state to tab ${tabId}:`, error.message);
  }
}

async function broadcastSessionStateToAllTabs() {
  if (currentSession.state === 'idle') return;
  
  console.log(`📡 Broadcasting ${currentSession.state} state to all tabs`);
  const tabs = await chrome.tabs.query({});
  
  for (const tab of tabs) {
    if (tab.url && !tab.url.startsWith('chrome://')) {
      injectSessionStateToTab(tab.id);
    }
  }
}

function startSessionBroadcasting() {
  if (sessionBroadcastInterval) {
    clearInterval(sessionBroadcastInterval);
  }
  
  sessionBroadcastInterval = setInterval(async () => {
    if (currentSession.state !== 'idle') {
      console.log('🔄 Periodic session state broadcast');
      await broadcastSessionStateToAllTabs();
    }
  }, 10000); // Every 10 seconds
  
  console.log('📡 Started continuous session broadcasting');
}

function stopSessionBroadcasting() {
  if (sessionBroadcastInterval) {
    clearInterval(sessionBroadcastInterval);
    sessionBroadcastInterval = null;
    console.log('📡 Stopped session broadcasting');
  }
}

/**
 * Tab Management
 */
async function updateAllTabsForFocusMode() {
  const tabs = await chrome.tabs.query({});
  
  for (const tab of tabs) {
    if (tab.url && !tab.url.startsWith('chrome://')) {
      chrome.tabs.sendMessage(tab.id, {
        action: 'enterFocusMode',
        session: currentSession
      }).catch(() => {});
    }
  }
}

async function updateAllTabsForBreakMode() {
  const tabs = await chrome.tabs.query({});
  
  for (const tab of tabs) {
    if (tab.url && !tab.url.startsWith('chrome://')) {
      chrome.tabs.sendMessage(tab.id, {
        action: 'enterBreakMode',
        session: currentSession
      }).catch(() => {});
    }
  }
}

async function updateAllTabsForNormalMode() {
  const tabs = await chrome.tabs.query({});
  
  for (const tab of tabs) {
    if (tab.url && !tab.url.startsWith('chrome://')) {
      chrome.tabs.sendMessage(tab.id, {
        action: 'exitSessionMode'
      }).catch(() => {});
    }
  }
}

/**
 * Site Blocking
 */
function checkAndBlockSite(tabId, url) {
  if (currentSession.state !== 'focus') {
    return; // Only block during focus sessions
  }
  
  const domain = extractDomain(url);
  
  if (blockedSites.has(domain)) {
    console.log(`🚫 Blocking site: ${domain}`);
    
    // Redirect to focus page
    chrome.tabs.update(tabId, {
      url: chrome.runtime.getURL('focus-overlay.html')
    });
    
    // Increment blocked count
    callPythonService('/system/block-sites', 'POST', { sites: [domain] });
    
    // Show notification
    chrome.notifications.create({
      type: 'basic',
      iconUrl: 'icons/icon48.png',
      title: 'Site Blocked',
      message: `${domain} is blocked during focus time. Stay focused! 🎯`
    });
  }
}

function addBlockedSite(site) {
  const domain = extractDomain(site);
  blockedSites.add(domain);
  saveBlockedSites();
  console.log(`➕ Added blocked site: ${domain}`);
}

function removeBlockedSite(site) {
  const domain = extractDomain(site);
  blockedSites.delete(domain);
  saveBlockedSites();
  console.log(`➖ Removed blocked site: ${domain}`);
}

function extractDomain(url) {
  try {
    const urlObj = new URL(url);
    return urlObj.hostname.replace('www.', '');
  } catch (error) {
    return url;
  }
}

/**
 * Alarm Handler
 */
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === 'sessionEnd') {
    if (currentSession.state === 'focus') {
      // Focus session ended, start break
      startBreakSession(5);
    } else if (currentSession.state === 'break') {
      // Break ended, return to idle
      endSession();
    }
  }
});

/**
 * Storage Management
 */
function saveBlockedSites() {
  chrome.storage.local.set({
    [BLOCKED_SITES_KEY]: Array.from(blockedSites)
  });
}

function loadBlockedSites() {
  chrome.storage.local.get([BLOCKED_SITES_KEY], (result) => {
    if (result[BLOCKED_SITES_KEY]) {
      blockedSites = new Set(result[BLOCKED_SITES_KEY]);
      console.log(`📚 Loaded ${blockedSites.size} blocked sites`);
    } else {
      // Default blocked sites
      blockedSites = new Set([
        'youtube.com',
        'facebook.com',
        'twitter.com',
        'instagram.com',
        'reddit.com',
        'tiktok.com',
        'netflix.com'
      ]);
      saveBlockedSites();
    }
  });
}

/**
 * Health Monitoring
 */
function startHealthMonitoring() {
  // Check Python service health every 30 seconds
  setInterval(async () => {
    try {
      await callPythonService('/health');
      console.log('💚 Python service is healthy');
    } catch (error) {
      console.log('💔 Python service is not responding');
    }
  }, 30000);
}

/**
 * Communication with Python Service
 */
async function callPythonService(endpoint, method = 'GET', data = null) {
  try {
    const options = {
      method: method,
      headers: {
        'Content-Type': 'application/json',
      }
    };
    
    if (data) {
      options.body = JSON.stringify(data);
    }
    
    const response = await fetch(`${PYTHON_SERVICE_URL}${endpoint}`, options);
    return await response.json();
  } catch (error) {
    console.error(`❌ Python service error (${endpoint}):`, error);
    throw error;
  }
}

/**
 * Session Management with Persistent State
 */
async function startFocusSession(duration = 25) {
  try {
    const response = await callPythonService('/session/start', 'POST', { duration });
    
    currentSession = {
      state: 'focus',
      startTime: Date.now(),
      duration: duration
    };
    
    // Update all tabs to show focus mode
    await updateAllTabsForFocusMode();
    startSessionBroadcasting();
    
    // Set alarm for session end
    chrome.alarms.create('sessionEnd', { delayInMinutes: duration });
    
    // Show notification
    chrome.notifications.create({
      type: 'basic',
      iconUrl: 'icons/icon48.png',
      title: 'Focus Session Started',
      message: `${duration} minute focus session has begun!`
    });
    
    console.log(`🎯 Focus session started for ${duration} minutes`);
    return { success: true, session: currentSession };
    
  } catch (error) {
    console.error('❌ Failed to start focus session:', error);
    return { success: false, error: error.message };
  }
}

async function startBreakSession(duration = 5) {
  try {
    const response = await callPythonService('/session/break', 'POST', { duration });
    
    currentSession = {
      state: 'break',
      startTime: Date.now(),
      duration: duration
    };
    
    // Update all tabs to show break mode
    await updateAllTabsForBreakMode();
    startSessionBroadcasting();
    
    // Set alarm for break end
    chrome.alarms.create('sessionEnd', { delayInMinutes: duration });
    
    // Show notification
    chrome.notifications.create({
      type: 'basic',
      iconUrl: 'icons/icon48.png',
      title: 'Break Time!',
      message: `Enjoy your ${duration} minute break!`
    });
    
    console.log(`☕ Break session started for ${duration} minutes`);
    return { success: true, session: currentSession };
    
  } catch (error) {
    console.error('❌ Failed to start break session:', error);
    return { success: false, error: error.message };
  }
}

async function endSession() {
  try {
    currentSession = {
      state: 'idle',
      startTime: null,
      duration: 0
    };
    
    // Clear alarms
    chrome.alarms.clear('sessionEnd');
    
    // Update all tabs to normal mode
    await updateAllTabsForNormalMode();
    stopSessionBroadcasting();
    
    console.log('🏠 Session ended, returning to normal mode');
    return { success: true, session: currentSession };
    
  } catch (error) {
    console.error('❌ Failed to end session:', error);
    return { success: false, error: error.message };
  }
}

async function getSessionStatus() {
  try {
    // Try to get status from Python service
    const response = await callPythonService('/session/status');
    return { success: true, session: response };
  } catch (error) {
    // Fallback to local state
    return { success: true, session: currentSession };
  }
}

/**
 * Persistent Session State Management
 */
async function injectSessionStateToTab(tabId) {
  if (currentSession.state === 'idle') return;
  
  try {
    const message = currentSession.state === 'focus' 
      ? { action: 'enterFocusMode', session: currentSession }
      : { action: 'enterBreakMode', session: currentSession };
    
    await chrome.tabs.sendMessage(tabId, message);
    console.log(`✅ Injected ${currentSession.state} state to tab ${tabId}`);
  } catch (error) {
    console.log(`⚠️ Could not inject state to tab ${tabId}:`, error.message);
  }
}

async function broadcastSessionStateToAllTabs() {
  if (currentSession.state === 'idle') return;
  
  console.log(`📡 Broadcasting ${currentSession.state} state to all tabs`);
  const tabs = await chrome.tabs.query({});
  
  for (const tab of tabs) {
    if (tab.url && !tab.url.startsWith('chrome://')) {
      injectSessionStateToTab(tab.id);
    }
  }
}

function startSessionBroadcasting() {
  if (sessionBroadcastInterval) {
    clearInterval(sessionBroadcastInterval);
  }
  
  sessionBroadcastInterval = setInterval(async () => {
    if (currentSession.state !== 'idle') {
      console.log('🔄 Periodic session state broadcast');
      await broadcastSessionStateToAllTabs();
    }
  }, 10000); // Every 10 seconds
  
  console.log('📡 Started continuous session broadcasting');
}

function stopSessionBroadcasting() {
  if (sessionBroadcastInterval) {
    clearInterval(sessionBroadcastInterval);
    sessionBroadcastInterval = null;
    console.log('📡 Stopped session broadcasting');
  }
}

/**
 * Tab Management
 */
async function updateAllTabsForFocusMode() {
  const tabs = await chrome.tabs.query({});
  
  for (const tab of tabs) {
    if (tab.url && !tab.url.startsWith('chrome://')) {
      chrome.tabs.sendMessage(tab.id, {
        action: 'enterFocusMode',
        session: currentSession
      }).catch(() => {});
    }
  }
}

async function updateAllTabsForBreakMode() {
  const tabs = await chrome.tabs.query({});
  
  for (const tab of tabs) {
    if (tab.url && !tab.url.startsWith('chrome://')) {
      chrome.tabs.sendMessage(tab.id, {
        action: 'enterBreakMode',
        session: currentSession
      }).catch(() => {});
    }
  }
}

async function updateAllTabsForNormalMode() {
  const tabs = await chrome.tabs.query({});
  
  for (const tab of tabs) {
    if (tab.url && !tab.url.startsWith('chrome://')) {
      chrome.tabs.sendMessage(tab.id, {
        action: 'exitSessionMode'
      }).catch(() => {});
    }
  }
}

/**
 * Site Blocking (Legacy - now handled by AI analysis)
 */
function checkAndBlockSite(tabId, url) {
  // Legacy function - AI analysis handles blocking now
  return;
}

function addBlockedSite(site) {
  const domain = extractDomain(site);
  blockedSites.add(domain);
  saveBlockedSites();
  console.log(`➕ Added blocked site: ${domain}`);
}

function removeBlockedSite(site) {
  const domain = extractDomain(site);
  blockedSites.delete(domain);
  saveBlockedSites();
  console.log(`➖ Removed blocked site: ${domain}`);
}

function extractDomain(url) {
  try {
    const urlObj = new URL(url);
    return urlObj.hostname.replace('www.', '');
  } catch (error) {
    return url;
  }
}

/**
 * Alarm Handler
 */
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === 'sessionEnd') {
    if (currentSession.state === 'focus') {
      // Focus session ended, start break
      startBreakSession(5);
    } else if (currentSession.state === 'break') {
      // Break ended, return to idle
      endSession();
    }
  }
});

console.log('🚀 Productivity Buddy Enhanced background script loaded!');
