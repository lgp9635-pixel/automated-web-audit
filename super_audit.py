import asyncio
import os
import sys
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from jinja2 import Template

# --- DYNAMIC TERMINAL CONFIGURATION ---
if len(sys.argv) < 3:
    print("\n❌ Error: Missing arguments.")
    print("Usage: python super_audit.py <URL> <MAX_PAGES>")
    print("Example: python super_audit.py https://www.example.com 15\n")
    sys.exit(1)

START_URL = sys.argv[1]
try:
    MAX_PAGES = int(sys.argv[2])
except ValueError:
    print("❌ Error: Max pages must be a number.")
    sys.exit(1)

SCREENSHOT_DIR = "audit_screenshots"
# --------------------------------------

os.makedirs(SCREENSHOT_DIR, exist_ok=True)

target_domain = ""
visited_urls = set()
urls_to_visit = []
discovered_urls = set() # NEW: Tracks every single internal link we find

# Data structures for our HTML report
scanned_pages = [] 
broken_links = []  
js_errors = []     
console_errors = []  
network_errors = []  

async def audit_page(playwright, url):
    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context(viewport={"width": 1280, "height": 720}, ignore_https_errors=True)
    page = await context.new_page()

    # --- DEVTOOLS EVENT LISTENERS ---
    page.on("pageerror", lambda exc: js_errors.append({"source": url, "error": exc.message}))
    page.on("console", lambda msg: console_errors.append({"source": url, "error": msg.text}) if msg.type == "error" else None)
    page.on("requestfailed", lambda req: network_errors.append({"source": url, "error": f"Failed to load: {req.url}"}))
    # --------------------------------

    print(f"📸 Auditing & Snapping: {url}")
    try:
        response = await page.goto(url, wait_until="networkidle", timeout=20000)
        status = response.status if response else "Unknown"

        if status >= 400:
            broken_links.append({"source": "Direct Entry", "url": url, "status": status})
            await browser.close()
            return []

        safe_filename = url.replace("https://", "").replace("http://", "").replace("/", "_").replace("?", "_") + ".png"
        screenshot_path = os.path.join(SCREENSHOT_DIR, safe_filename)
        
        await page.screenshot(path=screenshot_path, full_page=True)
        
        scanned_pages.append({
            "url": url,
            "screenshot": screenshot_path,
            "status": status
        })

        content = await page.content()
        soup = BeautifulSoup(content, "html.parser")
        
        found_links = []
        for anchor in soup.find_all("a", href=True):
            href = anchor.get("href")
            if not href or href.startswith(("javascript:", "mailto:", "tel:")):
                continue
                
            full_url = urljoin(url, href)
            full_url = urlparse(full_url)._replace(fragment="").geturl()
            found_links.append(full_url)

        await browser.close()
        return found_links

    except Exception as e:
        print(f"⚠️ Error processing {url}: {str(e)}")
        broken_links.append({"source": "Crawler", "url": url, "status": "Timeout/Error"})
        await browser.close()
        return []

async def main():
    global urls_to_visit, target_domain, discovered_urls
    
    target_domain = urlparse(START_URL).netloc
    urls_to_visit = [START_URL]
    discovered_urls.add(START_URL)
    
    async with async_playwright() as playwright:
        while urls_to_visit and len(visited_urls) < MAX_PAGES:
            current_url = urls_to_visit.pop(0)
            if current_url in visited_urls:
                continue
            
            visited_urls.add(current_url)
            
            discovered_links = await audit_page(playwright, current_url)
            
            for link in discovered_links:
                link_domain = urlparse(link).netloc
                if link_domain == target_domain:
                    # We found an internal link! Add it to our total discovered list
                    discovered_urls.add(link)
                    # If we haven't visited it or queued it yet, put it in the queue
                    if link not in visited_urls and link not in urls_to_visit:
                        urls_to_visit.append(link)

    generate_html_report(target_domain)

