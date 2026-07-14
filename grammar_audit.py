import json
import os
import language_tool_python
from bs4 import BeautifulSoup
from utils import write_grammar_report

def analyze_scraped_content(input_filename="scraped_content.jsonl"):
    """
    Reads the scraped text and checks for grammar/spelling errors.
    """
    if not os.path.exists(input_filename):
        print(f"❌ Error: {input_filename} not found. Did you run audit.py first?")
        return []

    print("🚀 Initializing grammar checker (this may take a moment to load)...")
    tool = language_tool_python.LanguageTool('en-US')
    
    all_errors = []
    
    print(f"🔍 Analyzing text from {input_filename}...")
    
    # Read the file line by line so we don't blow up our memory!
    with open(input_filename, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line)
            url = data.get('url')
            raw_content = data.get('text', '')
            
            if not raw_content:
                continue
                
            # --- NEW: BeautifulSoup Filtering Step ---
            # Parse the content to strip out navigation, headers, footers, and scripts
            soup = BeautifulSoup(raw_content, "html.parser")
            
            # Remove the noisy HTML elements that cause false positives
            for element in soup(["nav", "header", "footer", "script", "style", "aside", "noscript"]):
                element.decompose()
                
            # Extract only the clean, visible text
            clean_text = soup.get_text(separator=' ', strip=True)
            
            # Check the CLEANED text for errors
            matches = tool.check(clean_text)
            
            for match in matches:
                # --- NEW: Ignore specific False Positive rules ---
                # Silence the rules that trigger on responsive website menus
                if match.rule_issue_type == 'duplication' or "is duplicated" in match.message:
                    continue
                    
                all_errors.append({
                    'URL': url,
                    'Issue Type': match.rule_issue_type,
                    'Message': match.message,
                    'Context': match.context,
                    'Correction': ", ".join(match.replacements[:3])
                })     

    tool.close()
    
    # Optional: Clean up the temporary text file when we are done
    os.remove(input_filename)
    print(f"🧹 Cleaned up temporary file: {input_filename}")
    
    return all_errors

if __name__ == "__main__":
    # 1. Run the analysis
    errors_found = analyze_scraped_content()
    
    # 2. Call the function that lives in utils.py!
    write_grammar_report(errors_found)