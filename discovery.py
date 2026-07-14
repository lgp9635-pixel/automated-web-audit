import asyncio
import sys # <-- Make sure to import sys!
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

# Read the URL from the terminal command
if len(sys.argv) < 2:
    print("\n❌ Error: Please provide a URL. Example: python3 discovery.py http://www.deadlinkcity.com/")
    sys.exit(1)

START_URL = sys.argv[1]
target_domain = urlparse(START_URL).netloc
visited = set()
to_visit = [START_URL]
all_links = set()

async def discover():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        while to_visit:
            url = to_visit.pop(0)
            if url in visited: continue
            visited.add(url)
            
            print(f"Crawling: {url}")
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=10000)
                soup = BeautifulSoup(await page.content(), "html.parser")
                links = soup.find_all("a", href=True)
                print(f"Found {len(links)} links on {url}")
                
                for a in links:
                    link = urljoin(url, a.get("href")).split('#')[0]
                    # Check if domain matches
                    if target_domain in link:
                        if link not in visited:
                            all_links.add(link)
                            to_visit.append(link)
                    else:
                        print(f"  Skipping (not same domain): {link}")
            except Exception as e:
                print(f"  Error: {e}")
        
        # FINAL TOTAL PRINT
        print("\n" + "="*30)
        print(f"✅ Total unique links found: {len(all_links)}")
        print("="*30)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(discover())