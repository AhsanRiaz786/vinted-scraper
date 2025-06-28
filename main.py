from playwright.sync_api import sync_playwright, TimeoutError
import re
import time
import math
import os

base_url = "https://www.vinted.de/catalog/26-sunglasses?search_id=24435863200&time=1751113385"
filename = "flared.jeans.xxxs"
heart_limit = 0
items_per_page = 500  # Items per HTML page



def extract_id(text):
    match = re.search(r'selectable-item-brand-(\d+)', text)
    return int(match.group(1)) if match else None


def get_brands(playwright):
    """Extracts all brand IDs and names from the filter options."""
    brands = []  # Will store tuples of (brand_id, brand_name)
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
        for filter in filters:
            if(filter.query_selector("span.web_ui__Text__text.web_ui__Text__subtitle.web_ui__Text__left.web_ui__Text__amplified.web_ui__Text__truncated").inner_text() == "Marke"):
                brand_filter = filter
                break
            else:
                continue
        
        button = brand_filter.query_selector("button")
        button.click()
        
        # Extract brand IDs and names
        brand_elements = brand_filter.query_selector_all("li.pile__element")
        for brand_element in brand_elements:
            try:
                brand_data_testid = brand_element.query_selector("div.web_ui__Cell__cell.web_ui__Cell__default.web_ui__Cell__navigating").get_attribute("data-testid")
                brand_id = extract_id(brand_data_testid)
                
                # Try multiple selectors for brand name
                brand_name = None
                name_selectors = [
                    "span.web_ui__Text__text.web_ui__Text__title.web_ui__Text__left",
                    "span.web_ui__Text__text.web_ui__Text__title",
                    "span[class*='web_ui__Text__title']",
                    ".web_ui__Cell__navigating span"
                ]
                
                for selector in name_selectors:
                    name_element = brand_element.query_selector(selector)
                    if name_element:
                        brand_name = name_element.inner_text().strip()
                        if brand_name:
                            break
                
                if brand_id and brand_name:
                    brands.append((brand_id, brand_name))
                    print(f"Found brand: {brand_name} (ID: {brand_id})")
                elif brand_id:
                    # Fallback to using ID as name if name extraction fails
                    brands.append((brand_id, f"Brand_{brand_id}"))
                    print(f"Found brand: Brand_{brand_id} (ID: {brand_id})")
                    
            except Exception as e:
                print(f"Error extracting brand info: {e}")
                
    print(f"Found {len(brands)} brands to scrape")
    return brands


def get_items_for_brand(page, brand_id, brand_name, unique_urls):
    """Scrapes all items for a specific brand."""
    items = []
    pages = 1
    brand_items_count = 0
    
    while True:
        brand_url = f"{base_url}&brand_ids[]={brand_id}&page={pages}"
        print(f"  Scraping {brand_name}, page {pages}...")
        page.goto(brand_url)
        time.sleep(1)

        try:
            # Wait until items are loaded or timeout after 5 seconds
            page.wait_for_selector("div.feed-grid__item-content", timeout=5000)
            item_elements = page.query_selector_all("div.feed-grid__item-content")
        except TimeoutError:
            print(f"  No more items found for {brand_name}. Moving to next brand.")
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
                        items.append([hearts, price, image, url, brand_name])
                        page_items += 1
                        brand_items_count += 1
            except Exception as e:
                print(f"    Error extracting item data: {e}")
        
        if page_items == 0:
            break
            
        pages += 1

    print(f"  {brand_name} completed: {brand_items_count} unique items found")
    return items


def get_items(playwright):
    """Scrapes all items from all brands using Playwright."""
    brands = get_brands(playwright)
    all_items = []
    unique_urls = set()  # To track unique items by URL
    
    with playwright.chromium.launch(headless=True) as browser:
        page = browser.new_page()
        total_items = 0
        
        for i, (brand_id, brand_name) in enumerate(brands, 1):
            print(f"Scraping brand {i}/{len(brands)}: {brand_name}...")
            brand_items = get_items_for_brand(page, brand_id, brand_name, unique_urls)
            all_items.extend(brand_items)
            total_items += len(brand_items)
            print(f"Total items so far: {total_items}")
            
            # Small delay between brands to avoid being rate limited
            time.sleep(3)

        print(f"Total unique items scraped from all brands: {total_items}")
    return all_items


def sort(item_data):
    """Sorts items by number of likes in descending order."""
    return sorted(item_data, key=lambda x: x[0], reverse=True)


def write_paginated_html(item_data):
    """Writes sorted items to paginated HTML files in a dedicated folder."""
    total_items = len(item_data)
    total_pages = math.ceil(total_items / items_per_page)
    
    # Create output directory
    output_dir = filename
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")
    
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
                prev_file = f"page_{page_num}.html"
                nav_links += f"<a href='{prev_file}' style='margin: 0 10px; padding: 5px 10px; background: #007bff; color: white; text-decoration: none; border-radius: 3px;'>← Previous</a>"
            
            # Next page link
            if page_num < total_pages - 1:
                next_file = f"page_{page_num + 2}.html"
                nav_links += f"<a href='{next_file}' style='margin: 0 10px; padding: 5px 10px; background: #007bff; color: white; text-decoration: none; border-radius: 3px;'>Next →</a>"
            
            nav_links += "</div></div>"
        
        # Generate HTML content
        html_str = f"""
        <html>
        <head>
            <title>{filename} - Page {page_num + 1}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                .header {{ text-align: center; margin-bottom: 20px; }}
                .items-container {{ display: flex; flex-wrap: wrap; justify-content: center; }}
                .item {{ width: 200px; margin: 10px; border: 1px solid #ddd; border-radius: 8px; overflow: hidden; background: white; transition: all 0.3s ease; }}
                .item img {{ width: 100%; height: auto; }}
                .item-info {{ padding: 10px; text-align: center; }}
                .item a {{ text-decoration: none; color: inherit; }}
                .item:hover {{ box-shadow: 0 4px 12px rgba(0,0,0,0.15); transform: translateY(-2px); }}
                .brand-name {{ color: #666; font-size: 12px; font-weight: bold; }}
                .hearts {{ color: #e74c3c; font-weight: bold; }}
                .price {{ color: #27ae60; font-weight: bold; font-size: 14px; }}
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
        
        for hearts, price, image, link, brand_name in page_items:
            html_str += f"""
            <div class="item">
                <a href='{link}' target='_blank'>
                    <img src='{image}' alt='Item from {brand_name}'>
                    <div class="item-info">
                        <p class="hearts">❤️ {hearts}</p>
                        <p class="price">€{price}</p>
                        <p class="brand-name">{brand_name}</p>
                    </div>
                </a>
            </div>
            """
        
        html_str += "</div>"
        html_str += nav_links  # Add navigation at bottom too
        html_str += "</body></html>"
        
        # Write to file in the dedicated folder
        page_filename = f"page_{page_num + 1}.html"
        file_path = os.path.join(output_dir, page_filename)
        with open(file_path, "w", encoding="utf-8") as html_file:
            html_file.write(html_str)
        
        print(f"Created {output_dir}/{page_filename} with {len(page_items)} items")
    
    print(f"All {total_pages} HTML pages created successfully in '{output_dir}' folder!")
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
