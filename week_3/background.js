// Listen for installation
chrome.runtime.onInstalled.addListener(() => {
  // Initialize storage with default values
  chrome.storage.local.get(['openaiApiKey'], (result) => {
    if (!result.openaiApiKey) {
      chrome.storage.local.set({ openaiApiKey: null });
    }
  });
});

// Listen for messages from content script or popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.type === 'getApiKey') {
    chrome.storage.local.get(['openaiApiKey'], (result) => {
      sendResponse({ apiKey: result.openaiApiKey });
    });
    return true; // Will respond asynchronously
  }
  
  if (request.type === 'setApiKey') {
    chrome.storage.local.set({ openaiApiKey: request.apiKey }, () => {
      sendResponse({ success: true });
    });
    return true; // Will respond asynchronously
  }
}); 