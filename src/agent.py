import asyncio
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain.agents.structured_output import ProviderStrategy
from src.tools import search_jobs
from src.models import MatchResponse

load_dotenv()

# System Prompt
SYSTEM_PROMPT = """You are an expert Career Coach and Technical Recruiter.
Your goal is to help a candidate find the best job matches from our database.

Process:
1. Analyze the candidate's resume.
2. Search for relevant jobs using `search_jobs`. Call it multiple times if needed.
3. Analyze the top matches against the resume.
4. Select the top 3 best fits.
5. Generate a detailed analysis for each.
"""

def get_agent():
    """Creates and returns the Career Coach agent."""
    llm = ChatOpenAI(model="gpt-5-mini", temperature=0)
    
    agent = create_agent(
        model=llm,
        tools=[search_jobs],
        system_prompt=SYSTEM_PROMPT,
        response_format=ProviderStrategy(MatchResponse)
    )
    return agent

if __name__ == "__main__":
    async def main():
        print("🤖 Initializing Agent...")
        agent = get_agent()
        
        resume_text = """
        John Doe
        Senior Software Engineer
        Skills: Python, AWS, Docker, Kubernetes, FastAPI, React
        Experience: 5 years building cloud-native applications.
        """
        
        print("🚀 Running Agent with sample resume...")
        # The agent expects a "messages" key with the conversation history
        # We start with the user's resume
        result = await agent.ainvoke({
            "messages": [{"role": "user", "content": f"Here is my resume:\n{resume_text}"}]
        })
        
        # The result will contain 'structured_response' because we used ProviderStrategy
        structured_data: MatchResponse = result["structured_response"]
        
        print(f"\n✅ Found {len(structured_data.matches)} matches:\n")
        for match in structured_data.matches:
            print(f"🔹 {match.job_title} (Score: {match.match_score})")
            print(f"   Reasoning: {match.reasoning}")
            print(f"   Strengths: {match.strengths}")
            print("-" * 40)

    asyncio.run(main())
