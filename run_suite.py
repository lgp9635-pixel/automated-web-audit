import sys
import subprocess
from load_tester import run_native_load_test
from utils import write_load_test_report  # Added this to generate the HTML!

def run_step(command, step_name):
    """
    Runs a shell command and halts the suite if it fails.
    """
    print(f"\n{'='*60}")
    print(f"🚀 STARTING STEP: {step_name}")
    print(f"{'='*60}")
    
    try:
        # check=True ensures that if a script crashes, the whole suite stops
        subprocess.run(command, check=True)
        print(f"\n✅ COMPLETED: {step_name}")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ ERROR: {step_name} failed with exit code {e.returncode}.")
        print("Stopping the QA suite.")
        sys.exit(1)

if __name__ == "__main__":
    # Ensure the user provides the required arguments
    if len(sys.argv) < 3:
        print("\n❌ Error: Usage: python3 run_suite.py <URL> <MAX_PAGES>")
        sys.exit(1)

    target_url = sys.argv[1]
    max_pages = sys.argv[2]

    print("\n" + "#"*60)
    print(f"  INITIALIZING QA SUITE FOR: {target_url}")
    print("#"*60)

    # --- STEP 1: The Crawler ---
    run_step(["python3", "audit.py", target_url, max_pages], "Crawler & Text Extractor (audit.py)")

    # --- STEP 2: The Grammar Checker ---
    run_step(["python3", "grammar_audit.py"], "Grammar & Spell Check (grammar_audit.py)")

    # --- STEP 3: The Security Audit ---
    run_step(["python3", "security_audit.py", target_url], "Security Headers Audit (security_audit.py)")
    
    # --- STEP 4: The Load Tester ---
    print(f"\n{'='*60}")
    print("🚀 STARTING STEP: Load Testing")
    print(f"{'='*60}")
    
    print("\n--- Load Test Settings ---")
    req_input = input("How many total requests do you want to send? (Press Enter for 1000): ")
    
    # Convert input to integer, defaulting to 1000 if empty
    total_reqs = int(req_input) if req_input.strip().isdigit() else 1000
    
    # Safely calculate concurrency
    concurrency = max(1, min(total_reqs // 10, 100))

    print(f"[*] Running Load Test: {total_reqs} total requests ({concurrency} at a time)...")
    load_metrics = run_native_load_test(target_url, total_requests=total_reqs, concurrent_users=concurrency)
    
    print("[*] Generating Load Test HTML Report...")
    write_load_test_report(load_metrics)
    print(f"\n✅ COMPLETED: Load Testing")

    print(f"\n{'='*60}")
    print("🎉 QA SUITE EXECUTION FULLY COMPLETE!")
    print("Check your browser for the generated HTML reports.")
    print(f"{'='*60}\n")