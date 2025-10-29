from pydantic import BaseModel, Field
from typing import Optional
import logging
from datetime import datetime
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from core.config import settings


class DDGSQueryConfig(BaseModel):
    """Schema for DDGS query configuration"""
    query: str = Field(description="Optimized search query")
    region: str = Field(default="us-en", description="Search region")
    safesearch: str = Field(default="moderate", description="Safe search setting")
    timelimit: Optional[str] = Field(default=None, description="Time limit for results")
    max_results: int = Field(default=10, description="Maximum number of results")
    backend: str = Field(default="auto", description="Backend search engine")


class AIBasedDDGSOptimizer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Valid parameter values
        self.valid_regions = [
            'us-en', 'uk-en', 'ca-en', 'au-en', 'de-de', 'fr-fr', 'es-es', 
            'it-it', 'ru-ru', 'cn-zh', 'jp-jp', 'kr-kr', 'in-en', 'br-pt',
            'mx-es', 'ar-es', 'nl-nl', 'se-sv', 'no-no', 'dk-da', 'fi-fi',
            'pl-pl', 'wt-wt'
        ]
        
        self.valid_safesearch = ['on', 'moderate', 'off']
        self.valid_timelimits = ['d', 'w', 'm', 'y', None]
        self.valid_backends = [
            'auto', 'bing', 'brave', 'duckduckgo', 'google', 'mojeek',
            'mullvad_brave', 'mullvad_google', 'yandex', 'yahoo', 'wikipedia'
        ]
        
        # Initialize LLM
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.3
        )
        
        self.parser = JsonOutputParser(pydantic_object=DDGSQueryConfig)
        
    def optimize_query(self, query: str) -> dict:
        """
        Optimize search query using AI
        """
        try:
            current_date = datetime.now().strftime("%Y-%m-%d")
            current_year = datetime.now().year
            
            prompt = ChatPromptTemplate.from_template("""
You are an expert search query optimizer for DuckDuckGo Search (DDGS). Your job is to analyze a user's search query and optimize it for better results by determining the best search parameters.

Current date: {current_date}
Current year: {current_year}

User's original query: "{query}"

Analyze the query and provide optimized search parameters:

1. **query** (string): The optimized search query text
   - Add relevant keywords to improve search results
   - Add current year for recent/news topics
   - Add "review" for shopping/product queries
   - Add "tutorial documentation" for technical queries
   - Use quotes for exact phrases when needed
   - Keep it concise and focused

2. **region** (string): Search region code
   - us-en (USA - default)
   - uk-en (United Kingdom)
   - ca-en (Canada)
   - au-en (Australia)
   - de-de (Germany)
   - fr-fr (France)
   - es-es (Spain)
   - it-it (Italy)
   - jp-jp (Japan)
   - cn-zh (China)
   - in-en (India)
   - wt-wt (Global/International)
   - Choose based on location references in query or use 'us-en' as default

3. **safesearch** (string): Content filtering level
   - "on" - strict filtering (for family-friendly, kids, school content)
   - "moderate" - balanced filtering (default for most queries)
   - "off" - no filtering (for research, technical, academic content)

4. **timelimit** (string or null): Time range for results
   - "d" - last day (for breaking news, "today", "now")
   - "w" - last week (for news, latest, current, recent)
   - "m" - last month (for "this month")
   - "y" - last year (for "this year" or current year mentioned)
   - null - no time limit (for historical, general, or timeless queries)

5. **max_results** (integer): Number of results to return
   - 5 - simple factual queries (definitions, "what is")
   - 10 - default for most queries
   - 15 - how-to guides, tutorials
   - 20 - comparisons, "best of", shopping
   - 50 - research, academic, comprehensive analysis
   - Range: 1-200

6. **backend** (string): Search engine backend
   - "auto" - default, let DDGS choose
   - "wikipedia" - for facts, definitions, history, biography
   - "google" - for comprehensive research
   - "brave" - privacy-focused searches
   - "duckduckgo" - general queries
   - "google,brave" - for research (multiple engines)
   - "google,bing,brave" - for shopping comparisons

{format_instructions}

Respond ONLY with valid JSON. No additional text or explanation.
""")
            
            chain = prompt | self.llm | self.parser
            
            result = chain.invoke({
                "query": query,
                "current_date": current_date,
                "current_year": current_year,
                "format_instructions": self.parser.get_format_instructions()
            })
            
            # Handle both Pydantic model and dict responses
            if hasattr(result, 'dict'):
                result_dict = result.dict()
            else:
                result_dict = result if isinstance(result, dict) else {}
            
            # Validate the result
            validated_result = self._validate_parameters(result_dict)
            
            self.logger.info(f"Query optimized: '{query}' -> {validated_result}")
            return validated_result
            
        except Exception as e:
            self.logger.error(f"AI query optimization failed: {e}")
            return self._fallback_optimization(query)
    
    def _validate_parameters(self, result: dict) -> dict:
        """Validate and sanitize DDGS parameters"""
        validated = {}
        
        # Validate query
        validated['query'] = str(result.get('query', '')).strip()
        if not validated['query']:
            raise ValueError("Query cannot be empty")
        
        # Validate region
        validated['region'] = result.get('region', 'us-en')
        if validated['region'] not in self.valid_regions:
            self.logger.warning(f"Invalid region '{validated['region']}', using 'us-en'")
            validated['region'] = 'us-en'
        
        # Validate safesearch
        validated['safesearch'] = result.get('safesearch', 'moderate')
        if validated['safesearch'] not in self.valid_safesearch:
            self.logger.warning(f"Invalid safesearch '{validated['safesearch']}', using 'moderate'")
            validated['safesearch'] = 'moderate'
        
        # Validate timelimit
        validated['timelimit'] = result.get('timelimit')
        if validated['timelimit'] not in self.valid_timelimits:
            self.logger.warning(f"Invalid timelimit '{validated['timelimit']}', using None")
            validated['timelimit'] = None
        
        # Validate max_results
        max_results = result.get('max_results', 10)
        try:
            max_results = int(max_results)
            validated['max_results'] = max(1, min(200, max_results))
        except (ValueError, TypeError):
            self.logger.warning(f"Invalid max_results '{max_results}', using 10")
            validated['max_results'] = 10
        
        # Validate backend
        backend = result.get('backend', 'auto')
        if ',' in backend:  # Multiple backends
            backends = [b.strip() for b in backend.split(',')]
            valid_combo = all(b in self.valid_backends for b in backends)
            if not valid_combo:
                self.logger.warning(f"Invalid backend combination '{backend}', using 'auto'")
                validated['backend'] = 'auto'
            else:
                validated['backend'] = backend
        else:
            if backend not in self.valid_backends:
                self.logger.warning(f"Invalid backend '{backend}', using 'auto'")
                validated['backend'] = 'auto'
            else:
                validated['backend'] = backend
        
        return validated
    
    def _fallback_optimization(self, query: str) -> dict:
        """Fallback optimization when AI fails"""
        self.logger.warning("Using fallback optimization")
        return {
            "query": query.strip(),
            "region": "us-en",
            "safesearch": "moderate",
            "timelimit": None,
            "max_results": 10,
            "backend": "auto"
        }


def optimize_query(user_query: str) -> dict:
    """Main function to optimize a search query using AI"""
    optimizer = AIBasedDDGSOptimizer()
    return optimizer.optimize_query(user_query)
