import requests
import time

# --- CONFIGURATION ---
API_URL = "https://wiki.metakgp.org/api.php"
OUTPUT_FILE = "all_article_urls.txt"
BASE_URL = "https://wiki.metakgp.org/wiki/"

# We ask for:
# action=query: "I want to ask a question"
# list=allpages: "Give me the list of all pages"
# aplimit=500: "Give me 500 at a time" (Maximum allowed)
# apnamespace=0: "Only real articles" (No User pages, No Talk pages, No Files)
params = {
    "action": "query",
    "format": "json",
    "list": "allpages",
    "aplimit": "500",
    "apnamespace": "0" 
}

all_titles = []
print("--- Contacting MetaKGP API ---")

while True:
    try:
        response = requests.get(API_URL, params=params, timeout=10)
        data = response.json()
        
        # Extract pages from the JSON response
        pages = data.get("query", {}).get("allpages", [])
        
        for page in pages:
            # The API gives us the title (e.g., "Technology Literary Society")
            # We convert it to a URL: "Technology_Literary_Society"
            clean_title = page['title'].replace(" ", "_")
            full_url = BASE_URL + clean_title
            all_titles.append(full_url)
            
        print(f"Fetched {len(pages)} pages... Total: {len(all_titles)}")
        
        # Check if there are more pages (Pagination)
        if "continue" in data:
            params["apcontinue"] = data["continue"]["apcontinue"]
            time.sleep(0.5) # Be polite
        else:
            break # No more pages

    except Exception as e:
        print(f"Error: {e}")
        break

# Save to file
print(f"\nWriting {len(all_titles)} URLs to {OUTPUT_FILE}...")
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    for url in all_titles:
        f.write(url + "\n")

print("Done! run main.py")