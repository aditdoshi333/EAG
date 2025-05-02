// Background script to handle page indexing
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "indexPage") {
        // Forward the indexing request to the content script
        chrome.tabs.sendMessage(sender.tab.id, { action: "indexPage" });
    }
});

// Listen for tab updates
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    // Only proceed if the page has finished loading
    if (changeInfo.status === 'complete' && tab.url && tab.url.startsWith('http')) {
        console.log('Page loaded:', tab.url);
        
        // Inject content script
        chrome.scripting.executeScript({
            target: { tabId: tabId },
            files: ['content.js']
        }).catch(err => console.error('Failed to inject content script:', err));
    }
}); 