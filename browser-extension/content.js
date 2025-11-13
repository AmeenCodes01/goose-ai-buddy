// /**
//  * Productivity Buddy - Content Script
//  * Smart content analysis and distraction blocking
//  */

// console.log('🤖 Productivity Buddy content script loaded');

// // Current session state
// let sessionState = 'idle';
// let focusOverlay = null;

// // Content analysis state
// let pageLoadTime = Date.now();
// let analysisTimer = null;
// let isAnalyzed = false;
// let currentTabId = null;

// // Get current tab ID
// chrome.runtime.sendMessage({ action: 'getCurrentTabId' }, (response) => {
//     currentTabId = response?.tabId;
// });

// // Listen for messages from background script
// chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
//     console.log('📨 Content script received message:', request);
    
//     switch (request.action) {
//         case 'enterFocusMode':
//             enterFocusMode(request.session);
//             break;
            
//         case 'enterBreakMode':
//             enterBreakMode(request.session);
//             break;
            
//         case 'exitSessionMode':
//             exitSessionMode();
//             break;
            
//         case 'closeTab':
//             showClosingMessage(request.reason);
//             break;
//     }
    
//     sendResponse({ success: true });
// });

// /**
//  * Content Analysis Functions
//  */
// function startContentAnalysis() {
//     // Clear existing timer
//     if (analysisTimer) {
//         clearTimeout(analysisTimer);
//     }
    
//     // Reset state
//     isAnalyzed = false;
//     pageLoadTime = Date.now();
    
//     // Only analyze if in focus mode
//     if (sessionState === 'focus') {
//         console.log('⏱️ Starting 15-second content analysis timer...');
        
//         analysisTimer = setTimeout(() => {
//             analyzeCurrentPage();
//         }, 15000); // 15 seconds
//     }
// }

// function analyzeCurrentPage() {
//     if (isAnalyzed || sessionState !== 'focus') {
//         return;
//     }
    
//     console.log('🔍 Analyzing page content...');
//     isAnalyzed = true;
    
//     try {
//         // Extract page content
//         const contentData = extractPageContent();
        
//         // Send to Python service for analysis
//         sendContentForAnalysis(contentData);
        
//     } catch (error) {
//         console.error('❌ Error analyzing content:', error);
//     }
// }

// function extractPageContent() {
//     // Get meta description
//     const getMetaContent = (name) => {
//         const meta = document.querySelector(`meta[name="${name}"], meta[property="${name}"]`);
//         return meta ? meta.getAttribute('content') || '' : '';
//     };
    
//     // Get main content (try different selectors)
//     const getMainContent = () => {
//         const selectors = ['main', 'article', '.content', '#content', '.post', '.entry'];
        
//         for (const selector of selectors) {
//             const element = document.querySelector(selector);
//             if (element) {
//                 return element.innerText.substring(0, 300);
//             }
//         }
        
//         // Fallback: get first paragraph or body text
//         const paragraphs = document.querySelectorAll('p');
//         if (paragraphs.length > 0) {
//             return Array.from(paragraphs).slice(0, 3).map(p => p.innerText).join(' ').substring(0, 300);
//         }
        
//         return document.body.innerText.substring(0, 300);
//     };
    
//     // Get headings
//     const getHeadings = () => {
//         return Array.from(document.querySelectorAll('h1, h2, h3'))
//                     .map(h => h.innerText.trim())
//                     .filter(text => text.length > 0)
//                     .slice(0, 5);
//     };
    
//     // YouTube-specific data extraction
//     const getYouTubeData = () => {
//         if (!window.location.hostname.includes('youtube.com')) {
//             return null;
//         }
        
//         return {
//             videoTitle: document.querySelector('h1.title, #title h1, .title-text')?.innerText?.trim() || '',
//             channelName: document.querySelector('#channel-name, .channel-name, #owner-name a')?.innerText?.trim() || '',
//             description: document.querySelector('#description, .description')?.innerText?.substring(0, 500) || '',
//             category: document.querySelector('.category, #category')?.innerText?.trim() || '',
//             viewCount: document.querySelector('.view-count, #count')?.innerText?.trim() || ''
//         };
//     };
    
