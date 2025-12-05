from typing import List
from pydantic import BaseModel, Field

class MatchResult(BaseModel):
    """The agent's analysis of how well a resume fits a job."""
    job_id: str
    job_title: str
    job_url: str = Field(..., description="The URL to apply for the job")
    match_score: int = Field(..., description="0-100 score indicating fit")
    strengths: List[str] = Field(..., description="Key strengths matching the job requirements")
    reasoning: str = Field(..., description="Why this is a good/bad fit")
    missing_skills: List[str] = Field(..., description="Critical skills the candidate lacks")
    improvement_tips: str = Field(..., description="Actionable advice to improve chances")

class MatchResponse(BaseModel):
    """Structured response containing a list of job matches."""
    matches: List[MatchResult]
 