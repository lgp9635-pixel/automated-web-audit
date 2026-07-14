# Playwright Web Quality Auditor

A lightweight, automated web quality auditor built with Python and Playwright. This tool crawls a target website to map internal routing and generates a dynamic HTML dashboard detailing structural, visual, and network-level health.

The script goes beyond standard link checking by monitoring background DevTools traffic to catch failing connections before users notice them.

### Features
- **Automated Crawling**: Maps internal site architecture and discovers active links up to a user-defined page limit.
- **Structural Verification**: Catches broken links and dead ends (404/500 HTTP status codes).
- **DevTools Network Monitoring**: Intercepts the browser network tab to log failed requests (e.g., broken images, failing API calls, blocked scripts).
- **Runtime Error Tracking**: Logs uncaught JavaScript exceptions and explicit console.error() messages.
- **Visual Verification**: Automatically captures full-page screenshots of every audited page to catch layout regressions.
- **Dynamic HTML Reporting**: Compiles all findings into a clean, easy-to-read, offline HTML dashboard (powered by Jinja2).
- **Grammar and Misspellings Checker**: Scans page content for grammatical errors and typos.
- **Security Checker**: Identifies common web security vulnerabilities.
- **Load Tester**: Evaluates site performance under simulated traffic.

### Installation
```bash
git clone https://github.com/lgp9635-pixel/automated-web-audit.git
cd automated-web-audit
pip install -r requirements.txt
playwright install chromium
```

### Usage
```bash
python run_suite.py --url https://example.com --limit 10
```
