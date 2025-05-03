// Initialize extension data
chrome.runtime.onInstalled.addListener(() => {
  // Initialize wishlist if it doesn't exist
  chrome.storage.sync.get(['wishlist'], result => {
    if (!result.wishlist) {
      chrome.storage.sync.set({ wishlist: [] });
    }
  });
});

// Listen for messages from content scripts or popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'addToWishlist') {
    addItemToWishlist(message.item, sendResponse);
    return true; // Keep the message channel open for async response
  }
});

// Function to add item to wishlist
function addItemToWishlist(item, callback) {
  chrome.storage.sync.get(['wishlist'], result => {
    const wishlist = result.wishlist || [];
    
    // Check if item is already in wishlist
    const exists = wishlist.some(existingItem => existingItem.url === item.url);
    
    if (!exists) {
      // Add item to wishlist
      wishlist.push({
        ...item,
        dateAdded: new Date().toISOString()
      });
      
      // Save updated wishlist
      chrome.storage.sync.set({ wishlist }, () => {
        if (callback) callback({ success: true, message: 'Item added to wishlist' });
      });
    } else {
      if (callback) callback({ success: false, message: 'Item already in wishlist' });
    }
  });
} 