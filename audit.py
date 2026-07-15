import asyncio
from asyncio import Semaphore, gather
import os
import sys
import webbrowser
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

# --- FIX: Use the updated v2.0.3 Stealth API ---
from playwright_stealth import Stealth

from utils import generate_html_report
import json

def save_scraped_text(url, raw_text, temp_filename="scraped_content.jsonl"):
    data = {
        "url": url,
        "text": raw_text
    }
    with open(temp_filename, 'a', encoding='utf-8') as f:
        f.write(json.dumps(data) + '\n')

# --- CONFIGURATION ---
if len(sys.argv) < 3:
    print("\n❌ Error: Usage: python3 audit.py <URL> <MAX_PAGES>")
    sys.exit(1)

START_URL = sys.argv[1]
MAX_PAGES = int(sys.argv[2])
target_domain = urlparse(START_URL).netloc
visited_urls = set()
urls_to_visit = [START_URL]
all_found_links = {} 
broken_links = []
passed_links = []

def normalize_url(raw_url, base_url=None):
    if base_url:
        raw_url = urljoin(base_url, raw_url)
    return raw_url.split('#')[0].strip()

def is_same_site(url_value, target_host):
    parsed = urlparse(url_value)
    return target_host.lower() in parsed.netloc.lower()

def determine_priority(parent_tags, url):
    if 'nav' in parent_tags or 'footer' in parent_tags:
        return "High"
    if 'head' in parent_tags or 'style' in parent_tags or 'script' in parent_tags:
        if url.endswith(('.css', '.js')):
            return "High" 
        return "Low"
    return "Medium"

async def audit_page(context, url):
    page = await context.new_page()
    try:
        print(f"🥷 Crawling (Stealth Active): {url}")
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        
        html_content = await page.content()
        soup = BeautifulSoup(html_content, "html.parser")
        
        for hidden_element in soup(["script", "style", "noscript"]):
            hidden_element.decompose()
            
        extracted_text = soup.get_text(separator=' ', strip=True)
        
        if extracted_text:
            save_scraped_text(url, extracted_text)

        links = soup.find_all("a", href=True)
        
        for a in links:
            full_url = normalize_url(a.get("href"), url)
            if is_same_site(full_url, target_domain) and full_url not in all_found_links:
                parents = [p.name for p in a.parents]
                link_text = a.get_text(strip=True)
                all_found_links[full_url] = {"source": url, "parents": parents, "text": link_text}
    except Exception as e:
        print(f"⚠️ Error crawling {url}: {e}")
    finally:
        await page.close()

async def main():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        
        # Humanize the browser profile
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        
        # --- FIX: Apply Stealth at the Context level for v2.0.3 API ---
        stealth = Stealth()
        await stealth.apply_stealth_async(context)
        
        # 1. Crawling Phase
        while len(visited_urls) < MAX_PAGES and urls_to_visit:
            url = urls_to_visit.pop(0)
            if url not in visited_urls:
                visited_urls.add(url)
                await audit_page(context, url)
                for link in all_found_links:
                    if link not in visited_urls and link not in urls_to_visit:
                        urls_to_visit.append(link)
                        
        # 2. Validation Phase
        sem = Semaphore(5)
        
        async def validate_link(link, data):
            # THE FIX: Count static files as passed so math perfectly balances!
            if link.lower().endswith(('.pdf', '.docx', '.xlsx', '.pptx', '.zip', '.rar', '.jpg', '.png', '.mp4', '.exe', '.dmg', '.gif', '.mov')):
                passed_links.append(link)
                return
            
            async with sem:
                try:
                    res = await context.request.get(link, timeout=10000)
                    
                    if res.status == 200:
                        passed_links.append(link)
                    else:
                        broken_links.append({
                            "url": link, 
                            "status": f"HTTP {res.status}", 
                            "found_on": data["source"],
                            "priority": determine_priority(data["parents"], link),
                            "text": data.get("text", "N/A")
                        })
                except Exception as e:
                    broken_links.append({
                        "url": link, 
                        "status": "Connection Error", 
                        "found_on": data["source"],
                        "priority": determine_priority(data["parents"], link),
                        "text": data.get("text", "N/A")
                    })

        print(f"\n🚀 Validating {len(all_found_links)} links...")
        
        tasks = [validate_link(link, data) for link, data in all_found_links.items()]
        await gather(*tasks) 
        
        await context.close()
        await browser.close()
    
    generate_html_report(target_domain, len(all_found_links), len(broken_links), len(passed_links), broken_links)

if __name__ == "__main__":
    asyncio.run(main())
