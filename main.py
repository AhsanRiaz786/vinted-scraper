from playwright.sync_api import sync_playwright, TimeoutError
import re
import time
import math

base_url = "https://www.vinted.de/catalog?search_id=24361207426&time=1750625701&catalog[]=1841&catalog_from=0&page=1&size_ids[]=1226"
filename = "flared.jeans.xxxs"
heart_limit = 0
items_per_page = 500  # Items per HTML page



def extract_id(text):
    match = re.search(r'selectable-item-brand-(\d+)', text)
    return int(match.group(1)) if match else None


def get_brands(playwright):
    """Extracts all brand IDs from the filter options."""
    brand_ids = []
    with playwright.chromium.launch(headless=True) as browser:
        page = browser.new_page()
        page.goto(f"{base_url}")
        time.sleep(3)
        
        # Handle modals
        close_button = page.query_selector("button[data-testid='domain-select-modal-close-button']")
        if close_button:
            close_button.click()
        time.sleep(3)
        accept_button = page.query_selector("button[id='onetrust-accept-btn-handler']")
        if accept_button:
            accept_button.click()
            
        # Navigate to brand filter
        content_container = page.wait_for_selector("section.content-container", timeout=5000)
        filter_bar = content_container.query_selector("div.u-flexbox.u-flex-wrap")
        filters = filter_bar.query_selector_all("div.u-ui-margin-right-regular.u-ui-margin-bottom-regular")
        brand_filter = filters[2]
        button = brand_filter.query_selector("button")
        button.click()
        
        # Extract brand IDs
        brand_elements = brand_filter.query_selector_all("li.pile__element")
        for brand_element in brand_elements:
            brand_data_testid = brand_element.query_selector("div.web_ui__Cell__cell.web_ui__Cell__default.web_ui__Cell__navigating").get_attribute("data-testid")
            brand_id = extract_id(brand_data_testid)
            if brand_id:
                brand_ids.append(brand_id)
                
    print(f"Found {len(brand_ids)} brands to scrape")
    return brand_ids


def get_items_for_brand(page, brand_id, unique_urls):
    """Scrapes all items for a specific brand."""
    items = []
    pages = 1
    brand_items_count = 0
    
    while True:
        brand_url = f"{base_url}&brand_ids[]={brand_id}&page={pages}"
        print(f"  Scraping brand {brand_id}, page {pages}...")
        page.goto(brand_url)

        try:
            # Wait until items are loaded or timeout after 5 seconds
            page.wait_for_selector("div.feed-grid__item-content", timeout=5000)
            item_elements = page.query_selector_all("div.feed-grid__item-content")
        except TimeoutError:
            print(f"  No more items found for brand {brand_id}. Moving to next brand.")
            break

        page_items = 0
        for item in item_elements:
            try:
                hearts_text = item.query_selector("span.web_ui__Text__text.web_ui__Text__caption.web_ui__Text__left").inner_text()
                hearts = int(hearts_text) if hearts_text.isdigit() else 0
                
                if hearts >= heart_limit:
                    price_text = item.query_selector("p.web_ui__Text__text.web_ui__Text__caption.web_ui__Text__left.web_ui__Text__muted").inner_text()
                    price_match = re.findall(r"[-+]?\d*\,\d+|\d+", price_text)
                    price = float(price_match[0].replace(',', '.')) if price_match else 0.0
                    
                    image = item.query_selector_all("img")[0].get_attribute("src")
                    url = item.query_selector("a.new-item-box__overlay.new-item-box__overlay--clickable").get_attribute("href")
                    
                    # Add only unique items based on URL
                    if url not in unique_urls:
                        unique_urls.add(url)
                        items.append([hearts, price, image, url, brand_id])
                        page_items += 1
                        brand_items_count += 1
            except Exception as e:
                print(f"    Error extracting item data: {e}")
        
        if page_items == 0:
            break
            
        pages += 1

    print(f"  Brand {brand_id} completed: {brand_items_count} unique items found")
    return items


