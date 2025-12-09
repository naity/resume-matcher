import asyncio
from dotenv import load_dotenv
from typing import List, Dict, Union, Optional
from langchain_core.tools import tool
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

@tool
async def search_jobs(query: str, top_k: int = 5, where_document: Optional[Union[str, Dict]] = None) -> List[Dict]:
    """
    Search for relevant job postings based on a natural language query.
    Use this tool to find jobs that match the candidate's skills and experience.
    
    Args:
        query: A search string (e.g., "Senior Python Developer with AWS experience")
        top_k: Number of job matches to return (default: 5)
        where_document: Optional filter for the document content.
                        - If a string is provided, it performs a case-sensitive "$contains" search.
                        - If a dictionary is provided, it is passed directly as the Chroma `where_document` filter.
                          You can use logical operators like "$and" and "$or".
                          Example: {"$and": [{"$contains": "Remote"}, {"$contains": "Python"}]}
    """
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vector_store = Chroma(
        collection_name="job_postings",
        embedding_function=embeddings,
        persist_directory="./chroma_db"
    )
    
    # Retrieve top k matches
    search_kwargs = {}
    if where_document:
        if isinstance(where_document, str):
            search_kwargs["where_document"] = {"$contains": where_document}
        else:
            search_kwargs["where_document"] = where_document

    results = await vector_store.asimilarity_search(query, k=top_k, **search_kwargs)
    
    # Return structured data for the agent to analyze
    jobs = []
    for doc in results:
        job_info = doc.metadata
        job_info["content"] = doc.page_content # Add full text for analysis
        jobs.append(job_info)
        
    return jobs

if __name__ == "__main__":
    load_dotenv()
    
    async def test_search():
        print("🔍 Testing search_jobs tool (top_k=3)...")
        results = await search_jobs.ainvoke({"query": "Software Engineer in Seattle", "top_k": 3})
        
        print(f"✅ Found {len(results)} matches!")
        for i, job in enumerate(results):
            print(f"\n--- Result {i+1} ---")
            print(f"URL: {job.get('source', 'Unknown')}")
            print(f"Title: {job.get('title', 'N/A')}")
            
        print("\n🔍 Testing hybrid search (where_document='Python')...")
        results_hybrid = await search_jobs.ainvoke({
            "query": "Software Engineer", 
            "top_k": 3,
            "where_document": "Python"
        })
        print(f"✅ Found {len(results_hybrid)} matches with 'Python'!")

        print("\n🔍 Testing complex hybrid search (where_document with $and)...")
        # Example: Must contain "Python" AND "Seattle"
        complex_filter = {
            "$and": [
                {"$contains": "Python"},
                {"$contains": "Seattle"}
            ]
        }
        results_complex = await search_jobs.ainvoke({
            "query": "Software Engineer", 
            "top_k": 3,
            "where_document": complex_filter
        })
        print(f"✅ Found {len(results_complex)} matches with 'Python' AND 'Seattle'!")
        for job in results_complex:
             print(f"  - {job.get('title', 'N/A')}")

    asyncio.run(test_search())
