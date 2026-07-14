import requests
import sys
from utils import write_security_report

def analyze_security_headers(url):
    """
    Checks the target URL for essential HTTP security headers and information leakage.
    """
    print(f"🚀 Running Advanced Security Audit on: {url}...")
    
    # 1. Shields Up: Headers that MUST be present for good security
    required_headers = {
        'Strict-Transport-Security': 'Forces secure (HTTPS) connections to the server.',
        'Content-Security-Policy': 'Prevents Cross-Site Scripting (XSS) and data injection.',
        'X-Frame-Options': 'Prevents clickjacking by blocking the site from being framed.',
        'X-Content-Type-Options': 'Prevents MIME-sniffing vulnerabilities.',
        'Referrer-Policy': 'Controls how much routing information is shared with other sites.',
        'Permissions-Policy': 'Restricts which device features (camera, mic, etc.) the site can use.'
    }
    
    # 2. Information Leakage: Headers that SHOULD NOT be present
    leakage_headers = {
        'Server': 'May reveal server type and version, aiding attackers.',
        'X-Powered-By': 'May reveal backend technologies (e.g., PHP, Express).'
    }
    
    results = []
    
    try:
        response = requests.get(url, timeout=10)
        site_headers = response.headers
        
        # Check required headers
        for header, description in required_headers.items():
            is_present = header in site_headers
            results.append({
                'Header': header,
                'Category': 'Protection',
                'Status': '✅ Pass' if is_present else '❌ Missing',
                'Description': description,
                'Value': site_headers.get(header, 'N/A')
            })
            
        # Check for information leakage
        for header, description in leakage_headers.items():
            is_present = header in site_headers
            results.append({
                'Header': header,
                'Category': 'Leakage',
                'Status': '⚠️ Warning (Leaked)' if is_present else '✅ Pass (Hidden)',
                'Description': description,
                'Value': site_headers.get(header, 'N/A')
            })
            
    except Exception as e:
        print(f"⚠️ Security audit failed to reach {url}: {e}")
        
    return results

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ Error: Usage: python3 security_audit.py <URL>")
        sys.exit(1)
        
    target_url = sys.argv[1]
    security_results = analyze_security_headers(target_url)
    write_security_report(target_url, security_results)