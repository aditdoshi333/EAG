# Global Shopping Wishlist Chrome Extension

A Chrome extension that allows you to save products from any website to a universal wishlist.

## Features

- Add any product from any website to your wishlist
- Automatically detects product title, price, and image when available
- **Edit product information** - customize the product name and price before saving
- View all your saved items in one place
- Easily navigate to your saved products
- Add or remove items from your wishlist

## Installation

1. Download or clone this repository
2. Open Chrome and navigate to `chrome://extensions/`
3. Enable "Developer Mode" by toggling the switch in the top right corner
4. Click "Load unpacked" and select the folder containing the extension files
5. The extension should now be installed and visible in your Chrome toolbar

## Usage

### Adding items to your wishlist
1. Navigate to any product page
2. Click the extension icon in your Chrome toolbar
3. Review the detected product information
4. **Edit the product name and price if needed**
5. Click "Add to Wishlist"

### Viewing your wishlist
1. Click the extension icon in your Chrome toolbar
2. Click the "My Wishlist" tab
3. Browse through your saved items
4. Click on any item to navigate to its page

### Removing items from your wishlist
1. View your wishlist as described above
2. Click the "Remove" button next to any item you want to delete

## How it works

The extension tries to automatically detect product information by scanning the page for common product page elements. It looks for:

- Product title
- Price
- Product image

The extension is designed to work with many popular shopping websites, but may have varying results on less common sites. **That's why you can now manually edit the product name and price before adding them to your wishlist.**

## Supported Sites

While the extension should work on any website, it has enhanced product detection for:

- Amazon
- Walmart
- eBay
- Best Buy
- Target
- Etsy
- And many more generic online shops

## Limitations

- Product detection may not work perfectly on all websites (but you can manually edit the information)
- Some websites may block content scripts from extracting information
- The extension uses Chrome's storage sync API, which has storage limits (512KB) 