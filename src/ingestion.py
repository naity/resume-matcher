import asyncio
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.documents import Document

load_dotenv()

# Base Search URL (without page param)
BASE_SEARCH_URL = "https://www.google.com/about/careers/applications/jobs/results?location=Seattle%2C%20WA%2C%20USA"

def get_job_urls(base_url: str, pages: int = 5) -> list[str]:
    """
    Crawls multiple pages of search results.
    """
    job_urls = set()
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    for page in range(1, pages + 1):
        url = f"{base_url}&page={page}"
        print(f"🔍 Crawling page {page}: {url}")
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Simplified logic as requested
            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                if "jobs/results/" in href:
                     full_url = f"https://www.google.com/about/careers/applications/{href}"
                     job_urls.add(full_url)
                     
        except Exception as e:
            print(f"❌ Error on page {page}: {e}")
            
    print(f"🎉 Found {len(job_urls)} unique job links across {pages} pages!")
    return list(job_urls)

async def ingest_jobs():
    """Ingests real job descriptions from the web into ChromaDB."""
    print("🚀 Starting ingestion from Web...")
    
    # 1. Get Job URLs dynamically (5 pages)
    job_urls = get_job_urls(BASE_SEARCH_URL, pages=5)
    
    if not job_urls:
        print("⚠️ No jobs found. Exiting.")
        return

    print(f"🕷️ Scraping content for {len(job_urls)} jobs...")

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vector_store = Chroma(
        collection_name="job_postings",
        embedding_function=embeddings,
        persist_directory="./chroma_db"
    )

    # 2. Load Content
    loader = WebBaseLoader(job_urls)
    # WebBaseLoader is synchronous
    docs = loader.load()
    
    # 3. Process and Index
    # WebBaseLoader automatically sets 'source' and 'title' in metadata.
    # We can ingest the docs directly.

    if docs:
        print(f"💾 Ingesting {len(docs)} documents...")
        
        # Batching to be gentler on the API
        batch_size = 20
        for i in range(0, len(docs), batch_size):
            batch = docs[i : i + batch_size]
            print(f"  - Processing batch {i//batch_size + 1} ({len(batch)} docs)...")
            try:
                await vector_store.aadd_documents(batch)
            except Exception as e:
                print(f"  ❌ Failed to ingest batch: {e}")
        
        # Verify count
        count = vector_store._collection.count()
        print(f"✅ Ingestion complete! Total documents in DB: {count}")
    else:
        print("⚠️ No content loaded.")

if __name__ == "__main__":
    asyncio.run(ingest_jobs())