def get_items(playwright):
    """Scrapes all items from all brands using Playwright."""
    brand_ids = get_brands(playwright)
    all_items = []
    unique_urls = set()  # To track unique items by URL
    
    with playwright.chromium.launch(headless=False) as browser:
        page = browser.new_page()
        total_items = 0
        
        for i, brand_id in enumerate(brand_ids, 1):
            print(f"Scraping brand {i}/{len(brand_ids)} (ID: {brand_id})...")
            brand_items = get_items_for_brand(page, brand_id, unique_urls)
            all_items.extend(brand_items)
            total_items += len(brand_items)
            print(f"Total items so far: {total_items}")
            
            # Small delay between brands to avoid being rate limited
            time.sleep(1)

        print(f"Total unique items scraped from all brands: {total_items}")
    return all_items


def sort(item_data):
    """Sorts items by number of likes in descending order."""
    return sorted(item_data, key=lambda x: x[0], reverse=True)


def write_paginated_html(item_data):
    """Writes sorted items to paginated HTML files."""
    total_items = len(item_data)
    total_pages = math.ceil(total_items / items_per_page)
    
    print(f"Creating {total_pages} HTML pages with {items_per_page} items each...")
    
    for page_num in range(total_pages):
        start_idx = page_num * items_per_page
        end_idx = min(start_idx + items_per_page, total_items)
        page_items = item_data[start_idx:end_idx]
        
        # Create navigation links
        nav_links = ""
        if total_pages > 1:
            nav_links = "<div style='text-align: center; margin: 20px; font-size: 18px;'>"
            nav_links += f"<p>Page {page_num + 1} of {total_pages} | Items {start_idx + 1}-{end_idx} of {total_items}</p>"
            nav_links += "<div style='margin: 10px;'>"
            
            # Previous page link
            if page_num > 0:
                prev_file = f"{filename}_page_{page_num}.html" if page_num == 1 else f"{filename}_page_{page_num}.html"
                nav_links += f"<a href='{filename}_page_{page_num}.html' style='margin: 0 10px; padding: 5px 10px; background: #007bff; color: white; text-decoration: none; border-radius: 3px;'>← Previous</a>"
            
            # Next page link
            if page_num < total_pages - 1:
                next_file = f"{filename}_page_{page_num + 2}.html"
                nav_links += f"<a href='{next_file}' style='margin: 0 10px; padding: 5px 10px; background: #007bff; color: white; text-decoration: none; border-radius: 3px;'>Next →</a>"
            
            nav_links += "</div></div>"
        
        # Generate HTML content
        html_str = f"""
        <html>
        <head>
            <title>{filename} - Page {page_num + 1}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
                .header {{ text-align: center; margin-bottom: 20px; }}
                .items-container {{ display: flex; flex-wrap: wrap; justify-content: center; }}
                .item {{ width: 200px; margin: 10px; border: 1px solid #ddd; border-radius: 8px; overflow: hidden; }}
                .item img {{ width: 100%; height: auto; }}
                .item-info {{ padding: 10px; text-align: center; }}
                .item a {{ text-decoration: none; color: inherit; }}
                .item:hover {{ box-shadow: 0 4px 8px rgba(0,0,0,0.1); }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Vinted Items - {filename}</h1>
                <p>Items Sorted by Likes (❤️)</p>
            </div>
            {nav_links}
            <div class="items-container">
        """
        
        for hearts, price, image, link, brand_id in page_items:
            html_str += f"""
            <div class="item">
                <a href='{link}' target='_blank'>
                    <img src='{image}' alt='Item image'>
                    <div class="item-info">
                        <p><strong>❤️ {hearts}</strong></p>
                        <p>€{price}</p>
                        <p><small>Brand ID: {brand_id}</small></p>
                    </div>
                </a>
            </div>
            """
        
        html_str += "</div>"
        html_str += nav_links  # Add navigation at bottom too
        html_str += "</body></html>"
        
        # Write to file
        page_filename = f"{filename}_page_{page_num + 1}.html"
        with open(page_filename, "w", encoding="utf-8") as html_file:
            html_file.write(html_str)
        
        print(f"Created {page_filename} with {len(page_items)} items")
    
    print(f"All {total_pages} HTML pages created successfully!")
    return total_pages


def main():
    with sync_playwright() as playwright:
        items = get_items(playwright)
        sorted_data = sort(items)
        total_pages = write_paginated_html(sorted_data)
        print(f"Script completed. Created {total_pages} HTML pages with {len(items)} total items.")

if __name__ == '__main__':
    start_time = time.time()
    main()
    print('--------------------')
    print("Execution time is %s seconds" % "%0.2f" % (time.time() - start_time))
