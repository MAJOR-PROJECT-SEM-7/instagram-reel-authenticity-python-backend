from typing import Dict, List, Any, Optional
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from core.config import settings
from src.websearchengine.pipeline import pipeline
from fastapi import WebSocket


class ClaimVerificationResult(BaseModel):
    claim: str = Field(description="The original claim being verified")
    can_verify_with_llm: bool = Field(description="Whether this claim can be verified using LLM knowledge alone")
    verification_method: str = Field(description="Either 'llm_knowledge' or 'web_search'")
    authenticity_score: float = Field(description="Score from 0.0 to 1.0 indicating authenticity")
    authenticity_label: str = Field(description="One of: 'True', 'False', 'Partially True', 'Misleading', 'Unverifiable'")
    explanation: str = Field(description="Detailed explanation of the verification")
    evidence_sources: Optional[List[str]] = Field(description="URLs or sources used for verification", default=None)
    confidence: float = Field(description="Confidence level from 0.0 to 1.0")


def create_unverifiable_result(claim: str, error_reason: str) -> Dict[str, Any]:
    """Create a result for claims that cannot be verified."""
    return {
        "claim": claim,
        "can_verify_with_llm": False,
        "verification_method": "error",
        "authenticity_score": 0.5,
        "authenticity_label": "Unverifiable",
        "explanation": f"Unable to verify this claim due to: {error_reason}",
        "evidence_sources": None,
        "confidence": 0.0
    }


async def verify_claim_with_web_search(claim: str, evidence: str, websocket: WebSocket = None) -> Dict[str, Any]:
    """Verify a claim using web search and evidence."""
    try:
        # Use the existing web search pipeline
        search_query = claim
        web_results = await pipeline(search_query, websocket)
        
        if web_results.get("error"):
            # print(f"Web search error: {web_results['error']}")
            return create_unverifiable_result(claim, "Web search failed")
        
        # Now use LLM to analyze the web search results
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.1
        )
        
        parser = JsonOutputParser(pydantic_object=ClaimVerificationResult)
        
        prompt = ChatPromptTemplate.from_template("""
        You are an expert fact-checker. Analyze the following claim using the provided web search evidence.

        Claim: "{claim}"
        Evidence from video: "{evidence}"
        
        Web search results summary: "{web_summary}"
        Web sources: {web_sources}

        Based on the web search evidence, provide a thorough fact-check analysis:
        1. Does the web evidence support or refute the claim?
        2. Are there any contradictions or additional context?
        3. What is the credibility of the sources?

        Respond in valid JSON format with these exact fields:
        {{
            "claim": "{claim}",
            "can_verify_with_llm": false,
            "verification_method": "web_search",
            "authenticity_score": 0.0-1.0,
            "authenticity_label": "True/False/Partially True/Misleading/Unverifiable",
            "explanation": "detailed explanation based on web evidence",
            "evidence_sources": ["list of URLs"],
            "confidence": 0.0-1.0
        }}

        Important: Set verification_method to "web_search" and include the web sources in evidence_sources.
        """)
        
        chain = prompt | llm | parser
        result = chain.invoke({
            "claim": claim,
            "evidence": evidence,
            "web_summary": web_results.get("summary", "No summary available"),
            "web_sources": json.dumps(web_results.get("sources", []))
        })
        
        # Handle both Pydantic model and dict responses
        if hasattr(result, 'dict'):
            result_dict = result.dict()
        else:
            result_dict = result if isinstance(result, dict) else {}
        
        # Ensure all required fields are present
        required_fields = {
            "claim": claim,
            "can_verify_with_llm": False,
            "verification_method": "web_search",
            "authenticity_score": result_dict.get("authenticity_score", 0.5),
            "authenticity_label": result_dict.get("authenticity_label", "Unverifiable"),
            "explanation": result_dict.get("explanation", "Analysis completed using web search evidence"),
            "evidence_sources": web_results.get("sources", []),
            "confidence": result_dict.get("confidence", 0.5)
        }
        
        # Update with actual results, keeping defaults for missing fields
        for key, default_value in required_fields.items():
            if key not in result_dict or result_dict[key] is None:
                result_dict[key] = default_value
                
        return result_dict
        
    except Exception as e:
        # print(f"Error in verify_claim_with_web_search: {e}")
        return create_unverifiable_result(claim, f"Error during web verification: {str(e)}")

