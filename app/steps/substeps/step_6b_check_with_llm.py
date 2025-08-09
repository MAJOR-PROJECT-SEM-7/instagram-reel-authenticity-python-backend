from typing import Dict, List, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from core.config import settings


class ClaimVerificationResult(BaseModel):
    claim: str = Field(description="The original claim being verified")
    can_verify_with_llm: bool = Field(description="Whether this claim can be verified using LLM knowledge alone")
    verification_method: str = Field(description="Either 'llm_knowledge' or 'web_search'")
    authenticity_score: float = Field(description="Score from 0.0 to 1.0 indicating authenticity")
    authenticity_label: str = Field(description="One of: 'True', 'False', 'Partially True', 'Misleading', 'Unverifiable'")
    explanation: str = Field(description="Detailed explanation of the verification")
    evidence_sources: Optional[List[str]] = Field(description="URLs or sources used for verification", default=None)
    confidence: float = Field(description="Confidence level from 0.0 to 1.0")



def verify_claim_with_llm(claim: str, evidence: str) -> Dict[str, Any]:
    """Verify a claim using LLM knowledge alone."""
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.1
        )
        
        parser = JsonOutputParser(pydantic_object=ClaimVerificationResult)
        
        prompt = ChatPromptTemplate.from_template("""
        You are an expert fact-checker with access to extensive knowledge. Verify the following claim using your existing knowledge.

        Claim: "{claim}"
        Evidence from video: "{evidence}"

        Provide a thorough fact-check analysis. Consider:
        1. Is the claim factually accurate based on established knowledge?
        2. Is there any misleading information or context missing?
        3. Are there any logical fallacies or misrepresentations?

        Respond in valid JSON format with these exact fields:
        {{
            "claim": "{claim}",
            "can_verify_with_llm": true,
            "verification_method": "llm_knowledge",
            "authenticity_score": 0.0-1.0,
            "authenticity_label": "True/False/Partially True/Misleading/Unverifiable",
            "explanation": "detailed explanation",
            "evidence_sources": null,
            "confidence": 0.0-1.0
        }}

        Important: Set verification_method to "llm_knowledge" and evidence_sources to null since you're using internal knowledge.
        """)
        
        chain = prompt | llm | parser
        result = chain.invoke({
            "claim": claim,
            "evidence": evidence
        })
        
        # Handle both Pydantic model and dict responses
        if hasattr(result, 'dict'):
            result_dict = result.dict()
        else:
            result_dict = result if isinstance(result, dict) else {}
        
        # Ensure all required fields are present
        required_fields = {
            "claim": claim,
            "can_verify_with_llm": True,
            "verification_method": "llm_knowledge",
            "authenticity_score": result_dict.get("authenticity_score", 0.5),
            "authenticity_label": result_dict.get("authenticity_label", "Unverifiable"),
            "explanation": result_dict.get("explanation", "Analysis completed using LLM knowledge"),
            "evidence_sources": None,
            "confidence": result_dict.get("confidence", 0.5)
        }
        
        # Update with actual results, keeping defaults for missing fields
        for key, default_value in required_fields.items():
            if key not in result_dict or result_dict[key] is None:
                result_dict[key] = default_value
                
        return result_dict
        
    except Exception as e:
        # print(f"Error in verify_claim_with_llm: {e}")
        return {
            "claim": claim,
            "can_verify_with_llm": True,
            "verification_method": "llm_knowledge",
            "authenticity_score": 0.5,
            "authenticity_label": "Unverifiable",
            "explanation": f"Error occurred during verification: {str(e)}",
            "evidence_sources": None,
            "confidence": 0.0
        }
