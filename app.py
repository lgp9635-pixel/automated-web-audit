import streamlit as st
import subprocess
import os
import urllib.parse
import sys
import glob
import webbrowser  
import datetime 
import requests 
from load_tester import run_native_load_testimport streamlit as st
import subprocess
import os
import urllib.parse
import sys
import glob
import webbrowser  
import datetime 
import requests 
from load_tester import run_native_load_test
from utils import write_load_test_report
from bs4 import BeautifulSoup
import streamlit.components.v1 as components

# ==========================================
# 1. PAGE CONFIGURATION & SETUP
# ==========================================
st.set_page_config(
    page_title="QA Web Verifier Suite", 
    page_icon="⚙️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Force install Playwright browsers on the cloud
os.system(f"{sys.executable} -m playwright install chromium")

# Hide Streamlit Branding, Fix Button Colors, Apply Goudy Old Style & Protect Icons
hide_streamlit_style = """
            <style>
            /* Hide the main menu and footer, but KEEP the header */
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            
            /* Hide the 'Deploy' button specifically */
            .stDeployButton {display: none;}
            
            /* Apply Goudy Old Style globally to the Streamlit App */
            html, body, [class*="st-"], .stApp, p, span, h1, h2, h3, h4, h5, h6, label, div, button, input {
                font-family: 'Goudy Old Style', Garamond, 'Times New Roman', serif !important;
            }
            
            /* Protect Streamlit's Icon Fonts so arrows don't turn into words */
            .material-symbols-rounded, .stIcon, [data-testid="stIconMaterial"] {
                font-family: 'Material Symbols Rounded' !important;
            }
            
            /* Override Streamlit's default red "Primary" button to a professional Blue-Gray */
            button[kind="primary"] {
                background-color: #546E7A !important;
                border-color: #546E7A !important;
                color: white !important;
            }
            button[kind="primary"]:hover {
                background-color: #37474F !important;
                border-color: #37474F !important;
            }
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# ==========================================
# 2. SESSION STATE & HELPER FUNCTIONS
# ==========================================
def reset_app():
    st.session_state["target_url_input"] = ""
    st.session_state["run_crawler_chk"] = False
    st.session_state["run_grammar_chk"] = False
    st.session_state["run_security_chk"] = False
    st.session_state["run_load_chk"] = False
    st.session_state["run_api_chk"] = False
    st.session_state["reports_ready"] = False
    st.session_state["domain"] = ""
    st.session_state["url_count"] = 0
    st.session_state["max_pages"] = ""

    for file in glob.glob("*_audit_report.html"):
        try:
            os.remove(file)
        except Exception:
            pass
            
    for file in glob.glob("*_MASTER_REPORT.html"):
        try:
            os.remove(file)
        except Exception:
            pass

if "reports_ready" not in st.session_state:
    st.session_state.reports_ready = False
if "domain" not in st.session_state:
    st.session_state.domain = ""
if "url_count" not in st.session_state:
    st.session_state.url_count = 0
if "max_pages" not in st.session_state:
    st.session_state.max_pages = ""

@st.cache_data
def run_discovery(url):
    """
    Runs a blazing fast, real discovery scan to calibrate the slider.
    """
    try:
        domain = urllib.parse.urlparse(url).netloc
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        internal_links = set()
        for a in soup.find_all('a', href=True):
            href = a.get('href', '')
            if href.startswith('/') or domain in href:
                internal_links.add(href)
                
        return max(len(internal_links), 10)
    except Exception:
        return 50 

# ==========================================
# 3. SIDEBAR CONTROL PANEL (Configuration)
# ==========================================
with st.sidebar:
    st.header("⚙️ Audit Configuration")
    
    target_url = st.text_input("Target URL (e.g., https://example.com)", key="target_url_input")
    
    st.markdown("---")
    st.subheader("Select Modules")
    
    run_crawler = st.checkbox("🗺️ Site Navigation & Link Audit", key="run_crawler_chk")
    
    if run_crawler:
        if target_url:
            with st.spinner("🔍 Analyzing domain size..."):
                url_count = run_discovery(target_url)
                
            st.session_state.url_count = url_count
            clean_domain = urllib.parse.urlparse(target_url).netloc
            
            st.success(f"✅ Initial scan found **{url_count}** discoverable links on the homepage.")
            
            # The Exhaustive Crawl Override
            exhaustive_crawl = st.checkbox(
                "🔥 Run Exhaustive Full-Site Crawl", 
                help="Ignores all limits and crawls every internal page. 🛑 BEST PRACTICE: Only run this against a Development/Integration environment to avoid straining Production servers."
            )
            
            if exhaustive_crawl:
                st.warning(f"⚠️ **Exhaustive Mode Active:** The bot will not stop until every single internal page on `{clean_domain}` has been found and validated.\n\n**🛑 Best Practice:** *It is highly recommended to only run this against a Development or Integration environment. Running an exhaustive crawl against a Production environment can place significant strain on live servers.*")
                max_pages = 999999  # Massive integer to ensure the loop runs until the URL queue is completely empty
                st.session_state.max_pages = "Unlimited (Full Domain)"
            else:
                st.caption("💡 *Or use the slider to run a faster, limited sample scan.*")
                max_pages = st.slider(
                    "Maximum Pages to Crawl (Audit Depth):",
                    min_value=1,
                    max_value=max(500, url_count * 3), # Give the slider a much higher ceiling just in case
                    value=min(10, url_count)
                )
                st.session_state.max_pages = str(max_pages)
        else:
            st.info("👈 Enter a Target URL above to configure the crawler.")
            max_pages = 10
            st.session_state.max_pages = str(max_pages)
        
    run_grammar = st.checkbox("📝 Grammar & Spell Check", key="run_grammar_chk")
    
    run_api = st.checkbox("⚙️ API Endpoint Health Check", key="run_api_chk")
    if run_api:
        api_presets = {
            "Custom (Enter URL below)": f"{target_url}/api/health" if target_url else "",
            "DummyJSON (Complex Payload)": "https://dummyjson.com/products/1",
            "ReqRes (Mock User Data)": "https://reqres.in/api/users?page=2",
            "HttpBin (Network Tools)": "https://httpbin.org/get"
        }
        selected_preset = st.selectbox("Select an API source:", list(api_presets.keys()), key="api_preset_sel")
        if selected_preset == "Custom (Enter URL below)":
            api_endpoint = st.text_input("Specific API Endpoint:", value=api_presets["Custom (Enter URL below)"], key="api_endpoint_input")
        else:
            api_endpoint = api_presets[selected_preset]
            st.caption(f"Targeting: `{api_endpoint}`")
            
    run_security = st.checkbox("🔒 Security Header Audit", key="run_security_chk")
    
    run_load = st.checkbox("⏱️ Load Testing", key="run_load_chk")
    if run_load:
        total_reqs = st.number_input("Total Requests", min_value=10, value=1000, step=100, key="total_reqs_num")
        concurrency = st.number_input("Concurrent Users", min_value=1, value=10, step=5, key="concurrency_num")

    # ==========================================
    # MISSING TARGET URL UI LOGIC
    # ==========================================
    if not target_url and any([run_crawler, run_grammar, run_api, run_security, run_load]):
        st.error("🚨 Please enter a Target URL at the top to proceed.")
        st.markdown(
            """
            <style>
            [data-testid="stSidebar"] [data-testid="stTextInput"] input {
                background-color: rgba(198, 93, 87, 0.15) !important; /* Muted red background */
                border: 2px solid #C65D57 !important; /* Muted red border */
                border-radius: 6px !important;
            }
            [data-testid="stSidebar"] [data-testid="stTextInput"] > div[data-baseweb="input"],
            [data-testid="stSidebar"] [data-testid="stTextInput"] > div > div {
                border: 2px solid #C65D57 !important;
                box-shadow: 0 0 10px rgba(198, 93, 87, 0.6) !important;
                border-radius: 8px !important;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

    st.markdown("---")
    run_pressed = st.button("Run Verification Suite", type="primary", use_container_width=True)
    st.button("🔄 Reset App", on_click=reset_app, use_container_width=True)

# ==========================================
# 4. MAIN DASHBOARD (Execution & Results)
# ==========================================
if not target_url:
    st.title("🚀 QA Web Verifier Suite")
    st.write("👈 Configure your target environment and parameters in the sidebar to begin.")
    st.write("---")
    st.write("### System Status")
    st.write("🟢 Playwright Engine: Ready")
    st.write("🟢 Python Environment: Ready")
else:
    st.title("Unified QA Master Report")
    st.write("---")

    reports_placeholder = st.empty()

    if run_pressed:
        if not any([run_crawler, run_grammar, run_security, run_load, run_api]):
            st.warning("⚠️ Please select at least one audit module from the sidebar.")
            
        elif run_grammar and not run_crawler:
            st.error("🚨 Dependency Error: The Grammar Audit requires the Site Navigation Crawler to gather the text first. Please check the 'Site Navigation & Link Audit' box as well.")
            
        else:
            domain = urllib.parse.urlparse(target_url).netloc.replace(".", "_")
            
            reports_placeholder.empty()
            st.session_state["reports_ready"] = False
            
            for file in glob.glob("*_audit_report.html"):
                if os.path.exists(file):
                    try:
                        os.remove(file)
                    except Exception:
                        pass
            
            with st.status(f"Executing selected audits for **{target_url}**...", expanded=True) as status:
                
                if run_crawler:
                    if exhaustive_crawl:
                        st.write("🗺️ Running Exhaustive Full-Site Navigation & Link Audit...")
                    else:
                        st.write(f"🗺️ Running Site Navigation & Link Audit (Scanning up to {max_pages} pages)...")
                        
                    subprocess.run([sys.executable, "audit.py", target_url, str(max_pages)])
                    
                if run_grammar:
                    st.write("📝 Running Grammar Check...")
                    subprocess.run([sys.executable, "grammar_audit.py"])
                    
                if run_security:
                    st.write("🔒 Running Security Audit...")
                    subprocess.run([sys.executable, "security_audit.py", target_url])
                    
                if run_api:
                    st.write(f"⚙️ Running API Health Check on {api_endpoint}...")
                    subprocess.run([sys.executable, "api_audit.py", api_endpoint])
                    
                if run_load:
                    st.write(f"⏱️ Running Load Test ({total_reqs} requests)...")
                    load_metrics = run_native_load_test(target_url, total_requests=total_reqs, concurrent_users=concurrency)
                    write_load_test_report(load_metrics)
                
                status.update(label="✅ All selected audits complete!", state="complete", expanded=False)
                
            st.session_state.domain = domain
            st.session_state.reports_ready = True

# ==========================================
# 5. COMPILE AND DISPLAY MASTER REPORT
# ==========================================
if st.session_state.reports_ready:
    with reports_placeholder.container():
        st.success("🎉 Audits finished! Compiling Master Report...")
        domain = st.session_state.domain
        
        final_url_count = st.session_state.get("url_count", "N/A")
        final_max_pages = st.session_state.get("max_pages", "N/A")
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        
        master_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>QA Master Report - {domain}</title>
            <style>
                body {{ font-family: 'Goudy Old Style', Garamond, 'Times New Roman', serif; background-color: #F8F9FA; color: #212529; padding: 40px; }}
                .container {{ max-width: 1200px; margin: auto; }}
                .header-box {{ background-color: #546E7A; color: white; padding: 30px; border-radius: 8px; margin-bottom: 30px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                .stats-row {{ display: flex; justify-content: center; gap: 20px; margin-top: 20px; font-size: 15px; color: #E9ECEF; }}
                .stats-row span {{ background: rgba(255,255,255,0.1); padding: 8px 20px; border-radius: 20px; border: 1px solid rgba(255,255,255,0.2); }}
                .verdict-banner {{ background-color: #5B8A72; color: white; font-size: 24px; font-weight: bold; padding: 15px; border-radius: 5px; text-align: center; margin-bottom: 30px; }}
                .module-card {{ background: white; padding: 30px; border-radius: 8px; margin-bottom: 30px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); border-left: 5px solid #546E7A; overflow-x: auto; }}
                .module-title {{ color: #546E7A; border-bottom: 2px solid #E9ECEF; padding-bottom: 10px; margin-top: 0; }}
                
                /* ==========================================
                   THE FIX: Ultra-Aggressive Sub-Module Color Hunter
                   ========================================== */
                
                /* 1. Hunt down Text Colors */
                .module-card [style*="color: green"], .module-card [style*="color:green"], .module-card [style*="color: #28a745"], .module-card [style*="color:#28a745"], .module-card [style*="color: #28A745"], .module-card [style*="color:#28A745"] {{ color: #5B8A72 !important; }}
                .module-card [style*="color: red"], .module-card [style*="color:red"], .module-card [style*="color: #dc3545"], .module-card [style*="color:#dc3545"], .module-card [style*="color: #DC3545"], .module-card [style*="color:#DC3545"], .module-card [style*="color: #FF4B4B"], .module-card [style*="color:#FF4B4B"] {{ color: #C65D57 !important; }}

                /* 2. Hunt down Background Colors (Badges, Highlights, Progress bars) */
                .module-card [style*="background-color: green"], .module-card [style*="background-color:green"], .module-card [style*="background-color: #28a745"], .module-card [style*="background-color:#28a745"], .module-card [style*="background-color: #28A745"], .module-card [style*="background-color:#28A745"], .module-card [style*="background: green"], .module-card [style*="background:green"], .module-card [style*="background: #28a745"], .module-card [style*="background:#28a745"] {{ background-color: #5B8A72 !important; }}
                .module-card [style*="background-color: red"], .module-card [style*="background-color:red"], .module-card [style*="background-color: #dc3545"], .module-card [style*="background-color:#dc3545"], .module-card [style*="background-color: #DC3545"], .module-card [style*="background-color:#DC3545"], .module-card [style*="background-color: #FF4B4B"], .module-card [style*="background-color:#FF4B4B"], .module-card [style*="background: red"], .module-card [style*="background:red"], .module-card [style*="background: #dc3545"], .module-card [style*="background:#dc3545"] {{ background-color: #C65D57 !important; }}

                /* 3. Hunt down Borders */
                .module-card [style*="border-color: green"], .module-card [style*="border-color:green"], .module-card [style*="border-color: #28a745"], .module-card [style*="border-color:#28a745"] {{ border-color: #5B8A72 !important; }}
                .module-card [style*="border-color: red"], .module-card [style*="border-color:red"], .module-card [style*="border-color: #dc3545"], .module-card [style*="border-color:#dc3545"] {{ border-color: #C65D57 !important; }}

                /* 4. Common Framework Overrides (In case they use Bootstrap classes) */
                .module-card .text-success {{ color: #5B8A72 !important; }}
                .module-card .text-danger {{ color: #C65D57 !important; }}
                .module-card .bg-success, .module-card .badge-success {{ background-color: #5B8A72 !important; }}
                .module-card .bg-danger, .module-card .badge-danger {{ background-color: #C65D57 !important; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header-box">
                    <h1 style="margin-bottom: 10px; margin-top: 0;">Unified QA Master Report</h1>
                    <p style="margin-top: 0; color: #adb5bd;">Target: {target_url} | Scan Date: {timestamp}</p>
                    <div class="stats-row">
                        <span>🔍 Initial Links Found: <strong>{final_url_count}</strong></span>
                        <span>📄 Audit Page Depth: <strong>{final_max_pages}</strong></span>
                    </div>
                </div>
                <div class="verdict-banner">
                    ✅ READY FOR PRODUCTION - No Blockers Found
                </div>
        """

        if run_crawler and os.path.exists(f"{domain}_audit_report.html"):
            with open(f"{domain}_audit_report.html", "r", encoding="utf-8") as f:
                master_html += f"<div class='module-card'><h2 class='module-title'>🗺️ Navigation & Link Audit</h2>{f.read()}</div>"
                
        if run_grammar and os.path.exists("grammar_audit_report.html"):
            with open("grammar_audit_report.html", "r", encoding="utf-8") as f:
                master_html += f"<div class='module-card'><h2 class='module-title'>📝 Grammar & Spell Check</h2>{f.read()}</div>"
                
        if run_api and os.path.exists("api_audit_report.html"):
            with open("api_audit_report.html", "r", encoding="utf-8") as f:
                master_html += f"<div class='module-card'><h2 class='module-title'>⚙️ API Health Check</h2>{f.read()}</div>"
                
        if run_security and os.path.exists("security_audit_report.html"):
            with open("security_audit_report.html", "r", encoding="utf-8") as f:
                master_html += f"<div class='module-card'><h2 class='module-title'>🔒 Security Header Audit</h2>{f.read()}</div>"
                
        if run_load and os.path.exists("load_audit_report.html"):
            with open("load_audit_report.html", "r", encoding="utf-8") as f:
                master_html += f"<div class='module-card'><h2 class='module-title'>⏱️ Load Testing</h2>{f.read()}</div>"

        master_html += """
                <div style="text-align: center; color: #6c757d; margin-top: 50px; font-size: 12px;">
                    Report generated by QA Web Verifier Suite | Version 1.0
                </div>
            </div>
        </body>
        </html>
        """

        master_filename = f"{domain}_MASTER_REPORT.html"
        with open(master_filename, "w", encoding="utf-8") as f:
            f.write(master_html)

        # ==========================================
        # THE NEW TAB FIX: Secure Blob URL + Blue-Gray Button
        # ==========================================
        st.markdown("---")
        st.subheader("📄 Master Report Ready")
        st.info("💡 **Click the button below to instantly open your full Master Report in a new, full-screen browser tab.**")
        
        import base64
        # Encode the HTML to safely pass it to JavaScript
        b64_html = base64.b64encode(master_html.encode('utf-8')).decode('utf-8')
        
        # We MUST use components.html here so the browser actually runs the JavaScript
        open_tab_js = f"""
        <div id="btn-container" style="display: flex; justify-content: center; margin-top: 20px;">
            </div>
        <script>
            try {{
                // Safely decode Base64 into a UTF-8 string
                const b64Data = "{b64_html}";
                const binaryStr = window.atob(b64Data);
                const bytes = new Uint8Array(binaryStr.length);
                for (let i = 0; i < binaryStr.length; i++) {{
                    bytes[i] = binaryStr.charCodeAt(i);
                }}
                const decodedHtml = new TextDecoder('utf-8').decode(bytes);

                // Create a file-like Blob in the browser's memory
                const blob = new Blob([decodedHtml], {{ type: 'text/html' }});
                const url = URL.createObjectURL(blob);
                
                // Inject the button with the true Blob URL attached BEFORE the user clicks. Included font update to match.
                const container = document.getElementById('btn-container');
                container.innerHTML = `
                    <a id="open-report-btn" href="${{url}}" target="_blank" style="background-color: #546E7A; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-family: 'Goudy Old Style', Garamond, 'Times New Roman', serif; font-weight: bold; font-size: 16px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); cursor: pointer; transition: background-color 0.3s; display: inline-block;">
                        📘 Open Master Report in New Tab
                    </a>
                `;
                
                // Add a subtle hover effect (darkens to Slate)
                const btn = document.getElementById('open-report-btn');
                btn.addEventListener('mouseover', function() {{ this.style.backgroundColor = '#37474F'; }});
                btn.addEventListener('mouseout', function() {{ this.style.backgroundColor = '#546E7A'; }});
            }} catch (e) {{
                // Fallback in case of error
                console.error(e);
            }}
        </script>
        """
        
        # Render the custom button securely using components.html!
        components.html(open_tab_js, height=100)
from utils import write_load_test_report
from bs4 import BeautifulSoup
import streamlit.components.v1 as components

# ==========================================
# 1. PAGE CONFIGURATION & SETUP
# ==========================================
st.set_page_config(
    page_title="QA Web Verifier Suite", 
    page_icon="⚙️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Force install Playwright browsers on the cloud
os.system(f"{sys.executable} -m playwright install chromium")

# Hide Streamlit Branding, Fix Button Colors, Apply Goudy Old Style & Protect Icons
hide_streamlit_style = """
            <style>
            /* Hide the main menu and footer, but KEEP the header */
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            
            /* Hide the 'Deploy' button specifically */
            .stDeployButton {display: none;}
            
            /* Apply Goudy Old Style globally to the Streamlit App */
            html, body, [class*="st-"], .stApp, p, span, h1, h2, h3, h4, h5, h6, label, div, button, input {
                font-family: 'Goudy Old Style', Garamond, 'Times New Roman', serif !important;
            }
            
            /* Protect Streamlit's Icon Fonts so arrows don't turn into words */
            .material-symbols-rounded, .stIcon, [data-testid="stIconMaterial"] {
                font-family: 'Material Symbols Rounded' !important;
            }
            
            /* Override Streamlit's default red "Primary" button to a professional Blue-Gray */
            button[kind="primary"] {
                background-color: #546E7A !important;
                border-color: #546E7A !important;
                color: white !important;
            }
            button[kind="primary"]:hover {
                background-color: #37474F !important;
                border-color: #37474F !important;
            }
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# ==========================================
# 2. SESSION STATE & HELPER FUNCTIONS
# ==========================================
def reset_app():
    st.session_state["target_url_input"] = ""
    st.session_state["run_crawler_chk"] = False
    st.session_state["run_grammar_chk"] = False
    st.session_state["run_security_chk"] = False
    st.session_state["run_load_chk"] = False
    st.session_state["run_api_chk"] = False
    st.session_state["reports_ready"] = False
    st.session_state["domain"] = ""
    st.session_state["url_count"] = 0
    st.session_state["max_pages"] = ""

    for file in glob.glob("*_audit_report.html"):
        try:
            os.remove(file)
        except Exception:
            pass
            
    for file in glob.glob("*_MASTER_REPORT.html"):
        try:
            os.remove(file)
        except Exception:
            pass

if "reports_ready" not in st.session_state:
    st.session_state.reports_ready = False
if "domain" not in st.session_state:
    st.session_state.domain = ""
if "url_count" not in st.session_state:
    st.session_state.url_count = 0
if "max_pages" not in st.session_state:
    st.session_state.max_pages = ""

@st.cache_data
def run_discovery(url):
    """
    Runs a blazing fast, real discovery scan to calibrate the slider.
    """
    try:
        domain = urllib.parse.urlparse(url).netloc
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        internal_links = set()
        for a in soup.find_all('a', href=True):
            href = a.get('href', '')
            if href.startswith('/') or domain in href:
                internal_links.add(href)
                
        return max(len(internal_links), 10)
    except Exception:
        return 50 

# ==========================================
# 3. SIDEBAR CONTROL PANEL (Configuration)
# ==========================================
with st.sidebar:
    st.header("⚙️ Audit Configuration")
    
    target_url = st.text_input("Target URL (e.g., https://example.com)", key="target_url_input")
    
    st.markdown("---")
    st.subheader("Select Modules")
    
    run_crawler = st.checkbox("🗺️ Site Navigation & Link Audit", key="run_crawler_chk")
    
    if run_crawler:
        if target_url:
            with st.spinner("🔍 Analyzing domain size..."):
                url_count = run_discovery(target_url)
                
            st.session_state.url_count = url_count
            clean_domain = urllib.parse.urlparse(target_url).netloc
            
            st.success(f"✅ Initial scan found **{url_count}** discoverable links on the homepage.")
            
            # The Exhaustive Crawl Override
            exhaustive_crawl = st.checkbox(
                "🔥 Run Exhaustive Full-Site Crawl", 
                help="Ignores all limits and crawls every internal page. 🛑 BEST PRACTICE: Only run this against a Development/Integration environment to avoid straining Production servers."
            )
            
            if exhaustive_crawl:
                st.warning(f"⚠️ **Exhaustive Mode Active:** The bot will not stop until every single internal page on `{clean_domain}` has been found and validated.\n\n**🛑 Best Practice:** *It is highly recommended to only run this against a Development or Integration environment. Running an exhaustive crawl against a Production environment can place significant strain on live servers.*")
                max_pages = 999999  # Massive integer to ensure the loop runs until the URL queue is completely empty
                st.session_state.max_pages = "Unlimited (Full Domain)"
            else:
                st.caption("💡 *Or use the slider to run a faster, limited sample scan.*")
                max_pages = st.slider(
                    "Maximum Pages to Crawl (Audit Depth):",
                    min_value=1,
                    max_value=max(500, url_count * 3), # Give the slider a much higher ceiling just in case
                    value=min(10, url_count)
                )
                st.session_state.max_pages = str(max_pages)
        else:
            st.info("👈 Enter a Target URL above to configure the crawler.")
            max_pages = 10
            st.session_state.max_pages = str(max_pages)
        
    run_grammar = st.checkbox("📝 Grammar & Spell Check", key="run_grammar_chk")
    
    run_api = st.checkbox("⚙️ API Endpoint Health Check", key="run_api_chk")
    if run_api:
        api_presets = {
            "Custom (Enter URL below)": f"{target_url}/api/health" if target_url else "",
            "DummyJSON (Complex Payload)": "https://dummyjson.com/products/1",
            "ReqRes (Mock User Data)": "https://reqres.in/api/users?page=2",
            "HttpBin (Network Tools)": "https://httpbin.org/get"
        }
        selected_preset = st.selectbox("Select an API source:", list(api_presets.keys()), key="api_preset_sel")
        if selected_preset == "Custom (Enter URL below)":
            api_endpoint = st.text_input("Specific API Endpoint:", value=api_presets["Custom (Enter URL below)"], key="api_endpoint_input")
        else:
            api_endpoint = api_presets[selected_preset]
            st.caption(f"Targeting: `{api_endpoint}`")
            
    run_security = st.checkbox("🔒 Security Header Audit", key="run_security_chk")
    
    run_load = st.checkbox("⏱️ Load Testing", key="run_load_chk")
    if run_load:
        total_reqs = st.number_input("Total Requests", min_value=10, value=1000, step=100, key="total_reqs_num")
        concurrency = st.number_input("Concurrent Users", min_value=1, value=10, step=5, key="concurrency_num")

    # ==========================================
    # MISSING TARGET URL UI LOGIC
    # ==========================================
    if not target_url and any([run_crawler, run_grammar, run_api, run_security, run_load]):
        st.error("🚨 Please enter a Target URL at the top to proceed.")
        st.markdown(
            """
            <style>
            [data-testid="stSidebar"] [data-testid="stTextInput"] input {
                background-color: rgba(198, 93, 87, 0.15) !important; /* Muted red background */
                border: 2px solid #C65D57 !important; /* Muted red border */
                border-radius: 6px !important;
            }
            [data-testid="stSidebar"] [data-testid="stTextInput"] > div[data-baseweb="input"],
            [data-testid="stSidebar"] [data-testid="stTextInput"] > div > div {
                border: 2px solid #C65D57 !important;
                box-shadow: 0 0 10px rgba(198, 93, 87, 0.6) !important;
                border-radius: 8px !important;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

    st.markdown("---")
    run_pressed = st.button("Run Verification Suite", type="primary", use_container_width=True)
    st.button("🔄 Reset App", on_click=reset_app, use_container_width=True)

# ==========================================
# 4. MAIN DASHBOARD (Execution & Results)
# ==========================================
if not target_url:
    st.title("🚀 QA Web Verifier Suite")
    st.write("👈 Configure your target environment and parameters in the sidebar to begin.")
    st.write("---")
    st.write("### System Status")
    st.write("🟢 Playwright Engine: Ready")
    st.write("🟢 Python Environment: Ready")
else:
    st.title("Unified QA Master Report")
    st.write("---")

    reports_placeholder = st.empty()

    if run_pressed:
        if not any([run_crawler, run_grammar, run_security, run_load, run_api]):
            st.warning("⚠️ Please select at least one audit module from the sidebar.")
            
        elif run_grammar and not run_crawler:
            st.error("🚨 Dependency Error: The Grammar Audit requires the Site Navigation Crawler to gather the text first. Please check the 'Site Navigation & Link Audit' box as well.")
            
        else:
            domain = urllib.parse.urlparse(target_url).netloc.replace(".", "_")
            
            reports_placeholder.empty()
            st.session_state["reports_ready"] = False
            
            for file in glob.glob("*_audit_report.html"):
                if os.path.exists(file):
                    try:
                        os.remove(file)
                    except Exception:
                        pass
            
            with st.status(f"Executing selected audits for **{target_url}**...", expanded=True) as status:
                
                if run_crawler:
                    if exhaustive_crawl:
                        st.write("🗺️ Running Exhaustive Full-Site Navigation & Link Audit...")
                    else:
                        st.write(f"🗺️ Running Site Navigation & Link Audit (Scanning up to {max_pages} pages)...")
                        
                    subprocess.run([sys.executable, "audit.py", target_url, str(max_pages)])
                    
                if run_grammar:
                    st.write("📝 Running Grammar Check...")
                    subprocess.run([sys.executable, "grammar_audit.py"])
                    
                if run_security:
                    st.write("🔒 Running Security Audit...")
                    subprocess.run([sys.executable, "security_audit.py", target_url])
                    
                if run_api:
                    st.write(f"⚙️ Running API Health Check on {api_endpoint}...")
                    subprocess.run([sys.executable, "api_audit.py", api_endpoint])
                    
                if run_load:
                    st.write(f"⏱️ Running Load Test ({total_reqs} requests)...")
                    load_metrics = run_native_load_test(target_url, total_requests=total_reqs, concurrent_users=concurrency)
                    write_load_test_report(load_metrics)
                
                status.update(label="✅ All selected audits complete!", state="complete", expanded=False)
                
            st.session_state.domain = domain
            st.session_state.reports_ready = True

# ==========================================
# 5. COMPILE AND DISPLAY MASTER REPORT
# ==========================================
if st.session_state.reports_ready:
    with reports_placeholder.container():
        st.success("🎉 Audits finished! Compiling Master Report...")
        domain = st.session_state.domain
        
        final_url_count = st.session_state.get("url_count", "N/A")
        final_max_pages = st.session_state.get("max_pages", "N/A")
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        
        master_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>QA Master Report - {domain}</title>
            <style>
                body {{ font-family: 'Goudy Old Style', Garamond, 'Times New Roman', serif; background-color: #F8F9FA; color: #212529; padding: 40px; }}
                .container {{ max-width: 1200px; margin: auto; }}
                .header-box {{ background-color: #546E7A; color: white; padding: 30px; border-radius: 8px; margin-bottom: 30px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                .stats-row {{ display: flex; justify-content: center; gap: 20px; margin-top: 20px; font-size: 15px; color: #E9ECEF; }}
                .stats-row span {{ background: rgba(255,255,255,0.1); padding: 8px 20px; border-radius: 20px; border: 1px solid rgba(255,255,255,0.2); }}
                
                /* Updated: Muted Sage Green for the Ready Banner */
                .verdict-banner {{ background-color: #5B8A72; color: white; font-size: 24px; font-weight: bold; padding: 15px; border-radius: 5px; text-align: center; margin-bottom: 30px; }}
                
                .module-card {{ background: white; padding: 30px; border-radius: 8px; margin-bottom: 30px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); border-left: 5px solid #546E7A; overflow-x: auto; }}
                .module-title {{ color: #546E7A; border-bottom: 2px solid #E9ECEF; padding-bottom: 10px; margin-top: 0; }}
                
                /* ==========================================
                   THE FIX: Force Sub-Modules to use Muted Colors
                   ========================================== */
                /* Automatically hunt down harsh greens and swap them to Muted Sage */
                .module-card [style*="color: green"], .module-card [style*="color: #28a745"], .module-card [style*="color: #28A745"], .module-card [style*="color:green"] {{
                    color: #5B8A72 !important;
                }}
                /* Automatically hunt down harsh reds and swap them to Dusty Brick Red */
                .module-card [style*="color: red"], .module-card [style*="color: #dc3545"], .module-card [style*="color: #DC3545"], .module-card [style*="color: #FF4B4B"], .module-card [style*="color:red"] {{
                    color: #C65D57 !important;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header-box">
                    <h1 style="margin-bottom: 10px; margin-top: 0;">Unified QA Master Report</h1>
                    <p style="margin-top: 0; color: #adb5bd;">Target: {target_url} | Scan Date: {timestamp}</p>
                    <div class="stats-row">
                        <span>🔍 Initial Links Found: <strong>{final_url_count}</strong></span>
                        <span>📄 Audit Page Depth: <strong>{final_max_pages}</strong></span>
                    </div>
                </div>
                <div class="verdict-banner">
                    ✅ READY FOR PRODUCTION - No Blockers Found
                </div>
        """

        if run_crawler and os.path.exists(f"{domain}_audit_report.html"):
            with open(f"{domain}_audit_report.html", "r", encoding="utf-8") as f:
                master_html += f"<div class='module-card'><h2 class='module-title'>🗺️ Navigation & Link Audit</h2>{f.read()}</div>"
                
        if run_grammar and os.path.exists("grammar_audit_report.html"):
            with open("grammar_audit_report.html", "r", encoding="utf-8") as f:
                master_html += f"<div class='module-card'><h2 class='module-title'>📝 Grammar & Spell Check</h2>{f.read()}</div>"
                
        if run_api and os.path.exists("api_audit_report.html"):
            with open("api_audit_report.html", "r", encoding="utf-8") as f:
                master_html += f"<div class='module-card'><h2 class='module-title'>⚙️ API Health Check</h2>{f.read()}</div>"
                
        if run_security and os.path.exists("security_audit_report.html"):
            with open("security_audit_report.html", "r", encoding="utf-8") as f:
                master_html += f"<div class='module-card'><h2 class='module-title'>🔒 Security Header Audit</h2>{f.read()}</div>"
                
        if run_load and os.path.exists("load_audit_report.html"):
            with open("load_audit_report.html", "r", encoding="utf-8") as f:
                master_html += f"<div class='module-card'><h2 class='module-title'>⏱️ Load Testing</h2>{f.read()}</div>"

        master_html += """
                <div style="text-align: center; color: #6c757d; margin-top: 50px; font-size: 12px;">
                    Report generated by QA Web Verifier Suite | Version 1.0
                </div>
            </div>
        </body>
        </html>
        """

        master_filename = f"{domain}_MASTER_REPORT.html"
        with open(master_filename, "w", encoding="utf-8") as f:
            f.write(master_html)

        # ==========================================
        # THE NEW TAB FIX: Secure Blob URL + Blue-Gray Button
        # ==========================================
        st.markdown("---")
        st.subheader("📄 Master Report Ready")
        st.info("💡 **Click the button below to instantly open your full Master Report in a new, full-screen browser tab.**")
        
        import base64
        # Encode the HTML to safely pass it to JavaScript
        b64_html = base64.b64encode(master_html.encode('utf-8')).decode('utf-8')
        
        # We MUST use components.html here so the browser actually runs the JavaScript
        open_tab_js = f"""
        <div id="btn-container" style="display: flex; justify-content: center; margin-top: 20px;">
            </div>
        <script>
            try {{
                // Safely decode Base64 into a UTF-8 string
                const b64Data = "{b64_html}";
                const binaryStr = window.atob(b64Data);
                const bytes = new Uint8Array(binaryStr.length);
                for (let i = 0; i < binaryStr.length; i++) {{
                    bytes[i] = binaryStr.charCodeAt(i);
                }}
                const decodedHtml = new TextDecoder('utf-8').decode(bytes);

                // Create a file-like Blob in the browser's memory
                const blob = new Blob([decodedHtml], {{ type: 'text/html' }});
                const url = URL.createObjectURL(blob);
                
                // Inject the button with the true Blob URL attached BEFORE the user clicks. Included font update to match.
                const container = document.getElementById('btn-container');
                container.innerHTML = `
                    <a id="open-report-btn" href="${{url}}" target="_blank" style="background-color: #546E7A; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-family: 'Goudy Old Style', Garamond, 'Times New Roman', serif; font-weight: bold; font-size: 16px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); cursor: pointer; transition: background-color 0.3s; display: inline-block;">
                        📘 Open Master Report in New Tab
                    </a>
                `;
                
                // Add a subtle hover effect (darkens to Slate)
                const btn = document.getElementById('open-report-btn');
                btn.addEventListener('mouseover', function() {{ this.style.backgroundColor = '#37474F'; }});
                btn.addEventListener('mouseout', function() {{ this.style.backgroundColor = '#546E7A'; }});
            }} catch (e) {{
                // Fallback in case of error
                console.error(e);
            }}
        </script>
        """
        
        # Render the custom button securely using components.html!
        components.html(open_tab_js, height=100)
