# models.py
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Any, Dict
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Link(BaseModel):
    filename: str
    width: str
    height: str
    videoUrl: str
    success: bool

class VideoAndAudio(BaseModel):
    success: bool
    video: str
    audio: str

class Claim(BaseModel):
    claim: str
    evidence: str
    is_worth_verifying: bool

class Analysis(BaseModel):
    category: str
    claims: List[Claim]
    summary: str
    is_worthy: bool
    why_not_worthy: Optional[str] = None

class Description(BaseModel):
    success: bool
    analysis: Analysis

class IndividualClaim(BaseModel):
    claim: str
    can_verify_with_llm: bool
    verification_method: str
    authenticity_score: float
    authenticity_label: str
    explanation: str
    evidence_sources: Optional[List[str]] = None
    confidence: float

class IfWorthyResponse(BaseModel):
    overall_authenticity: str
    overall_score: float
    summary: str
    recommendation: str
    individual_claims: List[IndividualClaim]

class FinalResponse(BaseModel):
    overall_authenticity: str
    overall_score: float
    summary: str
    recommendation: str
    individual_claims: List[IndividualClaim]
class NotWorthyResponseDetails(BaseModel):
    summary: str
    reason: str
    category: str


class WorthyResponse(BaseModel):
    link: Link
    video_and_audio: VideoAndAudio
    transcription: str
    description: Description
    if_worthy_response: IfWorthyResponse
    final: FinalResponse

class NotWorthyResponse(BaseModel):
    link: Link
    video_and_audio: VideoAndAudio
    transcription: str
    description: Description
    not_worthy_response: NotWorthyResponseDetails
    final: NotWorthyResponseDetails

class Feedback(BaseModel):
    transcript_rating: int
    transcript_feedback: str

    description_rating: int
    description_feedback: str

    worthy_checked_correctly: bool

    not_worthy_reason_rating: int
    not_worthy_reason_feedback: str

    worthy_reason_rating: int
    worthy_reason_feedback: str

    urls_fetched_rating: int
    urls_fetched_feedback: str

    final_rating: int
    final_feedback: str


class FinalResponse(BaseModel):
    user_email: str
    worthy: bool
    feedback: Feedback
    response: WorthyResponse | NotWorthyResponse
    insta_reel_id: str
    created_at: datetime

class EntryCreateRequest(BaseModel):
    worthy: bool
    feedback: Feedback
    response: WorthyResponse | NotWorthyResponse
    insta_reel_id: str

class EntrySummary(BaseModel):
    _id: str
    insta_reel_id: str
    worthy: bool
    created_at: datetime