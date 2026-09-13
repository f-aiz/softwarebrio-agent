from pydantic import BaseModel, Field
from typing import List, Optional

class TeamMember(BaseModel):
    name: str = Field(..., description="Full name of the team member")
    role: str = Field(..., description="Job title or role")
    linkedin_url: Optional[str] = Field(None, description="LinkedIn profile URL if available")

class CompanyIntelligence(BaseModel):
    domain: str
    company_overview: str = Field(..., description="A concise 2-sentence summary of what the company does.")
    target_audience: str = Field(..., description="Who their product is built for (ICP).")
    contact_points: List[str] = Field(default_factory=list, description="Public emails found (e.g., contact@, sales@).")
    leadership: List[TeamMember] = Field(default_factory=list, description="Key leadership or team members found.")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Estimated score (0.0-1.0) indicating data completeness.")