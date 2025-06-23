# 🛍️ Vinted Multi-Brand Scraper

A comprehensive web scraper for Vinted.de that automatically collects items from all available brands and organizes them into paginated HTML files sorted by popularity (number of likes).

## 🌟 Features

- **Multi-Brand Scraping**: Automatically discovers and scrapes items from all available brands
- **Smart Pagination**: Organizes results into multiple HTML files (500 items per page)
- **Popularity Sorting**: Items sorted by number of likes (hearts) in descending order
- **Duplicate Prevention**: Ensures unique items across all brands
- **Progress Tracking**: Real-time progress updates during scraping
- **Responsive HTML Output**: Modern, mobile-friendly design with navigation
- **Brand Recognition**: Displays actual brand names (H&M, Zara, etc.) instead of IDs
- **Error Handling**: Graceful handling of timeouts and missing elements

## 📋 Requirements

- Python 3.7+
- Playwright library
- Internet connection

## 🚀 Installation

1. **Clone or download this repository**
   ```bash
   git clone <repository-url>
   cd vinted-scraper
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Playwright browsers**
   ```bash
   playwright install chromium
   ```

## 🎯 Usage

### Basic Usage

1. **Configure your search** (optional):
   Edit the configuration variables at the top of `main.py`:
   ```python
   base_url = "https://www.vinted.de/catalog?search_id=24361207426&time=1750625701&catalog[]=1841&catalog_from=0&page=1&size_ids[]=1226"
   filename = "flared.jeans.xxxs"
   heart_limit = 0
   items_per_page = 500
   ```

2. **Run the scraper**:
   ```bash
   python main.py
   ```

3. **View results**:
   Open the generated HTML files in your browser:
   - `flared.jeans.xxxs_page_1.html`
   - `flared.jeans.xxxs_page_2.html`
   - etc.

### Example URL Configuration

The scraper works with any Vinted.de search URL. Here are some examples:

**Flared Jeans XXXS:**
```
https://www.vinted.de/catalog?search_id=24361207426&time=1750625701&catalog[]=1841&catalog_from=0&page=1&size_ids[]=1226
```

**Women's Dresses Size S:**
```
https://www.vinted.de/catalog?catalog[]=16&size_ids[]=206&page=1
```

## ⚙️ Configuration Options

| Variable | Description | Default Value |
|----------|-------------|---------------|
| `base_url` | The Vinted search URL to scrape | Flared jeans XXXS search |
| `filename` | Prefix for output HTML files | `"flared.jeans.xxxs"` |
| `heart_limit` | Minimum number of likes required | `0` |
| `items_per_page` | Items per HTML page | `500` |

## 📁 Output Files

The scraper generates multiple files:

### HTML Files
- `{filename}_page_1.html` - First 500 items
- `{filename}_page_2.html` - Next 500 items
- etc.

Each HTML file includes:
- **Item cards** with image, price, likes, and brand name
- **Navigation links** between pages
- **Responsive design** that works on mobile and desktop
- **Direct links** to original Vinted listings

### Console Output
Real-time progress updates showing:
- Brand discovery progress
- Current brand being scraped
- Items found per brand
- Total execution time

## 🔄 How It Works

1. **Brand Discovery**: 
   - Opens the search URL
   - Extracts all available brand filters
   - Collects brand IDs and names

2. **Multi-Brand Scraping**:
   - Iterates through each brand individually
   - Scrapes all pages for each brand
   - Adds `&brand_ids[]={id}` to filter by specific brand

3. **Data Processing**:
   - Removes duplicate items (same URL)
   - Sorts by number of likes (descending)
   - Organizes into pages of 500 items each

4. **HTML Generation**:
   - Creates responsive HTML pages
   - Adds navigation between pages
   - Includes brand names and item details

## 📊 Expected Results

For a typical search, you can expect:
- **10-50 brands** depending on the category
- **1,000-10,000+ items** total
- **Multiple HTML pages** (2-20 pages typical)
- **Execution time**: 5-30 minutes depending on number of items

## 🛠️ Troubleshooting

### Common Issues

**"No items found" error:**
- Check if the base_url is valid and accessible
- Ensure your internet connection is stable
- Try increasing timeout values

**Brand names showing as "Brand_123":**
- This is normal fallback behavior when brand name extraction fails
- The scraper will still work correctly

**Slow performance:**
- The scraper includes 1-second delays between brands to avoid rate limiting
- Large searches with many brands will naturally take longer

### Browser Settings

- Scraper runs in **headless mode** by default for better performance
- Change `headless=True` to `headless=False` to see browser actions
- Brand discovery runs in **headless mode** for speed

## 📝 Example Console Output

```
Found brand: H&M (ID: 7)
Found brand: Zara (ID: 12)
Found brand: Stradivarius (ID: 41)
...
Found 42 brands to scrape

Scraping brand 1/42: H&M...
  Scraping H&M, page 1...
  Scraping H&M, page 2...
  H&M completed: 67 unique items found
Scraping brand 2/42: Zara...
  Scraping Zara, page 1...
  Zara completed: 23 unique items found
Total items so far: 90

...

Total unique items scraped from all brands: 3,247
Creating 7 HTML pages with 500 items each...
Created flared.jeans.xxxs_page_1.html with 500 items
Created flared.jeans.xxxs_page_2.html with 500 items
...
Script completed. Created 7 HTML pages with 3247 total items.
--------------------
Execution time is 18.45 seconds
```

## 🔒 Legal Notice

This scraper is intended for personal use only. Please respect Vinted's terms of service and robots.txt. Use responsibly and avoid overwhelming their servers with requests.

## 🤝 Contributing

Feel free to submit issues, feature requests, or improvements to this scraper! 