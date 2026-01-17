# MetaKGP Wiki Scraper & Vector Database

A Python project that scrapes the MetaKGP wiki, processes article content, and builds a searchable vector database using Google's Generative AI embeddings and FAISS.

---

## Team Name: [Insert Team Name]

### 👥 Team Members
- Member 1: Abhinav Bhardwaj- [abhinav2428]
- Member 2: Anshika - [Ancoderk]
- Member 3: Varad - [varad-oss]


## 🤖 Technical Implementation

### 1. Data Pipeline (Scraping)

**Tools Used:**
- Beautiful Soup 4 - HTML parsing and content extraction
- Requests - HTTP client for API calls
- PyWikiBot - Wiki API interaction

**Strategy:** 
The scraper follows a three-stage pipeline:
1. **URL Discovery** - Fetch all article URLs from the MetaKGP API (main.py)
2. **Content Extraction** - Download and process article content with HTML cleaning (fetch_content.py)
3. **Vectorization** - Create embeddings and build FAISS index using Google's API (ingest_modal.py)

The scraper handles:
- HTML content cleaning and text extraction
- UTF-8 encoding issues gracefully
- Rate limiting (0.1s delay per request)
- Network timeouts with retry logic
- Batch processing with configurable sizes (default: 100 pages per batch)

**Indexing:** FAISS vector database powered by Google's Generative AI embeddings (`text-embedding-004`)

### 2. Graph of Thoughts (GoT)

**Reasoning Model:**
- Nodes represent individual MetaKGP wiki articles/pages
- Edges represent internal wiki links connecting related pages
- Each node stores: article URL, title, cleaned content, and embedding vector

**Graph Logic:**
Knowledge graph connects different MetaKGP pages by:
- Extracting outgoing wiki links from article content
- Creating edges between "Society" pages, "Student" pages, "Academic" pages, etc.
- Enabling semantic traversal: e.g., a "Society" page links to associated "Student" members
- NetworkX generates graph structure in GML format for visualization and analysis
- Allows multi-hop reasoning across related knowledge domains

### 3. Mixture of Experts (MoE)

**Expert 1 (Source Matcher):**
- Verifies retrieved text exists in the scraped MetaKGP data
- Cross-references embeddings with original content
- Returns exact source URL and article title

**Expert 2 (Hallucination Hunter):**
- Detects fabricated or inconsistent information
- Validates semantic coherence with source content
- Flags low-confidence matches below similarity threshold

**Expert 3 (Logic Expert):**
- Ensures logical consistency across linked pages
- Verifies citations and references between articles
- Maintains factual integrity through graph traversal

---

## 📊 Setup Instructions

