# MetaKGP Wiki Scraper

A robust, concurrent wiki scraper for MetaKGP (https://wiki.metakgp.org) with batch processing, multi-threading, and organized output.

## ✨ Features

- 🚀 **Concurrent scraping** with 4-20 threads for parallel processing
- 📦 **Batch file storage** - save pages in separate files for better organization
- 🎯 **Flexible control** - scrape specific ranges, limits, or the entire wiki
- 📊 **Multiple formats** - JSON (structured) and text (readable) outputs
- 🔍 **Complete page list** - all 3,583 pages already fetched
- 🎮 **Easy to use** - simple Python commands
- 📁 **Clean structure** - organized src/ and results/ folders

## 📁 Project Structure

```
testing/
├── src/                        # Source code
│   ├── main.py                # Main parallel scraper ⭐
│   ├── fetch_all_links.py     # Fetch all page links
│   └── clean_wikitext.py      # Clean wikitext for indexing
├── results/                    # All data outputs
│   ├── all_pages.json         # List of all 3,583 pages ✅
│   ├── all_pages.txt          # Text version
│   └── scraped_data/          # Scraped page content
│       ├── scraped_pages.json
│       ├── scraped_pages_batch1.json
│       ├── scraped_pages_batch2.json
│       └── ...
├── venv/                       # Python virtual environment
└── README.md                   # This file
```

## 🚀 Quick Start

### 1. Activate Environment

```bash
# Activate virtual environment (from project root)
source venv/bin/activate
```

### 3. Scrape Pages

```bash
# Quick sample (10 pages)
python src/main.py results/all_pages.json --limit 10

# Medium batch (100 pages in batches of 25)
python src/main.py results/all_pages.json --limit 100 --pages 25 --threads 8

# Full wiki (all 3,583 pages in batches of 50)
python src/main.py results/all_pages.json --pages 50 --threads 4
```

### 3. Check Results

```bash
ls -lh results/scraped_data/
```

## 📖 Usage Examples

### Basic Usage

```bash
# Scrape 10 pages (single file output)
python src/main.py results/all_pages.json --limit 10

# Scrape 10 pages with text output
python src/main.py results/all_pages.json --limit 10 --text
```

### Batch Processing

```bash
# Scrape 100 pages in batches of 20 (creates 5 files)
python src/main.py results/all_pages.json --limit 100 --pages 20

# Each batch file contains max 20 pages:
# - results/scraped_data/scraped_pages_batch1.json
# - results/scraped_data/scraped_pages_batch2.json
# - results/scraped_data/scraped_pages_batch3.json
# - results/scraped_data/scraped_pages_batch4.json
# - results/scraped_data/scraped_pages_batch5.json
```

### Advanced Options

```bash
# Increase threads for faster scraping
python src/main.py results/all_pages.json --limit 100 --threads 8

# Skip first 50 pages, scrape next 50
python src/main.py results/all_pages.json --start 50 --limit 50

# Scrape ALL pages in batches of 100 with text output
python src/main.py results/all_pages.json --pages 100 --threads 8 --text
```

### Interactive Menu

```bash
python src/index.py
```

This provides an interactive interface with options to:
1. Fetch all page links
2. Scrape pages concurrently
3. Quick scrape samples
4. Exit

## 🎛️ Command-Line Options

### main.py

```
Required:
  input_file              JSON file with list of pages (use results/all_pages.json)

Optional:
  --limit N               Total number of pages to scrape (default: all)
  --pages N               Batch size - max pages per output file (default: all in one file)
  --threads N             Number of concurrent threads (default: 4, max: 20)
  --start N               Starting index in page list (default: 0)
  --text                  Also save in readable text format
```

### fetch_all_links.py

```
Optional:
  --output FILE           Output filename (default: all_pages)
  --no-text              Don't save text version
```

## 📊 Performance

- **Speed:** ~0.36-0.40 seconds per page with 4 threads
- **Full wiki:** ~20-30 minutes for all 3,583 pages
- **Memory:** Minimal - each batch saved immediately

## 💡 Common Workflows

### 1. First Time Setup (Already Done ✅)

```bash
source venv/bin/activate
python src/fetch_all_links.py  # Fetches all 3,583 page titles
```

### 2. Sample Testing

```bash
# Test with 10 pages first
python src/main.py results/all_pages.json --limit 10

# Check output
cat results/scraped_data/scraped_pages.json | jq '.pages | length'
```

### 3. Production Scraping

```bash
# Scrape entire wiki in manageable batches
python src/main.py results/all_pages.json --pages 50 --threads 8 --text

# This creates ~72 batch files with 50 pages each
# Both JSON and text formats for easy viewing
```

### 4. Specific Range

```bash
# Scrape pages 1000-1100 in batches of 25
python src/main.py results/all_pages.json --start 1000 --limit 100 --pages 25
```

## 🔧 All Available Scripts

### Concurrent Scraper (Main Tool)

```bash
python src/main.py results/all_pages.json [OPTIONS]
```

### Fetch All Page Links

```bash
python src/fetch_all_links.py [OPTIONS]
```

### Interactive Menu

```bash
python src/index.py
```

### Single Page Examples

```bash
# Get wiki statistics
python src/examples.py stats

# Scrape a specific page
python src/examples.py page "Main Page"

# Scrape a category
python src/examples.py category "Students"

# Search for pages
python src/examples.py search "election"
```

## 📦 Output Format

### JSON Structure

```json
{
  "total_pages": 10,
  "batch_number": 1,
  "scraped_at": "2024-01-15T10:30:00",
  "pages": [
    {
      "title": "Page Title",
      "content": "Full page content...",
      "url": "https://wiki.metakgp.org/w/Page_Title",
      "last_modified": "2023-12-01T12:00:00",
      "categories": ["Category1", "Category2"],
      "links": ["Link1", "Link2"]
    }
  ]
}
```

### Text Format

```
=== Page Title ===
URL: https://wiki.metakgp.org/w/Page_Title
Last Modified: 2023-12-01T12:00:00

Content:
Full page content...

Categories: Category1, Category2
Links: Link1, Link2
```

## 🛠️ Dependencies

- Python 3.13+
- mwclient 0.11.0 - MediaWiki API client
- beautifulsoup4 4.14.3 - HTML parsing
- requests 2.32.5 - HTTP library

All dependencies are already installed in the virtual environment.

## 📚 Additional Documentation

- `QUICK_START.md` - Quick reference guide
- `SCRAPER_README.md` - Detailed technical documentation
- `UPDATE_NOTES.md` - Flag system changes
- `BATCH_FILES_FEATURE.md` - Batch processing details

## 🎯 Current Status

- ✅ All 3,583 page links fetched and saved
- ✅ Concurrent scraper tested and working
- ✅ Batch processing tested with 5, 10, 25 pages per batch
- ✅ Performance validated: ~0.36-0.40 seconds/page
- ✅ Full project structure organized

## 🚦 Next Steps

1. **Activate environment:**
   ```bash
   source venv/bin/activate
   ```

2. **Run a quick test:**
   ```bash
   python src/main.py results/all_pages.json --limit 10
   ```

3. **Check the output:**
   ```bash
   cat results/scraped_data/scraped_pages.json
   ```

4. **Run full scrape:**
   ```bash
   python src/main.py results/all_pages.json --pages 50 --threads 8
   ```

## 📝 License

This is a scraper tool for MetaKGP Wiki. Please respect the wiki's terms of service and rate limits.
