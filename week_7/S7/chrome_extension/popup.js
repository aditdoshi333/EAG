document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('searchInput');
    const resultsDiv = document.getElementById('results');
    const indexedPagesList = document.getElementById('indexedPagesList');
    const refreshButton = document.getElementById('refreshButton');
    let searchTimeout;
    let isSearching = false;

    // Focus search input when popup opens
    searchInput.focus();

    // Load indexed pages when popup opens
    loadIndexedPages();

    // Add refresh button handler
    refreshButton.addEventListener('click', loadIndexedPages);

    searchInput.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        const query = e.target.value.trim();
        
        if (query) {
            // Show loading state
            resultsDiv.innerHTML = '<div class="loading">Searching...</div>';
            
            searchTimeout = setTimeout(() => {
                searchPages(query);
            }, 300);
        } else {
            resultsDiv.innerHTML = '';
        }
    });

    async function loadIndexedPages() {
        try {
            const response = await fetch('http://localhost:5001/pages');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            displayIndexedPages(data.pages);
        } catch (error) {
            console.error('Failed to load indexed pages:', error);
            indexedPagesList.innerHTML = `
                <div class="error-message">
                    <div>⚠️ Error loading indexed pages</div>
                    <div style="font-size: 12px; margin-top: 8px;">
                        Make sure the backend server is running at http://localhost:5001
                    </div>
                </div>`;
        }
    }

    function displayIndexedPages(pages) {
        if (pages.length === 0) {
            indexedPagesList.innerHTML = `
                <div class="no-results">
                    <div>No pages indexed yet</div>
                    <div style="font-size: 12px; margin-top: 8px;">
                        Visit some pages to start indexing
                    </div>
                </div>`;
            return;
        }

        indexedPagesList.innerHTML = pages.map(page => `
            <div class="indexed-page-item">
                <div class="indexed-page-url">${page.url}</div>
                <div class="indexed-page-timestamp">
                    Indexed: ${new Date(page.timestamp).toLocaleString()}
                </div>
            </div>
        `).join('');
    }

    async function searchPages(query) {
        if (isSearching) return;
        isSearching = true;

        try {
            const response = await fetch('http://localhost:5001/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            displayResults(data.results, query);
        } catch (error) {
            console.error('Search failed:', error);
            resultsDiv.innerHTML = `
                <div class="error-message">
                    <div>⚠️ Error performing search</div>
                    <div style="font-size: 12px; margin-top: 8px;">
                        Make sure the backend server is running at http://localhost:5001
                    </div>
                </div>`;
        } finally {
            isSearching = false;
        }
    }

    function displayResults(results, query) {
        if (results.length === 0) {
            resultsDiv.innerHTML = `
                <div class="no-results">
                    <div>No results found</div>
                    <div style="font-size: 12px; margin-top: 8px;">
                        Try a different search term
                    </div>
                </div>`;
            return;
        }

        resultsDiv.innerHTML = results.map(result => `
            <div class="result-item" data-url="${result.url}">
                <div class="result-url">${result.url}</div>
                <div class="result-content">${result.content.substring(0, 200)}...</div>
            </div>
        `).join('');

        // Add click handlers to result items
        document.querySelectorAll('.result-item').forEach(item => {
            item.addEventListener('click', async () => {
                const url = item.dataset.url;
                console.log('[WebPageIndexer] Result item clicked:', url);
                try {
                    // Show loading state
                    item.style.opacity = '0.7';
                    item.style.pointerEvents = 'none';
                    
                    // First, try to find an existing tab
                    const tabs = await chrome.tabs.query({ url: url });
                    console.log('[WebPageIndexer] Found existing tabs:', tabs);
                    
                    let targetTab;
                    if (tabs.length > 0) {
                        // Use existing tab
                        targetTab = tabs[0];
                        console.log('[WebPageIndexer] Using existing tab:', targetTab.id);
                        await chrome.tabs.update(targetTab.id, { active: true });
                        await chrome.windows.update(targetTab.windowId, { focused: true });
                    } else {
                        // Create new tab
                        console.log('[WebPageIndexer] Creating new tab for URL:', url);
                        targetTab = await chrome.tabs.create({ url: url });
                        console.log('[WebPageIndexer] Created new tab:', targetTab.id);
                    }
                    
                    // Wait for the tab to be ready
                    await new Promise(resolve => setTimeout(resolve, 1000));
                    
                    // Ensure content script is injected
                    try {
                        console.log('[WebPageIndexer] Injecting content script into tab:', targetTab.id);
                        await chrome.scripting.executeScript({
                            target: { tabId: targetTab.id },
                            files: ['content.js']
                        });
                        console.log('[WebPageIndexer] Content script injected successfully');
                    } catch (error) {
                        console.log('[WebPageIndexer] Content script already injected or injection failed:', error);
                    }
                    
                    // Wait for content script to initialize
                    await new Promise(resolve => setTimeout(resolve, 1000));
                    
                    // Send highlight message
                    console.log('[WebPageIndexer] Sending highlight message to tab:', targetTab.id);
                    const success = await sendMessageToTab(targetTab.id, {
                        action: 'highlight',
                        text: query
                    });
                    
                    console.log('[WebPageIndexer] Highlight message sent, success:', success);
                    
                    if (!success) {
                        throw new Error('Failed to highlight text');
                    }
                } catch (error) {
                    console.error('[WebPageIndexer] Error handling result click:', error);
                    // Show error message
                    const errorDiv = document.createElement('div');
                    errorDiv.className = 'error-message';
                    errorDiv.textContent = 'An error occurred while highlighting text. Please try again.';
                    item.appendChild(errorDiv);
                } finally {
                    // Reset item state
                    item.style.opacity = '1';
                    item.style.pointerEvents = 'auto';
                }
            });
        });
    }

    // Helper function to send message to tab with retry
    async function sendMessageToTab(tabId, message, maxRetries = 3) {
        console.log(`[WebPageIndexer] Attempting to send message to tab ${tabId}:`, message);
        for (let i = 0; i < maxRetries; i++) {
            try {
                console.log(`[WebPageIndexer] Attempt ${i + 1}/${maxRetries} to send message`);
                const response = await chrome.tabs.sendMessage(tabId, message);
                console.log('[WebPageIndexer] Message sent successfully, response:', response);
                return response?.success || false;
            } catch (error) {
                console.error(`[WebPageIndexer] Attempt ${i + 1} failed:`, error);
                if (i === maxRetries - 1) {
                    throw error;
                }
                // Wait before retrying
                await new Promise(resolve => setTimeout(resolve, 1000));
            }
        }
        return false;
    }

    // Helper function to check if URL is injectable
    function isInjectableUrl(url) {
        try {
            const urlObj = new URL(url);
            // List of restricted URL schemes
            const restrictedSchemes = ['chrome:', 'chrome-extension:', 'chrome-devtools:', 'edge:', 'about:'];
            return !restrictedSchemes.some(scheme => urlObj.protocol.startsWith(scheme));
        } catch (error) {
            console.error('[WebPageIndexer] Error parsing URL:', error);
            return false;
        }
    }

    // Helper function to handle tab activation and message sending
    async function handleTabActivation(url, query) {
        try {
            console.log('[WebPageIndexer] Starting tab activation for URL:', url);
            
            // Check if URL is injectable
            if (!isInjectableUrl(url)) {
                console.log('[WebPageIndexer] URL is not injectable:', url);
                return false;
            }
            
            // Find the tab with this URL
            const tabs = await chrome.tabs.query({ url: url });
            console.log('[WebPageIndexer] Found tabs:', tabs);
            
            if (tabs.length > 0) {
                console.log('[WebPageIndexer] Found existing tab:', tabs[0].id);
                // If tab exists, activate it and send highlight message
                await chrome.tabs.update(tabs[0].id, { active: true });
                await chrome.windows.update(tabs[0].windowId, { focused: true });
                
                // Wait for the tab to become active
                await new Promise(resolve => setTimeout(resolve, 500));
                
                // Inject content script if not already injected
                try {
                    console.log('[WebPageIndexer] Attempting to inject content script');
                    await chrome.scripting.executeScript({
                        target: { tabId: tabs[0].id },
                        files: ['content.js']
                    });
                    console.log('[WebPageIndexer] Content script injected successfully');
                } catch (error) {
                    console.log('[WebPageIndexer] Content script already injected or injection failed:', error);
                }
                
                // Wait for content script to initialize
                await new Promise(resolve => setTimeout(resolve, 1000));
                
                // Send highlight message
                console.log('[WebPageIndexer] Sending highlight message to tab');
                const success = await sendMessageToTab(tabs[0].id, {
                    action: 'highlight',
                    text: query
                });
                
                console.log('[WebPageIndexer] Highlight message sent, success:', success);
                return success;
            } else {
                console.log('[WebPageIndexer] Opening new tab for URL:', url);
                // If tab doesn't exist, open it in a new tab
                const newTab = await chrome.tabs.create({ url: url });
                console.log('[WebPageIndexer] Created new tab:', newTab.id);
                
                // Wait for the page to load before sending highlight message
                return new Promise((resolve) => {
                    chrome.tabs.onUpdated.addListener(function listener(tabId, info) {
                        if (tabId === newTab.id && info.status === 'complete') {
                            console.log('[WebPageIndexer] New tab loaded completely');
                            chrome.tabs.onUpdated.removeListener(listener);
                            // Wait for content script to load
                            setTimeout(async () => {
                                try {
                                    console.log('[WebPageIndexer] Sending highlight message to new tab');
                                    const success = await sendMessageToTab(tabId, {
                                        action: 'highlight',
                                        text: query
                                    });
                                    console.log('[WebPageIndexer] Highlight message sent to new tab, success:', success);
                                    resolve(success);
                                } catch (error) {
                                    console.error('[WebPageIndexer] Error sending message to new tab:', error);
                                    resolve(false);
                                }
                            }, 2000);
                        }
                    });
                });
            }
        } catch (error) {
            console.error('[WebPageIndexer] Error handling tab activation:', error);
            return false;
        }
    }

    function highlightText(text, query) {
        if (!query) return text;
        
        // Escape special characters in the query
        const escapedQuery = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        const regex = new RegExp(`(${escapedQuery})`, 'gi');
        return text.replace(regex, '<span class="highlight">$1</span>');
    }
}); 