import requests
import json
import time
import os
from bs4 import BeautifulSoup
from urllib.parse import unquote

# --- CONFIGURATION ---
INPUT_FILE = "all_article_urls.txt"
OUTPUT_DIR = "metakgp_data"
API_URL = "https://wiki.metakgp.org/api.php"
BATCH_SIZE = 100  # Save every 100 pages

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# 1.SETUP SESSION
session = requests.Session()
# faking browser
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) GraphMindBot/1.0"
})

# 2.LOAD URLS
try:
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()]
    print(f" Loaded {len(urls)} URLs. Switching to API Mode...")
except FileNotFoundError:
    print(f" Error: {INPUT_FILE} not found!")
    exit()

batch_data = [] #cleared once batch size is  reached

# 3. MAIN LOOP
for i, url in enumerate(urls):#enumerate->returns index,values of list(for progress tracking)
    try:
        # Step A: Extract Title from URL
        # URL: https://wiki.metakgp.org/wiki/Spring_Fest -> Title: "Spring Fest"
        if "/wiki/" not in url:
            continue
            
        title_slug = url.split("/wiki/")[-1]
        page_title = unquote(title_slug).replace("_", " ")# remove %20 %28 etc
        
        # S Ask the API for this specific title
        
        params = {
            "action": "parse",
            "page": page_title,
            "format": "json",
            "prop": "text", 
            "redirects": 1
        }
        
        # Status Log
        print(f"[{i+1}/{len(urls)}] API Request: {page_title}")

        response = session.get(API_URL, params=params, timeout=10)
        data = response.json()
        
        #  Handle Errors
        if "error" in data:
            print(f"    API Error: {data['error'].get('info')}")
            continue
            
        #  Process Content
        if "parse" in data:
            raw_html = data['parse']['text']['*']
            actual_title = data['parse']['title'] # The real title (in case of redirect)
            
            # Convert HTML to clean text
            soup = BeautifulSoup(raw_html, 'html.parser')
            
            # Remove "junk" that might clutter your AI
            for trash in soup.select('script, style, .mw-editsection, .printfooter'):
                trash.decompose()

            clean_text = soup.get_text(separator="\n").strip()
            
            # Extract Links for your Graph
            outgoing_links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.startswith("/wiki/") and ":" not in href:
                    full_link = f"https://wiki.metakgp.org{href}"
                    outgoing_links.append(full_link)

            # Add to Batch
            batch_data.append({
                "url": url,
                "title": actual_title,
                "content": clean_text,
                "links": list(set(outgoing_links))
            })

    except Exception as e:
        print(f"Network Error on {url}: {e}")

    # Be polite to the server
    time.sleep(0.1)

    # 4. SAVE BATCH
    if len(batch_data) >= BATCH_SIZE:
        timestamp = int(time.time())
        filename = os.path.join(OUTPUT_DIR, f"batch_api_{timestamp}.json")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(batch_data, f, ensure_ascii=False, indent=2)
        print(f"Saved Batch: {filename}")
        batch_data = []

# Save leftovers
if batch_data:
    filename = os.path.join(OUTPUT_DIR, "batch_final.json")
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(batch_data, f, ensure_ascii=False, indent=2)
    print("Saved final batch.")

print("\nDOWNLOAD COMPLETE!")