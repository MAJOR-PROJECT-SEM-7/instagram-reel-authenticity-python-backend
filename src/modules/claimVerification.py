from typing import Dict, List, Any, Optional
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from core.config import settings
from src.websearchengine.pipeline import pipeline


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


def can_verify_with_llm(claim: str) -> Dict[str, Any]:
    """Determine if a claim can be verified using LLM knowledge alone."""
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.1
        )
        
        parser = JsonOutputParser()
        
        prompt = ChatPromptTemplate.from_template("""
        You are an expert fact-checker. Analyze the following claim and determine if it can be verified using your existing knowledge alone, or if it requires web search for current/specific information.

        Claim: "{claim}"

        Consider these factors:
        1. Is this about general knowledge, historical facts, scientific principles, a event or news happened in the past or well-established information?
        2. Does it require current events, recent news, specific statistics, or real-time data?
        3. Does it involve specific people, companies, or events that might have recent developments?
        4. Is this a fact or an opinion?

        Respond in JSON format:
        {{
            "can_verify_with_llm": true/false,
            "reasoning": "explanation of why this can or cannot be verified with LLM knowledge alone",
            "verification_complexity": "simple/moderate/complex",
            "requires_current_data": true/false
        }}
        """)
        
        chain = prompt | llm | parser
        result = chain.invoke({"claim": claim})
        
        # Ensure result is a dictionary
        if not isinstance(result, dict):
            return {
                "can_verify_with_llm": False,
                "reasoning": "Unable to parse LLM response",
                "verification_complexity": "complex",
                "requires_current_data": True
            }
        
        return result
        
    except Exception as e:
        # print(f"Error in can_verify_with_llm: {e}")
        return {
            "can_verify_with_llm": False,
            "reasoning": f"Error occurred: {str(e)}",
            "verification_complexity": "complex",
            "requires_current_data": True
        }


def verify_claim_with_llm(claim: str, evidence: str) -> Dict[str, Any]:
    """Verify a claim using LLM knowledge alone."""
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
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


def verify_claim_with_web_search(claim: str, evidence: str) -> Dict[str, Any]:
    """Verify a claim using web search and evidence."""
    try:
        # Use the existing web search pipeline
        search_query = f"fact check verify: {claim}"
        web_results = pipeline(search_query)
        
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


def verify_individual_claim(claim: Dict[str, Any]) -> Dict[str, Any]:
    """Verify a single claim using the appropriate method."""
    claim_text = claim.get("claim", "")
    evidence = claim.get("evidence", "")
    
    if not claim_text:
        return create_unverifiable_result("", "Empty claim provided")
    
    # First, determine if we can verify with LLM alone
    llm_check = can_verify_with_llm(claim_text)
    
    if llm_check.get("can_verify_with_llm", False):
        # print(f"Verifying with LLM: {claim_text}")
        return verify_claim_with_llm(claim_text, evidence)
    else:
        # print(f"Verifying with web search: {claim_text}")
        return verify_claim_with_web_search(claim_text, evidence)


def generate_overall_assessment(claim_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate an overall assessment based on individual claim results."""
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
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


def verify_all_claims(claims: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Main function to verify all claims in a video."""
    if not claims:
        return {
            "overall_authenticity": "No Claims to Verify",
            "overall_score": 1.0,
            "summary": "No factual claims were found in this video that require verification.",
            "individual_claims": [],
            "recommendation": "This content appears to be safe to view as it contains no verifiable claims."
        }
    
    # Verify each claim
    claim_results = []
    for claim in claims:
        if claim.get("is_worth_verifying", False):
            result = verify_individual_claim(claim)
            claim_results.append(result)
        else:
            # Skip claims not worth verifying but add them to results
            claim_results.append({
                "claim": claim.get("claim", ""),
                "can_verify_with_llm": False,
                "verification_method": "skipped",
                "authenticity_score": 1.0,
                "authenticity_label": "Not Verified",
                "explanation": "This claim was deemed not significant enough for verification.",
                "evidence_sources": None,
                "confidence": 1.0
            })
    
    # Generate overall assessment
    overall_result = generate_overall_assessment(claim_results)
    
    return overall_result
