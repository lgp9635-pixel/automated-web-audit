import streamlit as st
import subprocess
import os
import urllib.parse
from load_tester import run_native_load_test
from utils import write_load_test_report

# 1. Page config MUST be the first Streamlit command
st.set_page_config(page_title="QA Web Verifier", layout="wide")

# 2. Caching function to prevent repetitive discovery scans
@st.cache_data
def run_discovery(url):
    """
    Runs the discovery scan and caches the result for this specific URL.
    """
    # Placeholder for your actual discovery logic
    return 42 

st.title("🚀 QA Web Verifier Suite")
st.markdown("Enter a target URL to begin the audit process.")

# --- STEP 1: Discovery ---
target_url = st.text_input("Target URL (e.g., https://example.com)")

# This now runs automatically when you press Enter in the text box
if target_url:
    with st.spinner(f"Crawling {target_url} for discoverable URLs..."):
        url_count = run_discovery(target_url)
        st.success(f"✅ Discovery Complete! Found **{url_count}** discoverable URLs on {target_url}.")

# --- STEP 2: Feature Selection ---
st.write("---")
st.subheader("2. Select Audits to Run")

col1, col2 = st.columns(2)

with col1:
    run_crawler = st.checkbox("🗺️ Site Navigation & Link Audit")
    
    # Conditional input: Only shows if the audit is checked
    if run_crawler:
        st.info("How many URLs do you want to scan?")
        max_pages = st.number_input("Maximum pages to scan", min_value=1, value=10, step=5)
        
    run_grammar = st.checkbox("📝 Grammar & Spell Check")

with col2:
    run_security = st.checkbox("🔒 Security Header Audit")
    
    run_load = st.checkbox("⏱️ Load Testing")
    
    # Conditional input: Only shows if Load Testing is checked
    if run_load:
        st.info("Load Test Configuration")
        total_reqs = st.number_input("Total Requests", min_value=10, value=1000, step=100)
        concurrency = st.number_input("Concurrent Users", min_value=1, value=10, step=5)

# --- STEP 3: Execution ---
st.write("---")
if st.button("3. Run Selected Audits", type="primary"):
    
    if not target_url:
        st.error("🚨 Please enter a Target URL at the top of the page before running audits.")
    elif not any([run_crawler, run_grammar, run_security, run_load]):
        st.warning("Please select at least one audit to run.")
    else:
        domain = urllib.parse.urlparse(target_url).netloc.replace(".", "_")
        
        # Expandable status box for a cleaner UI
        with st.status(f"Initiating audits for **{target_url}**...", expanded=True) as status:
            
            if run_crawler:
                st.write(f"🗺️ Running Site Navigation & Link Audit (Scanning up to {max_pages} pages)...")
                subprocess.run(["python3", "audit.py", target_url, str(max_pages)])
                
            if run_grammar:
                st.write("📝 Running Grammar Check...")
                subprocess.run(["python3", "grammar_audit.py"])
                
            if run_security:
                st.write("🔒 Running Security Audit...")
                subprocess.run(["python3", "security_audit.py", target_url])
                
            if run_load:
                st.write(f"⏱️ Running Load Test ({total_reqs} requests)...")
                load_metrics = run_native_load_test(target_url, total_requests=total_reqs, concurrent_users=concurrency)
                write_load_test_report(load_metrics)
            
            status.update(label="✅ All selected audits complete!", state="complete", expanded=False)

        st.success("🎉 Audits finished! View or download your reports below:")
        
        # Create columns to display download buttons side-by-side
        col_a, col_b = st.columns(2)
        
        with col_a:
            crawler_file = f"{domain}_audit_report.html"
            if run_crawler and os.path.exists(crawler_file):
                with open(crawler_file, "r", encoding="utf-8") as f:
                    st.download_button("📄 Download Navigation Report", f.read(), file_name=crawler_file, mime="text/html")
                    
            if run_grammar and os.path.exists("grammar_audit_report.html"):
                with open("grammar_audit_report.html", "r", encoding="utf-8") as f:
                    st.download_button("📄 Download Grammar Report", f.read(), file_name="grammar_audit_report.html", mime="text/html")
                    
        with col_b:
            if run_security and os.path.exists("security_audit_report.html"):
                with open("security_audit_report.html", "r", encoding="utf-8") as f:
                    st.download_button("📄 Download Security Report", f.read(), file_name="security_audit_report.html", mime="text/html")
                    
            if run_load and os.path.exists("load_audit_report.html"):
                with open("load_audit_report.html", "r", encoding="utf-8") as f:
                    st.download_button("📄 Download Load Report", f.read(), file_name="load_audit_report.html", mime="text/html")