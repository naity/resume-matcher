from typing import List, Dict
from langchain_core.tools import tool
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

@tool
async def search_jobs(query: str, top_k: int = 5) -> List[Dict]:
    """
    Search for relevant job postings based on a natural language query.
    Use this tool to find jobs that match the candidate's skills and experience.
    
    Args:
        query: A search string (e.g., "Senior Python Developer with AWS experience")
        top_k: Number of job matches to return (default: 5)
    """
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vector_store = Chroma(
        collection_name="job_postings",
        embedding_function=embeddings,
        persist_directory="./chroma_db"
    )
    
    # Retrieve top k matches
    results = await vector_store.asimilarity_search(query, k=top_k)
    
    # Return structured data for the agent to analyze
    jobs = []
    for doc in results:
        job_info = doc.metadata
        job_info["content"] = doc.page_content # Add full text for analysis
        jobs.append(job_info)
        
    return jobs
