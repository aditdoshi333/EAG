// DOM Elements
const currentTabBtn = document.getElementById('currentTabBtn');
const wishlistTabBtn = document.getElementById('wishlistTabBtn');
const currentItemTab = document.getElementById('currentItemTab');
const wishlistTab = document.getElementById('wishlistTab');
const itemBasicInfo = document.getElementById('itemBasicInfo');
const productTitleInput = document.getElementById('productTitle');
const productPriceInput = document.getElementById('productPrice');
const itemImage = document.getElementById('itemImage');
const addToWishlistBtn = document.getElementById('addToWishlistBtn');
const wishlistItems = document.getElementById('wishlistItems');

// Current item data
let currentItem = {
  url: '',
  title: '',
  price: '',
  imageUrl: ''
};

// Tab switching
currentTabBtn.addEventListener('click', () => {
  showTab('current');
});

wishlistTabBtn.addEventListener('click', () => {
  showTab('wishlist');
  loadWishlistItems();
});

function showTab(tabName) {
  // Update button states
  currentTabBtn.classList.toggle('active', tabName === 'current');
  wishlistTabBtn.classList.toggle('active', tabName === 'wishlist');
  
  // Show the selected tab
  currentItemTab.classList.toggle('visible', tabName === 'current');
  wishlistTab.classList.toggle('visible', tabName === 'wishlist');
}

// Load current page info
async function loadCurrentPageInfo() {
  // Get the active tab
  let [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  
  // Save basic URL and title from the tab
  currentItem.url = tab.url;
  currentItem.title = tab.title;
  
  // Show basic page info while we try to extract more details
  displayBasicInfo();
  
  // Execute content script to get additional info
  try {
    // Send message to content script to get product details
    chrome.tabs.sendMessage(tab.id, { action: 'getProductInfo' }, response => {
      if (response && response.success) {
        // Update with additional product details if available
        if (response.title) currentItem.title = response.title;
        if (response.price) currentItem.price = response.price;
        if (response.imageUrl) currentItem.imageUrl = response.imageUrl;
      }
      
      // Display the item info and populate the input fields
      displayBasicInfo();
      populateEditableFields();
      displayProductImage();
    });
  } catch (error) {
    console.error('Error getting product info:', error);
    displayBasicInfo();
    populateEditableFields();
  }
}

// Display basic item information
function displayBasicInfo() {
  let html = `<p><strong>Page URL:</strong></p>`;
  html += `<p class="item-url">${currentItem.url}</p>`;
  
  if (currentItem.title) {
    html += `<p><strong>Detected Title:</strong> ${currentItem.title}</p>`;
  } else {
    html += `<p><strong>Detected Title:</strong> <em>None detected</em></p>`;
  }
  
  itemBasicInfo.innerHTML = html;
}

// Populate the editable fields with current values
function populateEditableFields() {
  productTitleInput.value = currentItem.title || '';
  productPriceInput.value = currentItem.price || '';
}

// Display product image if available
function displayProductImage() {
  if (currentItem.imageUrl) {
    itemImage.innerHTML = `<img src="${currentItem.imageUrl}" class="item-image" alt="Product Image">`;
  } else {
    itemImage.innerHTML = '';
  }
}

// Add to wishlist button
addToWishlistBtn.addEventListener('click', () => {
  // Get values from editable fields
  const customTitle = productTitleInput.value.trim();
  const customPrice = productPriceInput.value.trim();
  
  // Check if we have the minimum required info
  if (currentItem.url && customTitle) {
    // Get existing wishlist
    chrome.storage.sync.get(['wishlist'], result => {
      const wishlist = result.wishlist || [];
      
      // Check if item is already in wishlist
      const exists = wishlist.some(item => item.url === currentItem.url);
      
      if (!exists) {
        // Add current item to wishlist with custom values
        wishlist.push({
          url: currentItem.url,
          title: customTitle, // Use the custom title
          price: customPrice, // Use the custom price
          imageUrl: currentItem.imageUrl,
          dateAdded: new Date().toISOString()
        });
        
        // Save updated wishlist
        chrome.storage.sync.set({ wishlist }, () => {
          alert('Item added to wishlist!');
          // Switch to wishlist tab
          showTab('wishlist');
          loadWishlistItems();
        });
      } else {
        alert('This item is already in your wishlist!');
      }
    });
  } else {
    alert('Please enter a product name before adding to wishlist.');
  }
});

// Load wishlist items
function loadWishlistItems() {
  chrome.storage.sync.get(['wishlist'], result => {
    const wishlist = result.wishlist || [];
    
    if (wishlist.length === 0) {
      wishlistItems.innerHTML = '<div class="empty-list">Your wishlist is empty.</div>';
      return;
    }
    
    let html = '';
    
    // Sort wishlist by date added (newest first)
    wishlist.sort((a, b) => new Date(b.dateAdded) - new Date(a.dateAdded));
    
    wishlist.forEach((item, index) => {
      let itemHtml = `
        <div class="wishlist-item">
          <div class="item-title" data-url="${item.url}">
            ${item.title || 'Unnamed Product'}
      `;
      
      if (item.price) {
        itemHtml += ` - ${item.price}`;
      }
      
      itemHtml += `
          </div>
          <button class="remove-btn" data-index="${index}">Remove</button>
        </div>
      `;
      
      html += itemHtml;
    });
    
    wishlistItems.innerHTML = html;
    
    // Add click event for items to open their URL
    document.querySelectorAll('.item-title').forEach(el => {
      el.addEventListener('click', function() {
        const url = this.getAttribute('data-url');
        chrome.tabs.create({ url });
      });
    });
    
    // Add click event for remove buttons
    document.querySelectorAll('.remove-btn').forEach(btn => {
      btn.addEventListener('click', function() {
        const index = parseInt(this.getAttribute('data-index'));
        removeWishlistItem(index);
      });
    });
  });
}

// Remove item from wishlist
function removeWishlistItem(index) {
  chrome.storage.sync.get(['wishlist'], result => {
    const wishlist = result.wishlist || [];
    
    if (index >= 0 && index < wishlist.length) {
      wishlist.splice(index, 1);
      
      chrome.storage.sync.set({ wishlist }, () => {
        // Reload wishlist display
        loadWishlistItems();
      });
    }
  });
}

// Initialize popup
document.addEventListener('DOMContentLoaded', function() {
  loadCurrentPageInfo();
}); 