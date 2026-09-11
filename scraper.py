import json
from playwright.sync_api import sync_playwright

def scrape_links():
    urls = [
        "https://mybuffstreams.plus/nflstreams2",
        "https://mybuffstreams.plus/mlb-live-streams",
        "https://mybuffstreams.plus/mmastreams2",
        "https://mybuffstreams.plus/boxingstreams2",
        "https://mybuffstreams.plus/nbastreams2"
    ]
    
    all_data = []
    global_id = 1

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled', '--no-sandbox']
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        for url in urls:
            try:
                print(f"Scraping: {url}")
                page.goto(url, timeout=45000)
                page.wait_for_timeout(3000)
                
                elements = page.query_selector_all("a.competition")
                for el in elements:
                    title = el.get_attribute("title") or "No Title"
                    href = el.get_attribute("href") or "#"
                    all_data.append({"id": global_id, "title": title, "href": href})
                    global_id += 1
            except Exception as e:
                print(f"Skipping {url} due to error: {e}")
                continue
        
        with open("links.json", "w") as f:
            json.dump(all_data, f, indent=2)
            
        browser.close()

if __name__ == "__main__":
    scrape_links()