//     // Compile all content data
//     const contentData = {
//         url: window.location.href,
//         title: document.title || '',
//         description: getMetaContent('description') || getMetaContent('og:description'),
//         keywords: getMetaContent('keywords'),
//         headings: getHeadings(),
//         pageText: getMainContent(),
//         domain: window.location.hostname,
//         timeSpent: Math.round((Date.now() - pageLoadTime) / 1000),
//         youtubeData: getYouTubeData()
//     };
    
//     console.log('📄 Extracted content data:', {
//         title: contentData.title.substring(0, 50) + '...',
//         domain: contentData.domain,
//         headings: contentData.headings.length,
//         hasYouTubeData: !!contentData.youtubeData
//     });
    
//     return contentData;
// }

// async function sendContentForAnalysis(contentData) {
//     try {
//         const response = await fetch('http://localhost:5000/analyze/content', {
//             method: 'POST',
//             headers: {
//                 'Content-Type': 'application/json',
//             },
//             body: JSON.stringify(contentData)
//         });
        
//         if (!response.ok) {
//             throw new Error(`HTTP error! status: ${response.status}`);
//         }
        
//         const result = await response.json();
//         console.log('🤖 Analysis result:', result);
        
//         // Handle the analysis result
//         handleAnalysisResult(result, contentData);
        
//     } catch (error) {
//         console.error('❌ Error sending content for analysis:', error);
        
//         // Fallback to basic blocking for known distracting sites
//         const distractingSites = ['9gag.com', 'buzzfeed.com', 'tmz.com'];
//         if (distractingSites.some(site => window.location.hostname.includes(site))) {
//             showBlockedSiteOverlay('Potentially distracting site during focus time');
//         }
//     }
// }

// function handleAnalysisResult(result, contentData) {
//     console.log(`📊 Content decision: ${result.decision} (confidence: ${result.confidence})`);
//     console.log(`📝 Reason: ${result.reason}`);
    
//     if (result.action === 'close_tab') {
//         // Show warning before closing
//         showDistractionWarning(result, contentData);
//     } else {
//         // Content is allowed
//         showContentAllowedIndicator(result.reason);
//     }
// }

// function showDistractionWarning(result, contentData) {
//     // Create warning overlay
//     const warningOverlay = document.createElement('div');
//     warningOverlay.id = 'productivity-buddy-warning';
//     warningOverlay.innerHTML = `
//         <div style="
//             position: fixed;
//             top: 0;
//             left: 0;
//             width: 100%;
//             height: 100%;
//             background: rgba(244, 67, 54, 0.95);
//             z-index: 999999;
//             display: flex;
//             flex-direction: column;
//             justify-content: center;
//             align-items: center;
//             color: white;
//             font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
//         ">
//             <div style="text-align: center; max-width: 600px; padding: 40px;">
//                 <div style="font-size: 80px; margin-bottom: 30px;">⚠️</div>
//                 <h1 style="font-size: 36px; margin-bottom: 20px; font-weight: 300;">
//                     Distraction Detected!
//                 </h1>
//                 <p style="font-size: 18px; margin-bottom: 20px; opacity: 0.9;">
//                     AI Analysis: "${result.reason}"
//                 </p>
//                 <p style="font-size: 16px; margin-bottom: 30px; opacity: 0.8;">
//                     This tab will close in <span id="countdown">10</span> seconds to help you stay focused.
//                 </p>
//                 <div style="margin-bottom: 30px;">
//                     <button id="override-btn" style="
//                         background: rgba(255,255,255,0.2);
//                         border: 2px solid white;
//                         color: white;
//                         padding: 12px 24px;
//                         border-radius: 25px;
//                         cursor: pointer;
//                         font-size: 16px;
//                         margin-right: 15px;
//                         transition: all 0.3s;
//                     ">
//                         Override (This Time)
//                     </button>
//                     <button id="feedback-work-btn" style="
//                         background: rgba(76, 175, 80, 0.8);
//                         border: 2px solid white;
//                         color: white;
//                         padding: 12px 24px;
//                         border-radius: 25px;
//                         cursor: pointer;
//                         font-size: 16px;
//                         transition: all 0.3s;
//                     ">
//                         This IS Work
//                     </button>
//                 </div>
//                 <div style="font-size: 14px; opacity: 0.7;">
//                     Page: ${contentData.title.substring(0, 60)}...
//                 </div>
//             </div>
//         </div>
//     `;
    
