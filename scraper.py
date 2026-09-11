import json
from playwright.sync_api import sync_playwright

def scrape_links():
    with sync_playwright() as p:
        # Launch browser with anti-detection flags
        browser = p.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled', '--no-sandbox']
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            page.goto("https://mybuffstreams.plus/home5", timeout=60000)
            
            # Wait a few seconds for Cloudflare's JavaScript challenge to clear
            page.wait_for_timeout(5000)
            
            elements = page.query_selector_all("a.competition")
            data = []
            for index, el in enumerate(elements):
                title = el.get_attribute("title") or "No Title"
                href = el.get_attribute("href") or "#"
                data.append({"id": index + 1, "title": title, "href": href})
                
            with open("links.json", "w") as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"Error during scraping: {e}")
            # Write an empty array so the workflow doesn't completely fail
            with open("links.json", "w") as f:
                json.dump([], f, indent=2)
        finally:
            browser.close()

if __name__ == "__main__":
    scrape_links()
