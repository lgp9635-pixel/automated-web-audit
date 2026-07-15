# utils.py
from jinja2 import Template
import webbrowser
import os
import csv

def generate_html_report(domain, total, broken, passed, broken_links):
    """
    Generates a standardized audit report in HTML format.
    """
    filename = f"{domain.replace('.', '_')}_audit_report.html"
    
    html_template = """
    <!DOCTYPE html><html><head><style>
        .High { color: red; font-weight: bold; }
        .Medium { color: orange; }
        .Low { color: gray; }
        .summary { margin-bottom: 20px; padding: 15px; background: #f4f4f4; border-radius: 5px; }
        table { border-collapse: collapse; width: 100%; margin-top: 20px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
    </style></head><body>
        <h1>Audit Report: {{ domain }}</h1>
        <div class="summary">
            <p>Total Links Validated: <strong>{{ total }}</strong></p>
            <p style="color: green;">Links Passed: <strong>{{ passed }}</strong></p>
            <p style="color: red;">Broken Links Found: <strong>{{ broken }}</strong></p>
        </div>
        <h2>Broken Links</h2>
        <table>
            <tr>
                <th>Priority</th>
                <th>Anchor Text</th>
                <th>Broken Link</th>
                <th>Status</th>
                <th>Found On</th>
            </tr>
            {% for link in broken_links %}
            <tr class="{{ link.priority }}">
                <td>{{ link.priority }}</td>
                <td>{{ link.text }}</td>
                <td><a href="{{ link.url }}">{{ link.url }}</a></td>
                <td>{{ link.status }}</td>
                <td>{{ link.found_on }}</td>
            </tr>
            {% endfor %}
        </table>
    </body></html>"""
    
    template = Template(html_template)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(template.render(
            domain=domain, 
            broken_links=broken_links, 
            total=total, 
            broken=broken, 
            passed=passed
        ))
    
    webbrowser.open(f"file://{os.path.abspath(filename)}")
    print(f"\n✅ Report generated: {filename}")


def write_grammar_report(errors, output_filename="grammar_audit_report.html"):
    """
    Takes a list of error dictionaries and writes them to an HTML report.
    """
    if not errors:
        print("✅ Great news! No grammar or spelling errors found.")
        return
        
    html_template = """
    <!DOCTYPE html><html><head><style>
        body { font-family: sans-serif; margin: 20px; }
        .summary { margin-bottom: 20px; padding: 15px; background: #f4f4f4; border-radius: 5px; }
        table { border-collapse: collapse; width: 100%; margin-top: 20px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; vertical-align: top; }
        th { background-color: #eaeaea; }
        .correction { color: green; font-weight: bold; }
        .context-highlight { background-color: #ffe6e6; padding: 2px; border-radius: 3px; }
    </style></head><body>
        <h1>Grammar & Spelling Audit Report</h1>
        <div class="summary">
            <p>Total Issues Found: <strong>{{ total_errors }}</strong></p>
        </div>
        <table>
            <tr>
                <th>URL</th>
                <th>Issue Type</th>
                <th>Message</th>
                <th>Context</th>
                <th>Suggested Correction</th>
            </tr>
            {% for error in errors %}
            <tr>
                <td><a href="{{ error['URL'] }}" target="_blank">Page Link</a></td>
                <td>{{ error['Issue Type'] }}</td>
                <td>{{ error['Message'] }}</td>
                <td><em>{{ error['Context'] }}</em></td>
                <td class="correction">{{ error['Correction'] }}</td>
            </tr>
            {% endfor %}
        </table>
    </body></html>"""
    
    try:
        template = Template(html_template)
        
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(template.render(
                errors=errors,
                total_errors=len(errors)
            ))
            
        print(f"📝 Grammar and spelling HTML report successfully generated: {output_filename}")
        
        # Automatically pop it open in the browser!
        webbrowser.open(f"file://{os.path.abspath(output_filename)}")
        
    except Exception as e:
        print(f"⚠️ An error occurred while writing the report: {e}")

