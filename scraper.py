import json
import re
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
                    raw_text = el.get_attribute("title")
                    if not raw_text or raw_text.strip() == "":
                        raw_text = el.inner_text().strip()
                    if not raw_text:
                        raw_text = "No Title"
                        
                    href = el.get_attribute("href") or "#"
                    
                    # Extract title (everything before the hyphen)
                    title_clean = raw_text
                    for sep in ['-', '–']:
                        if sep in raw_text:
                            title_clean = raw_text.split(sep)[0]
                            break
                    title_clean = title_clean.strip()
                    
                    # Extract time info (e.g., "02:00 PM ET")
                    time_match = re.search(r'\d{1,2}:\d{2}\s*(?:AM|PM)\s*(?:ET|MT|PT|CT)?', raw_text, re.IGNORECASE)
                    time_str = time_match.group(0).strip() if time_match else ""
                    
                    # Extract day/date keyword if present (e.g., "Sat", "Sep 14", "Tomorrow")
                    day_match = re.search(r'(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun|Today|Tomorrow|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2})', raw_text, re.IGNORECASE)
                    day_str = day_match.group(0).strip() if day_match else ""
                    
                    # Format standard display time string
                    display_time = f"{day_str} @ {time_str}" if day_str and time_str else (time_str or day_str or "Upcoming")

                    all_data.append({
                        "id": global_id, 
                        "category": src['category'],
                        "title": title_clean if title_clean else raw_text, 
                        "time": display_time,
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
