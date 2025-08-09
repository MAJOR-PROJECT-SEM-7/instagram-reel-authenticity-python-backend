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



class OverallVerificationResult(BaseModel):
    overall_authenticity: str = Field(description="Overall assessment of the reel")
    overall_score: float = Field(description="Overall authenticity score")
    summary: str = Field(description="Well-crafted summary of the verification results")
    individual_claims: List[ClaimVerificationResult] = Field(description="Results for each claim")
    recommendation: str = Field(description="Recommendation for users about this content")


def generate_overall_assessment(claim_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate an overall assessment based on individual claim results."""
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.2
        )
        
        parser = JsonOutputParser(pydantic_object=OverallVerificationResult)
        
        # Calculate overall score
        total_score = sum(result.get("authenticity_score", 0.5) for result in claim_results)
        overall_score = total_score / len(claim_results) if claim_results else 0.5
        
        # Prepare claim summaries for the prompt
        claim_summaries = []
        for result in claim_results:
            claim_summaries.append(f"Claim: {result.get('claim', 'Unknown')}\nLabel: {result.get('authenticity_label', 'Unknown')}\nScore: {result.get('authenticity_score', 0.5)}\nExplanation: {result.get('explanation', 'No explanation')}")
        
        prompt = ChatPromptTemplate.from_template("""
        You are an expert fact-checker providing a final assessment of a social media reel's authenticity.

        Based on the individual claim verification results below, provide an overall assessment:

        Individual Claim Results:
        {claim_summaries}

        Overall Score: {overall_score}

        Provide a comprehensive assessment in valid JSON format:
        {{
            "overall_authenticity": "Overall assessment label",
            "overall_score": {overall_score},
            "summary": "Well-crafted summary explaining the findings",
            "recommendation": "Clear recommendation for users"
        }}
        """)
        
        chain = prompt | llm | parser
        result = chain.invoke({
            "claim_summaries": "\n\n".join(claim_summaries),
            "overall_score": overall_score
        })
        
        # Handle both Pydantic model and dict responses
        if hasattr(result, 'dict'):
            result_dict = result.dict()
        else:
            result_dict = result if isinstance(result, dict) else {}
        
        # Ensure all required fields are present for overall assessment
        required_fields = {
            "overall_authenticity": result_dict.get("overall_authenticity", "Assessment Completed"),
            "overall_score": overall_score,
            "summary": result_dict.get("summary", "Analysis completed based on individual claim verification results."),
            "individual_claims": claim_results,
            "recommendation": result_dict.get("recommendation", "Please review the individual claim results for detailed information.")
        }
        
        # Update with actual results, keeping defaults for missing fields
        for key, default_value in required_fields.items():
            if key not in result_dict or result_dict[key] is None:
                result_dict[key] = default_value
                
        return result_dict
        
    except Exception as e:
        # print(f"Error in generate_overall_assessment: {e}")
        return {
            "overall_authenticity": "Error in Assessment",
            "overall_score": 0.5,
            "summary": f"Unable to generate overall assessment due to error: {str(e)}",
            "individual_claims": claim_results,
            "recommendation": "Unable to provide recommendation due to technical issues."
        }
