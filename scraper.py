import json
from playwright.sync_api import sync_playwright

def scrape_links():
    sources = [
        {"url": "https://mybuffstreams.plus/nflstreams2", "category": "NFL"},
        {"url": "https://mybuffstreams.plus/mlb-live-streams", "category": "MLB"},
        {"url": "https://mybuffstreams.plus/mmastreams2", "category": "MMA"},
        {"url": "https://mybuffstreams.plus/boxingstreams2", "category": "Boxing"},
        {"url": "https://mybuffstreams.plus/nbastreams2", "category": "NBA"}
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
        
        for src in sources:
            try:
                print(f"Scraping {src['category']}: {src['url']}")
                page.goto(src['url'], timeout=45000)
                page.wait_for_timeout(3000)
                
                elements = page.query_selector_all("a.competition")
                for el in elements:
                    # Check title attribute first, then fall back to visible text inside the element
                    title = el.get_attribute("title")
                    if not title or title.strip() == "":
                        title = el.inner_text().strip()
                    if not title:
                        title = "No Title"
                        
                    href = el.get_attribute("href") or "#"
                    
                    all_data.append({
                        "id": global_id, 
                        "category": src['category'],
                        "title": title, 
                        "href": href
                    })
                    global_id += 1
            except Exception as e:
                print(f"Skipping {src['url']} due to error: {e}")
                continue
        
        with open("links.json", "w") as f:
            json.dump(all_data, f, indent=2)
            
        browser.close()

if __name__ == "__main__":
    scrape_links()
