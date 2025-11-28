from typing import Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from src.core.config import settings

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

        CRITICAL RULES - LLMs CANNOT verify claims about:
        1. **Specific events** - Any claim about something that happened to specific people, at specific places, or at specific times (e.g., "Person X did Y at Z event")
        2. **Recent news or current events** - Anything that happened recently or is ongoing
        3. **Specific statistics or data points** - Exact numbers, prices, dates that need verification
        4. **Personal activities of public figures** - What celebrities, politicians, or public figures did/said recently
        5. **Viral content or trending topics** - Claims about things "going viral" or trending
        6. **Company-specific claims** - Specific actions, announcements, or data about particular companies
        7. **Location-specific information** - Prices, availability, or conditions at specific places

        LLMs CAN verify claims about:
        1. **Universal scientific facts** - Laws of physics, chemistry, biology (e.g., "Water boils at 100°C at sea level")
        2. **Well-established historical facts** - Major historical events with consensus (e.g., "World War II ended in 1945")
        3. **Mathematical truths** - Basic math, logic, established theorems
        4. **General conceptual knowledge** - Definitions, concepts, theories that are well-established
        5. **Common sense reasoning** - Logical deductions from known principles

        EXAMPLES:
        ❌ CANNOT verify with LLM: "Rohit Sharma and his wife danced at her brother's wedding and went viral"
           → Requires web search (specific event about specific people)
        
        ❌ CANNOT verify with LLM: "Company X launched a new product at $299"
           → Requires web search (specific company action and price)
        
        ✅ CAN verify with LLM: "Water is composed of hydrogen and oxygen"
           → General scientific fact
        
        ✅ CAN verify with LLM: "The Earth orbits around the Sun"
           → Well-established scientific fact

        **DEFAULT STANCE**: When in doubt, assume the claim CANNOT be verified with LLM alone. It's better to use web search than to rely on potentially outdated or incomplete LLM knowledge.

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