def generate_html_report(domain):
    html_template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>{{ domain }} - Web Quality Audit</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: #f4f6f9; color: #333; margin: 40px; }
            h1, h2 { color: #1e293b; margin-top: 40px;}
            .summary-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 30px; }
            .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
            .stat { padding: 20px; text-align: center; border-radius: 8px; font-weight: bold; color: white; }
            .stat.discovered { background-color: #0ea5e9; }
            .stat.scanned { background-color: #3b82f6; }
            .stat.broken { background-color: #ef4444; }
            .stat.js { background-color: #f59e0b; }
            .stat.network { background-color: #8b5cf6; }
            table { width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 30px; }
            th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #e2e8f0; word-break: break-all; }
            th { background-color: #1e293b; color: white; }
            .gallery { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 20px; }
            .screenshot-card { background: white; padding: 10px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); text-align: center; }
            .screenshot-card img { max-width: 100%; height: auto; border: 1px solid #cbd5e1; border-radius: 4px; max-height: 300px; object-fit: cover; }
            .screenshot-card p { font-size: 12px; word-break: break-all; margin-top: 8px; color: #64748b; }
        </style>
    </head>
    <body>
        <h1>🌐 Quality Audit Report: {{ domain }}</h1>
        <p>Generated automatically via custom Playwright framework. Includes DevTools network & console monitoring.</p>

        <div class="grid">
            <div class="stat discovered">Total Links Discovered<br><span style="font-size: 24px;">{{ total_discovered }}</span></div>
            <div class="stat scanned">Pages Scanned<br><span style="font-size: 24px;">{{ scanned_count }}</span></div>
            <div class="stat broken">Broken Links Found<br><span style="font-size: 24px;">{{ broken_count }}</span></div>
            <div class="stat js">Runtime JS Crashes<br><span style="font-size: 24px;">{{ js_count }}</span></div>
            <div class="stat js">DevTools Console Errors<br><span style="font-size: 24px;">{{ console_count }}</span></div>
            <div class="stat network">Network Failures<br><span style="font-size: 24px;">{{ network_count }}</span></div>
        </div>

        <h2>🚨 Broken Links & Dead Ends</h2>
        <table>
            <tr><th>Found On Page</th><th>Target URL</th><th>HTTP Status</th></tr>
            {% for link in broken_links %}
            <tr><td>{{ link.source }}</td><td><a href="{{ link.url }}" target="_blank">{{ link.url }}</a></td><td style="color:#ef4444; font-weight:bold;">{{ link.status }}</td></tr>
            {% else %}
            <tr><td colspan="3" style="color: #10b981;">🎉 No broken links found! Excellent routing integrity.</td></tr>
            {% endfor %}
        </table>

        <h2>⚠️ Uncaught JavaScript Exceptions (Crashes)</h2>
        <table>
            <tr><th>Source URL</th><th>Exception Text</th></tr>
            {% for err in js_errors %}
            <tr><td>{{ err.source }}</td><td style="color:#f59e0b; font-family: monospace;">{{ err.error }}</td></tr>
            {% else %}
            <tr><td colspan="2" style="color: #10b981;">🎉 Zero runtime script crashes encountered.</td></tr>
            {% endfor %}
        </table>

        <h2>🛑 DevTools Console Errors</h2>
        <table>
            <tr><th>Source URL</th><th>Console Error Message</th></tr>
            {% for err in console_errors %}
            <tr><td>{{ err.source }}</td><td style="color:#f59e0b; font-family: monospace;">{{ err.error }}</td></tr>
            {% else %}
            <tr><td colspan="2" style="color: #10b981;">🎉 Clean console output. No explicit errors logged.</td></tr>
            {% endfor %}
        </table>

        <h2>🔌 Failed Network Requests (Images, Scripts, APIs)</h2>
        <table>
            <tr><th>Source URL</th><th>Failed Resource</th></tr>
            {% for err in network_errors %}
            <tr><td>{{ err.source }}</td><td style="color:#8b5cf6; font-family: monospace;">{{ err.error }}</td></tr>
            {% else %}
            <tr><td colspan="2" style="color: #10b981;">🎉 All network resources loaded successfully.</td></tr>
            {% endfor %}
        </table>

        <h2>📸 UI Visual Verification Gallery</h2>
        <div class="gallery">
            {% for page in scanned_pages %}
            <div class="screenshot-card">
                <img src="{{ page.screenshot }}" alt="Screenshot">
                <p><strong>Status {{ page.status }}</strong><br>{{ page.url }}</p>
            </div>
            {% endfor %}
        </div>
    </body>
    </html>
    """
    
    template = Template(html_template)
    rendered_html = template.render(
        domain=domain,
        total_discovered=len(discovered_urls),
        scanned_count=len(scanned_pages),
        broken_count=len(broken_links),
        js_count=len(js_errors),
        console_count=len(console_errors),
        network_count=len(network_errors),
        broken_links=broken_links,
        js_errors=js_errors,
        console_errors=console_errors,
        network_errors=network_errors,
        scanned_pages=scanned_pages
    )
    
    safe_domain_name = domain.replace(".", "_")
    report_filename = f"{safe_domain_name}_audit_report.html"
    
    with open(report_filename, "w", encoding="utf-8") as f:
        f.write(rendered_html)
    
    print(f"\n✨ Success! Open '{report_filename}' in your browser to view your masterpiece.")

if __name__ == "__main__":
    asyncio.run(main())