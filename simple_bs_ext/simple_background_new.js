/**
 * Simple Productivity Buddy - Background Script (Simplified)
 *
 * Core Logic:
 * 1. A single timer tracks the user's focus on a specific tab and URL.
 * 2. When the user navigates to a new URL (by switching tabs or changing the URL in the active tab),
 *    the previous timer is cancelled.
 * 3. A new 1-minute timer starts for the new URL.
 * 4. If the timer completes (meaning the user stayed on the URL for 1 minute), the URL is sent to the
 *    backend for analysis.
 * 5. If the analysis flags the URL as a distraction, the tab is redirected to a safe page.
 */

const PYTHON_SERVICE_URL = 'http://localhost:5000/analyze-distraction';
const SAFE_URL = 'chrome://newtab/'; // URL to redirect to if a distraction is detected
const ANALYSIS_DELAY_MS = 10000; // 1 minute

let analysisTimer = null; // Holds the setTimeout ID for the current timer

console.log('🚀 Productivity Buddy (Simplified) loaded!');

/**
 * Clears any active analysis timer.
 * This is called whenever the user navigates away from a page.
 */
function clearAnalysisTimer() {
  if (analysisTimer) {
    clearTimeout(analysisTimer);
    analysisTimer = null;
    console.log('⏱️ Timer cleared.');
  }
}

/**
 * Starts a new 1-minute timer for the specified tab and URL.
 * @param {number} tabId - The ID of the tab.
 * @param {string} url - The URL of the tab to analyze.
 * @param {string} title - The title of the tab.
 */
function startAnalysisTimer(tabId, url, title) {
  // Always clear the previous timer before starting a new one.
  clearAnalysisTimer();

  // Don't start a timer for internal browser pages.
  if (!url || !url.startsWith('http')) {
    console.log(`Skipping timer for internal URL: ${url}`);
    return;
  }

  console.log(`⏱️ Starting 1-minute timer for: ${url}`);

  analysisTimer = setTimeout(() => {
    console.log(`✅ 1 minute elapsed. Analyzing: ${url}`);
    analyzeUrl(tabId, url, title);
  }, ANALYSIS_DELAY_MS);
}

/**
 * Sends the URL to the Python backend for analysis and handles the response.
 * @param {number} tabId - The ID of the tab to potentially redirect.
 * @param {string} url - The URL to analyze.
 * @param {string} title - The title of the page.
 */

async function analyzeUrl(tabId, url, title) {
  console.log(`🧠 Sending to backend for analysis: ${url}`);
  try {
    const response = await fetch(PYTHON_SERVICE_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        url,
        title,
        timestamp: new Date().toISOString(),
      }),
    });

    if (!response.ok) {
      console.error(`❌ Backend analysis failed with status: ${response.status}`);
      return;
    }

    const result = await response.json();
    console.log('💡 Backend analysis result:', result);

    // If the backend flags it as a distraction, redirect the tab.
    if (result.action === 'close_tab') {
      console.log(`🚫 Distraction detected! Redirecting tab ${tabId} to ${SAFE_URL}`);
      try {
        await chrome.tabs.update(tabId, { url: SAFE_URL });
      } catch (error) {
        console.error(`❌ Failed to redirect tab ${tabId}:`, error);
      }
    }
  } catch (error) {
    console.error('❌ Error during backend communication:', error);
  }
}

/**
 * Listener for when the active tab changes.
 */
chrome.tabs.onActivated.addListener((activeInfo) => {
  chrome.tabs.get(activeInfo.tabId, (tab) => {
    if (chrome.runtime.lastError) {
      console.error(chrome.runtime.lastError.message);
      return;
    }
    if (tab.url.includes("shorts")) {
      setTimeout(() => chrome.tabs.remove(activeInfo.tabId), 1500); // Close after 1.5s
      return;
    }

    console.log(`Tab switched to: ${tab.url}`);
    startAnalysisTimer(tab.id, tab.url, tab.title);
  });
});

/**
 * Listener for when the URL of any tab changes.
 */
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  // We only care about updates to the active tab when the URL is completely loaded.
  if (tab.active && changeInfo.status === 'complete' && tab.url) {
    if (tab.url.includes("shorts")) {
      setTimeout(() => chrome.tabs.remove(tabId), 1500); // Close after 1.5s
      return;
    }

    console.log(`Tab URL updated to: ${tab.url}`);
    startAnalysisTimer(tab.id, tab.url, tab.title);
  }
});

/**
 * Listener for when a tab is closed.
 * If the closed tab is the one we are timing, cancel the timer.
 * Note: This is a good practice, though our current logic of clearing the timer
 * on tab activation/update already handles most cases.
 */
chrome.tabs.onRemoved.addListener((tabId, removeInfo) => {
    // We can't easily check if the closed tab was the one being timed without
    // storing its ID. However, the timer will be naturally cleared when the user
    // activates a new tab, so we can keep this simple and omit a specific check here.
    console.log(`Tab ${tabId} was closed.`);
    // As a fallback, if no new tab becomes active, let's ensure the timer is cleared.
    // A more robust implementation might store the timed tab's ID.
    clearAnalysisTimer();
});