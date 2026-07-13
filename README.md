Playwright Web Quality Auditor

A lightweight, automated web quality auditor built with Python and Playwright. This tool crawls a target website to map internal routing and generates a dynamic HTML dashboard detailing structural, visual, and network-level health.

Designed as a modern QA automation utility, this script goes beyond standard link checking by monitoring background DevTools traffic to catch failing APIs, broken assets, and runtime JavaScript exceptions before users notice them.

✨ Key Features
Automated Crawling: Maps internal site architecture and discovers active links up to a user-defined
page limit.
Structural Verification: Catches broken links and dead ends (404/500 HTTP status codes).
DevTools Network Monitoring: Intercepts the browser network tab to log failed requests (e.g., broken
images, failing API calls, blocked scripts).
Runtime Error Tracking: Logs uncaught JavaScript exceptions and explicit console.error() messages.
Visual Verification: Automatically captures full-page screenshots of every audited page to catch
layout regressions.
Dynamic HTML Reporting: Compiles all findings into a clean, easy-to-read, offline HTML dashboard
(powered by Jinja2).
🛠️ Installation & Setup
Clone the repository:
git clone [https://github.com/lgp9635-pixel/automated-web-auditor.git](https://github.com/lgp9635-pixel/automated-web-auditor.git)
cd automated-web-auditor
