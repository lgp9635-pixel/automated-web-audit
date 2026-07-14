import sys
import requests
import json
import time

def run_api_audit(endpoint):
    """
    Pings an API endpoint, checks the status code, latency, and JSON validity,
    and generates an HTML report.
    """
    report_file = "api_audit_report.html"
    
    try:
        start_time = time.time()
        # Ping the API with a 10-second timeout
        response = requests.get(endpoint, timeout=10)
        latency = round((time.time() - start_time) * 1000, 2)
        status = response.status_code
        
        # Determine if the response is successful
        status_icon = "✅" if status < 400 else "❌"
        
        # Check if the response is valid JSON
        try:
            data = response.json()
            is_json = True
            # Pretty-print the first 500 characters of the JSON response
            preview = json.dumps(data, indent=2)[:500]
        except ValueError:
            is_json = False
            # If not JSON, just show the raw text
            preview = response.text[:500]

        # Generate the HTML Report
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>API Audit Report</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; padding: 2rem; max-width: 800px; margin: 0 auto; color: #333; }}
                h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
                .metric {{ background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 15px; border-left: 5px solid #3498db; }}
                pre {{ background: #2c3e50; color: #ecf0f1; padding: 15px; border-radius: 8px; overflow-x: auto; }}
            </style>
        </head>
        <body>
            <h1>⚙️ API Endpoint Audit Report</h1>
            <div class="metric">
                <strong>Target Endpoint:</strong> <a href="{endpoint}" target="_blank">{endpoint}</a>
            </div>
            <div class="metric">
                <strong>Status Code:</strong> {status} {status_icon}
            </div>
            <div class="metric">
                <strong>Response Latency:</strong> {latency} ms
            </div>
            <div class="metric">
                <strong>Valid JSON Response:</strong> {'✅ Yes' if is_json else '⚠️ No (or Empty)'}
            </div>
            
            <h2>Response Payload (Preview)</h2>
            <p><i>Showing up to the first 500 characters of the API response:</i></p>
            <pre><code>{preview}{'...' if len(preview) == 500 else ''}</code></pre>
        </body>
        </html>
        """
        
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(html_content)
            
    except Exception as e:
        # Fallback if the endpoint is completely unreachable
        html_content = f"""
        <!DOCTYPE html>
        <html><head><title>API Audit Failed</title></head>
        <body style="font-family: Arial, sans-serif; padding: 2rem;">
            <h1 style="color: red;">❌ API Audit Failed</h1>
            <p><strong>Endpoint:</strong> {endpoint}</p>
            <p><strong>Error:</strong> {str(e)}</p>
            <p>Ensure the URL is a valid, publicly accessible API endpoint.</p>
        </body></html>
        """
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(html_content)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_api_audit(sys.argv[1])
    else:
        print("Error: No API endpoint provided.")