//     document.body.appendChild(warningOverlay);
    
//     // Countdown timer
//     let countdown = 10;
//     const countdownElement = document.getElementById('countdown');
//     const countdownInterval = setInterval(() => {
//         countdown--;
//         if (countdownElement) {
//             countdownElement.textContent = countdown;
//         }
        
//         if (countdown <= 0) {
//             clearInterval(countdownInterval);
//             closeCurrentTab();
//         }
//     }, 1000);
    
//     // Override button
//     const overrideBtn = document.getElementById('override-btn');
//     if (overrideBtn) {
//         overrideBtn.addEventListener('click', () => {
//             clearInterval(countdownInterval);
//             warningOverlay.remove();
//             showContentAllowedIndicator('User override - allowed this time');
//         });
//     }
    
//     // Feedback: This IS work button
//     const feedbackBtn = document.getElementById('feedback-work-btn');
//     if (feedbackBtn) {
//         feedbackBtn.addEventListener('click', () => {
//             clearInterval(countdownInterval);
//             sendUserFeedback(contentData.domain, 'WORK');
//             warningOverlay.remove();
//             showContentAllowedIndicator('Thanks for the feedback! Added to work sites.');
//         });
//     }
    
//     // Prevent scrolling
//     document.body.style.overflow = 'hidden';
// }

// function closeCurrentTab() {
//     // Notify background script to close this tab
//     chrome.runtime.sendMessage({ 
//         action: 'closeCurrentTab',
//         reason: 'Distraction detected by AI analysis'
//     });
// }

// function sendUserFeedback(domain, decision) {
//     fetch('http://localhost:5000/analyze/user-feedback', {
//         method: 'POST',
//         headers: {
//             'Content-Type': 'application/json',
//         },
//         body: JSON.stringify({
//             domain: domain,
//             decision: decision
//         })
//     }).catch(error => {
//         console.error('❌ Error sending user feedback:', error);
//     });
// }

// function showContentAllowedIndicator(reason) {
//     const indicator = document.createElement('div');
//     indicator.id = 'productivity-buddy-allowed-indicator';
//     indicator.innerHTML = `
//         <div style="
//             position: fixed;
//             top: 20px;
//             right: 20px;
//             background: rgba(76, 175, 80, 0.9);
//             color: white;
//             padding: 10px 15px;
//             border-radius: 20px;
//             font-family: 'Segoe UI', sans-serif;
//             font-size: 12px;
//             z-index: 999998;
//             box-shadow: 0 4px 12px rgba(0,0,0,0.2);
//             max-width: 300px;
//         ">
//             ✅ Content Allowed: ${reason}
//         </div>
//     `;
    
//     document.body.appendChild(indicator);
    
//     // Auto-remove after 5 seconds
//     setTimeout(() => {
//         if (indicator.parentElement) {
//             indicator.remove();
//         }
//     }, 5000);
// }

// function showClosingMessage(reason) {
//     const message = document.createElement('div');
//     message.innerHTML = `
//         <div style="
//             position: fixed;
//             top: 50%;
//             left: 50%;
//             transform: translate(-50%, -50%);
//             background: rgba(244, 67, 54, 0.95);
//             color: white;
//             padding: 30px;
//             border-radius: 15px;
//             font-family: 'Segoe UI', sans-serif;
//             font-size: 18px;
//             z-index: 999999;
//             text-align: center;
//         ">
//             🚫 Tab closing: ${reason}
//         </div>
//     `;
    
//     document.body.appendChild(message);
// }

// /**
//  * Session Mode Functions
//  */
// function enterFocusMode(session) {
//     sessionState = 'focus';
//     console.log('🎯 Entering focus mode');
    
//     // Start content analysis for this page
//     startContentAnalysis();
    
//     // Show focus mode indicator
//     showFocusModeIndicator();
// }

// function enterBreakMode(session) {
//     sessionState = 'break';
//     console.log('☕ Entering break mode');
    
//     // Cancel any pending analysis
//     if (analysisTimer) {
//         clearTimeout(analysisTimer);
//     }
    
//     // Remove overlays and show break indicator
//     removeAllOverlays();
//     showBreakModeIndicator();
// }

