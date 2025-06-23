from playwright.sync_api import sync_playwright, TimeoutError
import re
import time

base_url = "https://www.vinted.de/catalog?search_id=24361207426&time=1750625701&catalog[]=1841&catalog_from=0&page=1&size_ids[]=1226"
filename = "flared.jeans.xxxs"
heart_limit = 0


def extract_id(text):
    match = re.search(r'selectable-item-brand-(\d+)--title', text)
    return int(match.group(1)) if match else None



def get_brands(playwright):
    brands = []
    with playwright.chromium.launch(headless=False) as browser:
        page = browser.new_page()
        page.goto(f"{base_url}")
        time.sleep(3)
        close_button = page.query_selector("button[data-testid='domain-select-modal-close-button']")
        if close_button:
            close_button.click()
        accept_button = page.query_selector("button[id='onetrust-accept-btn-handler']")
        if accept_button:
            accept_button.click()
        content_container = page.wait_for_selector("section.content-container", timeout=5000)
        filter_bar = content_container.query_selector("div.u-flexbox.u-flex-wrap")
        filters = filter_bar.query_selector_all("div.u-ui-margin-right-regular.u-ui-margin-bottom-regular")
        brand_filter = filters[2]
        button = brand_filter.query_selector("button")
        button.click()
        brands = brand_filter.query_selector_all("li.pile__element")
        for brand in brands:
            brand_id = brand.query_selector("div.web_ui__Cell__cell.web_ui__Cell__default.web_ui__Cell__navigating").get_attribute("data-testid")
            brand_id = extract_id(brand_id)
            brands.append(brand_id)
    return brands

def get_items(playwright):
    """Scrapes all items from fully loaded pages using Playwright."""
    brands = get_brands(playwright)
    items = []
    unique_urls = set()  # To track unique items by URL
    
    with playwright.chromium.launch(headless=True) as browser:
        page = browser.new_page()
        pages = 1
        total_items = 0
        
        while True:
            print(f"Scraping page {pages}...")
            page.goto(f"{base_url}&page={pages}")


            try:
                # Wait until items are loaded or timeout after 5 seconds
                page.wait_for_selector("div.feed-grid__item-content", timeout=5000)
                item_elements = page.query_selector_all("div.feed-grid__item-content")
            except TimeoutError:
                print("No items found on this page. Ending scraping.")
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
                            items.append([hearts, price, image, url])
                            page_items += 1
                except Exception as e:
                    print(f"Error extracting item data: {e}")
            
            print(f"Page {pages} scraped, {page_items} unique items added.")
            total_items += page_items
            pages += 1

        print(f"Total unique items scraped: {total_items}")
    return items

def sort(item_data):
    """Sorts items by number of likes in descending order."""
    return sorted(item_data, key=lambda x: x[0], reverse=True)

def write_html(item_data):
    """Writes sorted items to an HTML file."""
    html_str = "<html><body><p>Items Sorted by Likes</p><div style='display: flex; flex-wrap: wrap;'>"
 
    for hearts, price, image, link in item_data:
        html_str += f"""
        <div style='width: 200px; margin: 10px;'>
            <a href='{link}' target='_blank'>
                <img src='{image}' style='width: 100%; height: auto;'><br>
                <p>❤️ {hearts} - €{price}</p>
            </a>
        </div>
        """
        
    html_str += "</div></body></html>"
    with open(f"{filename}.html", "w", encoding="utf-8") as html_file:
        html_file.write(html_str)

    print(f"{filename}.html was created.")

def main():
    with sync_playwright() as playwright:
        items = get_items(playwright)
        sorted_data = sort(items)
        write_html(sorted_data)
        print("Script completed.")

if __name__ == '__main__':
    start_time = time.time()
    main()
    print('--------------------')
    print("Execution time is %s seconds" % "%0.2f" % (time.time() - start_time))
