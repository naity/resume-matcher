import asyncio
from dotenv import load_dotenv
from src.tools import search_jobs

load_dotenv()

async def test_search():
    print("🔍 Testing search_jobs tool (top_k=3)...")
    results = await search_jobs.ainvoke({"query": "Software Engineer in Seattle", "top_k": 3})
    
    print(f"✅ Found {len(results)} matches!")
    for i, job in enumerate(results):
        print(f"\n--- Result {i+1} ---")
        print(f"URL: {job.get('source', 'Unknown')}")
        print(f"Title: {job.get('title', 'N/A')}")

if __name__ == "__main__":
    asyncio.run(test_search())