// function exitSessionMode() {
//     sessionState = 'idle';
//     console.log('🏠 Exiting session mode');
    
//     // Cancel analysis and remove overlays
//     if (analysisTimer) {
//         clearTimeout(analysisTimer);
//     }
    
//     removeAllOverlays();
// }

// /**
//  * UI Functions
//  */
// function showFocusModeIndicator() {
//     removeIndicators();
    
//     const indicator = document.createElement('div');
//     indicator.id = 'productivity-buddy-focus-indicator';
//     indicator.innerHTML = `
//         <div style="
//             position: fixed;
//             top: 20px;
//             right: 20px;
//             background: rgba(76, 175, 80, 0.95);
//             color: white;
//             padding: 10px 15px;
//             border-radius: 20px;
//             font-family: 'Segoe UI', sans-serif;
//             font-size: 14px;
//             font-weight: bold;
//             z-index: 999998;
//             box-shadow: 0 4px 12px rgba(0,0,0,0.2);
//         ">
//             🎯 Focus Mode - Content Analysis Active
//         </div>
//     `;
    
//     document.body.appendChild(indicator);
    
//     setTimeout(() => {
//         if (indicator.parentElement) {
//             indicator.style.opacity = '0.7';
//         }
//     }, 5000);
// }

// function showBreakModeIndicator() {
//     removeIndicators();
    
//     const indicator = document.createElement('div');
//     indicator.id = 'productivity-buddy-break-indicator';
//     indicator.innerHTML = `
//         <div style="
//             position: fixed;
//             top: 20px;
//             right: 20px;
//             background: rgba(255, 152, 0, 0.95);
//             color: white;
//             padding: 10px 15px;
//             border-radius: 20px;
//             font-family: 'Segoe UI', sans-serif;
//             font-size: 14px;
//             font-weight: bold;
//             z-index: 999998;
//             box-shadow: 0 4px 12px rgba(0,0,0,0.2);
//         ">
//             ☕ Break Time - Browse Freely!
//         </div>
//     `;
    
//     document.body.appendChild(indicator);
// }

// function removeAllOverlays() {
//     const overlayIds = [
//         'productivity-buddy-warning',
//         'productivity-buddy-allowed-indicator',
//         'productivity-buddy-focus-indicator',
//         'productivity-buddy-break-indicator'
//     ];
    
//     overlayIds.forEach(id => {
//         const element = document.getElementById(id);
//         if (element) element.remove();
//     });
    
//     // Restore scrolling
//     document.body.style.overflow = '';
// }

// function removeIndicators() {
//     const indicators = ['productivity-buddy-focus-indicator', 'productivity-buddy-break-indicator'];
//     indicators.forEach(id => {
//         const element = document.getElementById(id);
//         if (element) element.remove();
//     });
// }

// /**
//  * Event Listeners
//  */
// // Listen for page navigation/changes
// let lastUrl = window.location.href;
// function checkForNavigation() {
//     if (window.location.href !== lastUrl) {
//         lastUrl = window.location.href;
//         console.log('🔄 Navigation detected, restarting analysis');
//         startContentAnalysis();
//     }
// }

// // Check for navigation changes every 2 seconds
// setInterval(checkForNavigation, 2000);

// // Listen for DOM changes (for SPAs)
// const observer = new MutationObserver(() => {
//     if (sessionState === 'focus' && !isAnalyzed) {
//         // Restart analysis if significant DOM changes occur
//         startContentAnalysis();
//     }
// });

// observer.observe(document.body, {
//     childList: true,
//     subtree: false // Only watch direct children to avoid too many triggers
// });

// /**
//  * Initialize content script
//  */
// function init() {
//     console.log('🚀 Initializing Productivity Buddy content script');
    
//     // Check current session state
//     chrome.runtime.sendMessage({ action: 'getSessionStatus' }, (response) => {
//         if (response && response.success && response.session) {
//             const session = response.session;
            
//             if (session.state === 'focus') {
//                 enterFocusMode(session);
//             } else if (session.state === 'break') {
//                 enterBreakMode(session);
//             }
//         }
//     });
// }

// // Initialize when DOM is ready
// if (document.readyState === 'loading') {
//     document.addEventListener('DOMContentLoaded', init);
// } else {
//     init();
// }
