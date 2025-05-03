class ShoppingTools {
  constructor() {
    this.supportedSites = ['amazon', 'walmart', 'bestbuy', 'ebay'];
  }

  async searchProducts(query, site) {
    window.logger.logToolInput('searchProducts', { query, site });
    
    try {
      let products;
      switch (site) {
        case 'amazon':
          products = await this.scrapeAmazon(query);
          break;
        case 'walmart':
          products = await this.scrapeWalmart(query);
          break;
        case 'bestbuy':
          products = await this.scrapeBestBuy(query);
          break;
        case 'ebay':
          products = await this.scrapeEbay(query);
          break;
        default:
          throw new Error(`Unsupported site: ${site}`);
      }

      window.logger.logToolOutput('searchProducts', products);
      return products;
    } catch (error) {
      window.logger.logToolOutput('searchProducts', { error: error.message });
      throw error;
    }
  }

  async scrapeAmazon(query) {
    // Using a proxy service to avoid CORS issues
    const proxyUrl = 'https://api.allorigins.win/raw?url=';
    const searchUrl = `https://www.amazon.com/s?k=${encodeURIComponent(query)}`;
    
    const response = await fetch(proxyUrl + encodeURIComponent(searchUrl));
    const html = await response.text();
    
    // Create a DOM parser
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, 'text/html');
    
    // Extract product information
    const products = [];
    const items = doc.querySelectorAll('.s-result-item');
    
    items.forEach(item => {
      const nameElement = item.querySelector('h2 a span');
      const priceElement = item.querySelector('.a-price .a-offscreen');
      const ratingElement = item.querySelector('.a-icon-star-small');
      const reviewsElement = item.querySelector('.a-link-normal .s-link-style');
      
      if (nameElement && priceElement) {
        products.push({
          name: nameElement.textContent.trim(),
          price: parseFloat(priceElement.textContent.replace('$', '').replace(',', '')),
          rating: ratingElement ? parseFloat(ratingElement.textContent.split(' ')[0]) : 0,
          reviews: reviewsElement ? parseInt(reviewsElement.textContent.replace(',', '')) : 0,
          url: 'https://www.amazon.com' + item.querySelector('h2 a').getAttribute('href'),
          site: 'amazon'
        });
      }
    });

    return products.slice(0, 10); // Limit to 10 results
  }

  async scrapeWalmart(query) {
    const proxyUrl = 'https://api.allorigins.win/raw?url=';
    const searchUrl = `https://www.walmart.com/search?q=${encodeURIComponent(query)}`;
    
    const response = await fetch(proxyUrl + encodeURIComponent(searchUrl));
    const html = await response.text();
    
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, 'text/html');
    
    const products = [];
    const items = doc.querySelectorAll('[data-item-id]');
    
    items.forEach(item => {
      const nameElement = item.querySelector('[data-automation-id="product-title"]');
      const priceElement = item.querySelector('[data-automation-id="product-price"]');
      const ratingElement = item.querySelector('[data-automation-id="product-rating"]');
      const reviewsElement = item.querySelector('[data-automation-id="product-review-count"]');
      
      if (nameElement && priceElement) {
        products.push({
          name: nameElement.textContent.trim(),
          price: parseFloat(priceElement.textContent.replace('$', '').replace(',', '')),
          rating: ratingElement ? parseFloat(ratingElement.textContent.split(' ')[0]) : 0,
          reviews: reviewsElement ? parseInt(reviewsElement.textContent.replace(',', '')) : 0,
          url: 'https://www.walmart.com' + item.querySelector('a').getAttribute('href'),
          site: 'walmart'
        });
      }
    });

    return products.slice(0, 10);
  }

  async scrapeBestBuy(query) {
    const proxyUrl = 'https://api.allorigins.win/raw?url=';
    const searchUrl = `https://www.bestbuy.com/site/searchpage.jsp?st=${encodeURIComponent(query)}`;
    
    const response = await fetch(proxyUrl + encodeURIComponent(searchUrl));
    const html = await response.text();
    
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, 'text/html');
    
    const products = [];
    const items = doc.querySelectorAll('.sku-item');
    
    items.forEach(item => {
      const nameElement = item.querySelector('.sku-title');
      const priceElement = item.querySelector('.priceView-customer-price span');
      const ratingElement = item.querySelector('.c-ratings-reviews');
      const reviewsElement = item.querySelector('.c-ratings-reviews .c-reviews-count');
      
      if (nameElement && priceElement) {
        products.push({
          name: nameElement.textContent.trim(),
          price: parseFloat(priceElement.textContent.replace('$', '').replace(',', '')),
          rating: ratingElement ? parseFloat(ratingElement.getAttribute('data-rating')) : 0,
          reviews: reviewsElement ? parseInt(reviewsElement.textContent.replace(',', '')) : 0,
          url: 'https://www.bestbuy.com' + item.querySelector('a').getAttribute('href'),
          site: 'bestbuy'
        });
      }
    });

    return products.slice(0, 10);
  }

  async scrapeEbay(query) {
    const proxyUrl = 'https://api.allorigins.win/raw?url=';
    const searchUrl = `https://www.ebay.com/sch/i.html?_nkw=${encodeURIComponent(query)}`;
    
    const response = await fetch(proxyUrl + encodeURIComponent(searchUrl));
    const html = await response.text();
    
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, 'text/html');
    
    const products = [];
    const items = doc.querySelectorAll('.s-item');
    
    items.forEach(item => {
      const nameElement = item.querySelector('.s-item__title');
      const priceElement = item.querySelector('.s-item__price');
      const ratingElement = item.querySelector('.x-star-rating');
      const reviewsElement = item.querySelector('.s-item__reviews-count');
      
      if (nameElement && priceElement) {
        products.push({
          name: nameElement.textContent.trim(),
          price: parseFloat(priceElement.textContent.replace('$', '').replace(',', '')),
          rating: ratingElement ? parseFloat(ratingElement.getAttribute('aria-label').split(' ')[0]) : 0,
          reviews: reviewsElement ? parseInt(reviewsElement.textContent.replace(',', '')) : 0,
          url: item.querySelector('.s-item__link').getAttribute('href'),
          site: 'ebay'
        });
      }
    });

    return products.slice(0, 10);
  }

  async comparePrices(products) {
    window.logger.logToolInput('comparePrices', { products });
    
    try {
      const priceComparison = {
        lowestPrice: Math.min(...products.map(p => p.price)),
        highestPrice: Math.max(...products.map(p => p.price)),
        averagePrice: products.reduce((sum, p) => sum + p.price, 0) / products.length,
        priceHistory: await this.getPriceHistory(products)
      };

      window.logger.logToolOutput('comparePrices', priceComparison);
      return priceComparison;
    } catch (error) {
      window.logger.logToolOutput('comparePrices', { error: error.message });
      throw error;
    }
  }

  async getPriceHistory(products) {
    // For demo purposes, we'll generate some mock price history
    return products.map(p => ({
      name: p.name,
      currentPrice: p.price,
      priceTrend: Math.random() > 0.5 ? 'increasing' : 'decreasing',
      historicalPrices: Array.from({ length: 7 }, () => ({
        date: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        price: p.price * (0.8 + Math.random() * 0.4)
      }))
    }));
  }

  async aggregateReviews(products) {
    window.logger.logToolInput('aggregateReviews', { products });
    
    try {
      const reviewAggregation = await Promise.all(
        products.map(async product => {
          const reviews = await this.fetchProductReviews(product);
          return {
            name: product.name,
            rating: product.rating,
            reviewCount: product.reviews,
            sentiment: this.analyzeSentiment(reviews),
            keyHighlights: this.extractKeyHighlights(reviews)
          };
        })
      );

      window.logger.logToolOutput('aggregateReviews', reviewAggregation);
      return reviewAggregation;
    } catch (error) {
      window.logger.logToolOutput('aggregateReviews', { error: error.message });
      throw error;
    }
  }

  async fetchProductReviews(product) {
    // For demo purposes, we'll generate some mock reviews
    return Array.from({ length: 5 }, (_, i) => ({
      rating: Math.floor(Math.random() * 3) + 3, // 3-5 stars
      text: `Sample review ${i + 1} for ${product.name}`,
      date: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString()
    }));
  }

  analyzeSentiment(reviews) {
    // Simple sentiment analysis based on average rating
    const avgRating = reviews.reduce((sum, r) => sum + r.rating, 0) / reviews.length;
    if (avgRating >= 4.5) return 'very positive';
    if (avgRating >= 4) return 'positive';
    if (avgRating >= 3.5) return 'neutral';
    if (avgRating >= 3) return 'negative';
    return 'very negative';
  }

  extractKeyHighlights(reviews) {
    // For demo purposes, we'll return some common highlights
    return [
      'Good quality',
      'Fast delivery',
      'Value for money',
      'Great customer service',
      'Product meets expectations'
    ];
  }

  async searchAllSites(query) {
    const allProducts = [];
    
    for (const site of this.supportedSites) {
      try {
        const products = await this.searchProducts(query, site);
        allProducts.push(...products);
      } catch (error) {
        console.error(`Error searching ${site}:`, error);
        // Continue with other sites even if one fails
      }
    }

    return allProducts;
  }
}

// Create a global tools instance
window.shoppingTools = new ShoppingTools(); 