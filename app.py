import streamlit as st
import subprocess
import os
import urllib.parse
import sys
from load_tester import run_native_load_test
from utils import write_load_test_report

# --- NEW: Force install Playwright browsers on the cloud ---
os.system(f"{sys.executable} -m playwright install chromium")

# 1. Page config MUST be the first Streamlit command
st.set_page_config(page_title="QA Web Verifier", layout="wide")

# --- THE FIX: A callback function to wipe the memory before the page reloads ---
def reset_app():
    # Delete all the stored widget keys so they revert to empty/unchecked
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    # Re-initialize the essential switches
    st.session_state.reports_ready = False
    st.session_state.domain = ""

# --- Initialize Session State Memory ---
if "reports_ready" not in st.session_state:
    st.session_state.reports_ready = False
if "domain" not in st.session_state:
    st.session_state.domain = ""

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
target_url = st.text_input("Target URL (e.g., https://example.com)", key="target_url_input")

if target_url:
    with st.spinner(f"Crawling {target_url} for discoverable URLs..."):
        url_count = run_discovery(target_url)
        st.success(f"✅ Discovery Complete! Found **{url_count}** discoverable URLs on {target_url}.")

# --- STEP 2: Feature Selection ---
st.write("---")
st.subheader("2. Select Audits to Run")

col1, col2 = st.columns(2)

with col1:
    run_crawler = st.checkbox("🗺️ Site Navigation & Link Audit", key="run_crawler_chk")
    
    if run_crawler:
        st.info("How many URLs do you want to scan?")
        max_pages = st.number_input("Maximum pages to scan", min_value=1, value=10, step=5, key="max_pages_num")
        
    run_grammar = st.checkbox("📝 Grammar & Spell Check", key="run_grammar_chk")

with col2:
    run_security = st.checkbox("🔒 Security Header Audit", key="run_security_chk")
    
    run_load = st.checkbox("⏱️ Load Testing", key="run_load_chk")
    
    if run_load:
        st.info("Load Test Configuration")
        total_reqs = st.number_input("Total Requests", min_value=10, value=1000, step=100, key="total_reqs_num")
        concurrency = st.number_input("Concurrent Users", min_value=1, value=10, step=5, key="concurrency_num")

# --- STEP 3: Execution ---
st.write("---")

btn_col1, btn_col2 = st.columns([2, 8])

with btn_col2:
    # Trigger the callback function when clicked, completely avoiding the API error
    st.button("🔄 Reset App", on_click=reset_app)

with btn_col1:
    run_pressed = st.button("3. Run Selected Audits", type="primary")

if run_pressed:
    
    if not target_url:
        st.error("🚨 Please enter a Target URL at the top of the page before running audits.")
    elif not any([run_crawler, run_grammar, run_security, run_load]):
        st.warning("Please select at least one audit to run.")
    else:
        domain = urllib.parse.urlparse(target_url).netloc.replace(".", "_")
        
        with st.status(f"Initiating audits for **{target_url}**...", expanded=True) as status:
            
            if run_crawler:
                st.write(f"🗺️ Running Site Navigation & Link Audit (Scanning up to {max_pages} pages)...")
                subprocess.run([sys.executable, "audit.py", target_url, str(max_pages)])
                
            if run_grammar:
                st.write("📝 Running Grammar Check...")
                subprocess.run([sys.executable, "grammar_audit.py"])
                
            if run_security:
                st.write("🔒 Running Security Audit...")
                subprocess.run([sys.executable, "security_audit.py", target_url])
                
            if run_load:
                st.write(f"⏱️ Running Load Test ({total_reqs} requests)...")
                load_metrics = run_native_load_test(target_url, total_requests=total_reqs, concurrent_users=concurrency)
                write_load_test_report(load_metrics)
            
            status.update(label="✅ All selected audits complete!", state="complete", expanded=False)
            
        st.session_state.domain = domain
        st.session_state.reports_ready = True

# --- STEP 4: Display Reports ---
if st.session_state.reports_ready:
    st.success("🎉 Audits finished! View or download your reports below:")
    
    col_a, col_b = st.columns(2)
    domain = st.session_state.domain
    
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
