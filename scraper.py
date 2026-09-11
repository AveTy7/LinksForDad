import json
from playwright.sync_api import sync_playwright

def scrape_links():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://mybuffstreams.plus/home5", timeout=60000)
        
        # Wait for elements to load
        page.wait_for_selector("a.competition", timeout=15000)
        
        elements = page.query_selector_all("a.competition")
        data = []
        for index, el in enumerate(elements):
            title = el.get_attribute("title") or "No Title"
            href = el.get_attribute("href") or "#"
            data.append({"id": index + 1, "title": title, "href": href})
            
        with open("links.json", "w") as f:
            json.dump(data, f, indent=2)
            
        browser.close()

if __name__ == "__main__":
    scrape_links()