### Prerequisites
- Python 3.8+
- pip (Python package manager)
- Google Generative AI API key (free from [Google AI Studio](https://aistudio.google.com/app/apikey))
- Modal account (for cloud ingestion - optional)
- Internet connection

---

## 📊 Setup Instructions

### Prerequisites
- Python 3.8+
- pip (Python package manager)
- Google Generative AI API key (free from [Google AI Studio](https://aistudio.google.com/app/apikey))
- Modal account (for cloud ingestion - optional)
- Internet connection

### Environment Variables

Create a `.env` file in the project root (do not share actual keys):

```
GOOGLE_API_KEY=your_google_generative_ai_key_here
MODAL_TOKEN_PATH=/path/to/modal/token  # Optional, for cloud deployment
```

**Required Environment Keys:**
- `GOOGLE_API_KEY` - Google Generative AI API key for embedding generation

### How to Run

#### 1. Installation & Setup

```bash
# Clone the repository
git clone <repository-url>
cd Team_3

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### 2. Run Scraper (Fetch & Index)

```bash
# Step 1: Fetch all wiki article URLs
python main.py

# Step 2: Download and process article content
python fetch_content.py

# Step 3: Create vector database and knowledge graph (Cloud)
# Update GOOGLE_API_KEY in ingest_modal.py first
python ingest_modal.py
```

#### 3. Run Bot/Chat Interface

```bash
# Start the Streamlit chat interface
streamlit run app.py

# Or run the basic bot
python bot.py
```

#### Quick Start
```bash
# Run all steps in sequence
python run.py
```

---

## 📸 Screenshots

[Image of Graph Visualization]

[Image of Chat Interface]
![alt text](<Screenshot 2026-01-17 160652.png>)
---

## Requirements

## Project Structure

```
Team_3/
├── main.py                      # Fetch all wiki article URLs
├── fetch_content.py             # Download and process article content
├── ingest_modal.py              # Cloud ingestion with Google embeddings
├── app.py                       # Streamlit chat interface
├── bot.py                       # Bot implementation
├── run.py                       # Quick start script
├── families/
│   └── metakgp_family.py        # PyWikiBot family configuration
├── metakgp_data/                # Generated batch JSON files
├── faiss_index/                 # Generated FAISS vector index
├── static/                      # Frontend assets
│   ├── index.html               # Chat UI
│   ├── script.js                # Frontend logic
│   └── styles.css               # Styling
├── all_article_urls.txt         # Generated URL list
├── metakgp_graph.gml            # Generated knowledge graph
├── requirements.txt             # Python dependencies
├── ARCHITECTURE/
│   └── ARCHITECTURE.md          # Detailed technical documentation
├── FRONT_END/
│   └── README.md                # Frontend documentation
└── README.md                    # This file
```

## Key Features

- ✅ Automated wiki scraping via MetaKGP API
- ✅ HTML content cleaning and text extraction
- ✅ Batch processing with configurable sizes
- ✅ Knowledge graph generation using NetworkX
- ✅ Cloud-based embedding generation with Modal
- ✅ FAISS vector database for semantic search
- ✅ Graceful error handling and progress logging
- ✅ Mixture of Experts architecture for fact verification
- ✅ Web-based chat interface (Streamlit)

## Dependencies

Core Dependencies:
- `requests` - HTTP client for API calls
- `beautifulsoup4` - HTML parsing and content extraction
- `langchain` - LLM framework
- `langchain-google-genai` - Google embeddings integration
- `langchain-text-splitters` - Text chunking
- `faiss-cpu` - Vector similarity search
- `networkx` - Graph data structure
- `pywikibot` - Wiki API interaction

Optional (for cloud deployment):
- `modal` - Cloud compute platform
- `streamlit` - Web interface framework

Install all dependencies:
```bash
pip install -r requirements.txt
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `all_article_urls.txt not found` | Run `python main.py` first to generate the URL list |
| `API Error: Page not found` | Some wiki pages may be deleted or redirected. Check at `https://wiki.metakgp.org/wiki/PageName` |
| `FAISS import error` | Reinstall: `pip install --force-reinstall faiss-cpu` |
| `Google API key error` | Verify API key is correct and has Generative AI access enabled |
| `Modal authentication failed` | Run `modal token new` to set up Modal credentials |

## Performance Considerations

1. **Batch Size**: Adjust `BATCH_SIZE` in `fetch_content.py`:
   - Smaller batches (10-50) for slow connections
   - Larger batches (200-500) for high-speed connections

2. **Rate Limiting**: Built-in 0.1s delay between requests to be respectful to the wiki server

3. **Cloud Ingestion**: Modal handles parallel processing for faster embedding generation

## Security Notes

⚠️ **Important:** Never commit sensitive credentials to the repository:
- Use `.env` files for local configuration (add to `.gitignore`)
- Store API keys securely
- Use environment variables in production
- Rotate keys regularly if exposed

## License

Distributed under the MIT License. See LICENSE.txt for more information.

## Contact & Support

For issues, questions, or suggestions, please open an issue on the GitHub repository.

---

**Note:** This project is designed for the MetaKGP wiki. Adaptation to other wikis may require configuration changes.

**Last Updated:** January 2026
