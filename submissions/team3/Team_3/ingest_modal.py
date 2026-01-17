import modal
import os
import shutil

# 1. Define Cloud Image
# We explicitly install the new split packages to fix the import errors
image = (
    modal.Image.debian_slim()
    .pip_install(
        "langchain",
        "langchain-community",
        "langchain-core",            # <--- ADDED: Required for Document
        "langchain-text-splitters",  # <--- ADDED: Required for Splitter
        "langchain-google-genai",    # <--- ADDED: For Google Embeddings
        "faiss-cpu",
        "networkx"
    )
    .add_local_dir("metakgp_data", remote_path="/root/data")
)

app = modal.App("metakgp-google-ingest", image=image)

@app.function(image=image, timeout=600)
def run_ingestion(api_key):
    import glob
    import json
    import networkx as nx
    
    # --- UPDATED IMPORTS (The "Modern" Way) ---
    from langchain_community.vectorstores import FAISS
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_core.documents import Document
    
    print(" cloud: Starting Google Ingestion...")
    
    DATA_DIR = "/root/data"
    OUTPUT_DIR = "/root/output"
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 2. SETUP GOOGLE EMBEDDINGS
    # We use 'models/text-embedding-004' which is newer and more stable
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/text-embedding-004", 
        google_api_key=api_key
    )
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    G = nx.DiGraph()
    documents = []
    
    # 3. PROCESS FILES
    json_files = glob.glob(os.path.join(DATA_DIR, "*.json"))
    print(f" cloud: Found {len(json_files)} files.")

    for file_path in json_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                batch_data = json.load(f)
                for page in batch_data:
                    url = page.get('url', '')
                    title = page.get('title', 'No Title')
                    content = page.get('content', '')
                    links = page.get('links', [])
                    
                    if url:
                        G.add_node(url, title=title)
                        for target in links:
                            if "wiki.metakgp.org" in target:
                                G.add_edge(url, target)
                                
                    if len(content) > 50:
                        doc = Document(page_content=content, metadata={"source": url, "title": title})
                        documents.append(doc)
        except Exception as e:
            print(f"Skipping file error: {e}")

    # 4. BUILD & SAVE
    if documents:
        print(f" cloud: Vectorizing {len(documents)} pages with Google...")
        try:
            chunks = text_splitter.split_documents(documents)
            # This is where the embedding happens
            vector_db = FAISS.from_documents(chunks, embeddings)
            
            vector_db.save_local(os.path.join(OUTPUT_DIR, "faiss_index"))
            nx.write_gml(G, os.path.join(OUTPUT_DIR, "metakgp_graph.gml"))
            
            shutil.make_archive("/root/results", 'zip', OUTPUT_DIR)
            with open("/root/results.zip", "rb") as f:
                return f.read()
        except Exception as e:
            print(f" Error during embedding: {e}")
            return None
            
    print(" No documents found to process.")
    return None

@app.local_entrypoint()
def main():
    # DOUBLE CHECK YOUR KEY IS CORRECT
    MY_API_KEY = "AIzaSyAsgcIwteMXQzve95ki1gTeIMMlq7zGGo8" 
    
    print("Sending to Modal Cloud...")
    zip_bytes = run_ingestion.remote(MY_API_KEY)
    
    if zip_bytes:
        with open("results.zip", "wb") as f:
            f.write(zip_bytes)
        import zipfile
        with zipfile.ZipFile("results.zip", 'r') as zip_ref:
            zip_ref.extractall(".")
        print(" SUCCESS! New Google-compatible Brains downloaded.")
    else:
        print(" Failed to get results. Check the cloud logs above.")