from typing import Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from core.config import settings

def can_verify_with_llm(claim: str) -> Dict[str, Any]:
    """Determine if a claim can be verified using LLM knowledge alone."""
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
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
