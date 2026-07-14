import urllib.request
import urllib.error
import time
import concurrent.futures

def fetch_url(url):
    """Hits the URL and returns the response time and status code."""
    start_time = time.time()
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (QA Audit)'})
        with urllib.request.urlopen(req, timeout=10) as response:
            status = response.getcode()
            response.read()
    except urllib.error.HTTPError as e:
        status = e.code
    except Exception:
        status = 500
        
    duration = time.time() - start_time
    return duration, status

def run_native_load_test(url, total_requests=50, concurrent_users=10):
    """Runs the load test."""
    times = []
    statuses = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
        futures = [executor.submit(fetch_url, url) for _ in range(total_requests)]
        
        for future in concurrent.futures.as_completed(futures):
            duration, status = future.result()
            times.append(duration)
            statuses.append(status)
            
    successes = statuses.count(200)
    
    return {
        "url": url,
        "total_requests": total_requests,
        "success_rate_percent": (successes / total_requests) * 100,
        "avg_response_time_sec": round(sum(times) / len(times), 3),
        "max_response_time_sec": round(max(times), 3)
    }