def write_security_report(domain, results, output_filename="security_audit_report.html"):
    """
    Takes a list of security header results and writes them to an HTML report.
    """
    if not results:
        print("⚠️ No security data to report.")
        return
        
    html_template = """
    <!DOCTYPE html><html><head><style>
        body { font-family: sans-serif; margin: 20px; }
        .summary { margin-bottom: 20px; padding: 15px; background: #f4f4f4; border-radius: 5px; }
        table { border-collapse: collapse; width: 100%; margin-top: 20px; }
        th, td { border: 1px solid #ddd; padding: 10px; text-align: left; }
        th { background-color: #eaeaea; }
        .pass { color: green; font-weight: bold; }
        .fail { color: red; font-weight: bold; }
        .warning { color: darkorange; font-weight: bold; }
        code { background-color: #f4f4f4; padding: 2px 5px; border-radius: 3px; }
    </style></head><body>
        <h1>Advanced Security Header Audit: {{ domain }}</h1>
        <div class="summary">
            <p>This report analyzes the presence of critical HTTP security headers and checks for unauthorized server information leakage.</p>
        </div>
        <table>
            <tr>
                <th>Security Header</th>
                <th>Category</th>
                <th>Status</th>
                <th>Purpose</th>
                <th>Value Found</th>
            </tr>
            {% for item in results %}
            <tr>
                <td><strong>{{ item['Header'] }}</strong></td>
                <td>{{ item['Category'] }}</td>
                <td class="{% if '✅' in item['Status'] %}pass{% elif '⚠️' in item['Status'] %}warning{% else %}fail{% endif %}">
                    {{ item['Status'] }}
                </td>
                <td>{{ item['Description'] }}</td>
                <td><code>{{ item['Value'] }}</code></td>
            </tr>
            {% endfor %}
        </table>
    </body></html>"""
    
    try:
        from jinja2 import Template
        import os, webbrowser
        
        template = Template(html_template)
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(template.render(domain=domain, results=results))
            
        print(f"🔒 Advanced Security HTML report successfully generated: {output_filename}")
        webbrowser.open(f"file://{os.path.abspath(output_filename)}")
        
    except Exception as e:
        print(f"⚠️ An error occurred while writing the security report: {e}")


def write_load_test_report(metrics, output_filename="load_audit_report.html"):
    """
    Takes the load test metrics dictionary and writes them to an HTML report.
    """
    if not metrics:
        print("⚠️ No load test data to report.")
        return
        
    # Determine color based on 100% success rate
    success_color = "green" if metrics.get('success_rate_percent', 0) == 100.0 else "red"
        
    html_template = """
    <!DOCTYPE html><html><head><style>
        body { font-family: sans-serif; margin: 20px; }
        .summary { margin-bottom: 20px; padding: 15px; background: #f4f4f4; border-radius: 5px; }
        table { border-collapse: collapse; width: 100%; margin-top: 20px; }
        th, td { border: 1px solid #ddd; padding: 10px; text-align: left; }
        th { background-color: #eaeaea; width: 40%; }
    </style></head><body>
        <h1>Load Test Audit Report</h1>
        <div class="summary">
            <p><strong>Target:</strong> <a href="{{ metrics['url'] }}" target="_blank">{{ metrics['url'] }}</a></p>
            <p>Performance metrics for simulated concurrent traffic.</p>
        </div>
        <table>
            <tr>
                <th>Total Requests Sent</th>
                <td>{{ metrics['total_requests'] }}</td>
            </tr>
            <tr>
                <th>Success Rate</th>
                <td style="color: {{ success_color }}; font-weight: bold;">{{ metrics['success_rate_percent'] }}%</td>
            </tr>
            <tr>
                <th>Avg Response Time</th>
                <td>{{ metrics['avg_response_time_sec'] }} seconds</td>
            </tr>
            <tr>
                <th>Max Response Time</th>
                <td>{{ metrics['max_response_time_sec'] }} seconds</td>
            </tr>
        </table>
    </body></html>"""
    
    try:
        # Template is already imported at the top of utils.py
        template = Template(html_template)
        
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(template.render(
                metrics
