from pydantic import BaseModel, Field
from typing import Optional
import logging
from datetime import datetime


class DDGSQueryConfig(BaseModel):
    """Schema for DDGS query configuration"""
    query: str = Field(description="Optimized search query")
    region: str = Field(default="us-en", description="Search region")
    safesearch: str = Field(default="moderate", description="Safe search setting")
    timelimit: Optional[str] = Field(default=None, description="Time limit for results")
    max_results: Optional[int] = Field(default=10, description="Maximum number of results")
    backend: str = Field(default="auto", description="Backend search engine")


class RuleBasedDDGSOptimizer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Define keyword patterns for different categories
        self.time_sensitive_keywords = [
            'news', 'latest', 'breaking', 'today', 'current', 'recent', 'now',
            '2024', '2025', 'this year', 'this month', 'this week', 'yesterday',
            'update', 'announcement', 'release', 'launched', 'happening'
        ]
        
        self.research_keywords = [
            'research', 'study', 'academic', 'technical', 'analysis', 'paper',
            'journal', 'publication', 'thesis', 'dissertation', 'scientific',
            'peer reviewed', 'methodology', 'experiment', 'data', 'statistics'
        ]
        
        self.how_to_keywords = [
            'how to', 'tutorial', 'guide', 'step by step', 'instructions',
            'learn', 'teach', 'explain', 'show me', 'help me', 'diy'
        ]
        
        self.shopping_keywords = [
            'buy', 'purchase', 'price', 'cost', 'review', 'comparison',
            'best', 'top', 'cheap', 'affordable', 'deal', 'sale', 'discount'
        ]
        
        self.local_keywords = [
            'near me', 'nearby', 'local', 'restaurant', 'hotel', 'store',
            'address', 'location', 'directions', 'map'
        ]
        
        self.technical_keywords = [
            'programming', 'code', 'software', 'development', 'api', 'database',
            'algorithm', 'framework', 'library', 'documentation', 'error', 'bug'
        ]
        
        self.educational_keywords = [
            'definition', 'what is', 'explain', 'meaning', 'history', 'facts',
            'information', 'encyclopedia', 'wiki', 'biography', 'overview'
        ]
        
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
        
    def optimize_query(self, query: str) -> dict:
        """
        Optimize search query using rule-based approach
        """
        try:
            query_lower = query.lower().strip()
            
            # Step 1: Optimize the query text
            optimized_query = self._optimize_query_text(query)
            
            # Step 2: Determine search parameters based on content analysis
            region = self._determine_region(query_lower)
            safesearch = self._determine_safesearch(query_lower)
            timelimit = self._determine_timelimit(query_lower)
            max_results = self._determine_max_results(query_lower)
            backend = self._determine_backend(query_lower)
            
            result = {
                "query": optimized_query,
                "region": region,
                "safesearch": safesearch,
                "timelimit": timelimit,
                "max_results": max_results,
                "backend": backend
            }
            
            # Validate the result
            validated_result = self._validate_parameters(result)
            
            self.logger.info(f"Query optimized: '{query}' -> {validated_result}")
            return validated_result
            
        except Exception as e:
            self.logger.error(f"Query optimization failed: {e}")
            return self._fallback_optimization(query)
    
    def _optimize_query_text(self, query: str) -> str:
        """
        Optimize the query text itself
        """
        query = query.strip()
        
        # Add quotes for exact phrases in how-to queries
        if any(keyword in query.lower() for keyword in ['how to', 'step by step']):
            if 'how to' in query.lower() and '"' not in query:
                query = query.replace('how to', '"how to"')
        
        # Add current year for recent topics
        current_year = str(datetime.now().year)
        if any(keyword in query.lower() for keyword in ['latest', 'current', 'recent', 'news']):
            if current_year not in query:
                query += f" {current_year}"
        
        # Enhance technical queries
        if any(keyword in query.lower() for keyword in self.technical_keywords):
            if 'documentation' not in query.lower() and 'tutorial' not in query.lower():
                query += " tutorial documentation"
        
        # Enhance research queries
        if any(keyword in query.lower() for keyword in self.research_keywords):
            if 'study' not in query.lower() and 'research' not in query.lower():
                query += " research study"
        
        # Add review for shopping queries
        if any(keyword in query.lower() for keyword in ['buy', 'purchase', 'best']):
            if 'review' not in query.lower():
                query += " review"
        
        return query
    
    def _determine_region(self, query_lower: str) -> str:
        """
        Determine appropriate region based on query content
        """
        # Check for location-specific terms
        location_patterns = {
            'uk-en': ['uk', 'britain', 'british', 'england', 'london'],
            'ca-en': ['canada', 'canadian', 'toronto', 'vancouver'],
            'au-en': ['australia', 'australian', 'sydney', 'melbourne'],
            'de-de': ['germany', 'german', 'berlin', 'munich'],
            'fr-fr': ['france', 'french', 'paris', 'lyon'],
            'es-es': ['spain', 'spanish', 'madrid', 'barcelona'],
            'it-it': ['italy', 'italian', 'rome', 'milan'],
            'jp-jp': ['japan', 'japanese', 'tokyo', 'osaka'],
            'cn-zh': ['china', 'chinese', 'beijing', 'shanghai'],
            'in-en': ['india', 'indian', 'mumbai', 'delhi'],
        }
        
        for region, keywords in location_patterns.items():
            if any(keyword in query_lower for keyword in keywords):
                return region
        
        # Global topics
        if any(keyword in query_lower for keyword in ['world', 'global', 'international']):
            return 'wt-wt'
        
        # Default to US English
        return 'us-en'
    
    def _determine_safesearch(self, query_lower: str) -> str:
        """
        Determine safesearch setting based on query content
        """
        # Technical/research queries - less filtering
        if any(keyword in query_lower for keyword in self.research_keywords + self.technical_keywords):
            return 'off'
        
        # Educational content - moderate filtering
        if any(keyword in query_lower for keyword in self.educational_keywords):
            return 'moderate'
        
        # Family-friendly indicators
        family_keywords = ['kids', 'children', 'family', 'school', 'education']
        if any(keyword in query_lower for keyword in family_keywords):
            return 'on'
        
        # Default to moderate
        return 'moderate'
    
    def _determine_timelimit(self, query_lower: str) -> Optional[str]:
        """
        Determine time limit based on query content
        """
        # Breaking news - last day
        if any(keyword in query_lower for keyword in ['breaking', 'today', 'now', 'just happened']):
            return 'd'
        
        # Recent news - last week
        if any(keyword in query_lower for keyword in ['news', 'latest', 'current', 'recent']):
            return 'w'
        
        # This year's content
        current_year = str(datetime.now().year)
        if current_year in query_lower or 'this year' in query_lower:
            return 'y'
        
        # This month's content
        if 'this month' in query_lower:
            return 'm'
        
        # Historical or general queries - no limit
        return None
    
    def _determine_max_results(self, query_lower: str) -> int:
        """
        Determine number of results based on query type
        """
        # Research queries need more results
        if any(keyword in query_lower for keyword in self.research_keywords):
            return 50
        
        # Shopping comparisons need multiple options
        if any(keyword in query_lower for keyword in ['comparison', 'vs', 'best', 'top']):
            return 20
        
        # How-to guides might need several options
        if any(keyword in query_lower for keyword in self.how_to_keywords):
            return 15
        
        # Simple fact-finding queries
        if any(keyword in query_lower for keyword in ['what is', 'definition', 'meaning']):
            return 5
        
        # Local searches
        if any(keyword in query_lower for keyword in self.local_keywords):
            return 10
        
        # Default
        return 10
    
    def _determine_backend(self, query_lower: str) -> str:
        """
        Determine best backend based on query type
        """
        # Wikipedia for educational/factual content
        if any(keyword in query_lower for keyword in self.educational_keywords + ['facts', 'history', 'biography']):
            return 'wikipedia'
        
        # Google for comprehensive research
        if any(keyword in query_lower for keyword in self.research_keywords):
            return 'google,brave'
        
        # Multiple engines for shopping
        if any(keyword in query_lower for keyword in self.shopping_keywords):
            return 'google,bing,brave'
        
        # Technical documentation
        if any(keyword in query_lower for keyword in self.technical_keywords):
            return 'google,duckduckgo'
        
        # Default to auto
        return 'auto'
    
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
            validated['region'] = 'us-en'
        
        # Validate safesearch
        validated['safesearch'] = result.get('safesearch', 'moderate')
        if validated['safesearch'] not in self.valid_safesearch:
            validated['safesearch'] = 'moderate'
        
        # Validate timelimit
        validated['timelimit'] = result.get('timelimit')
        if validated['timelimit'] not in self.valid_timelimits:
            validated['timelimit'] = None
        
        # Validate max_results
        max_results = result.get('max_results', 10)
        try:
            max_results = int(max_results)
            validated['max_results'] = max(1, min(200, max_results))
        except (ValueError, TypeError):
            validated['max_results'] = 10
        
        # Validate backend
        backend = result.get('backend', 'auto')
        if ',' in backend:  # Multiple backends
            backends = [b.strip() for b in backend.split(',')]
            valid_combo = all(b in self.valid_backends for b in backends)
            validated['backend'] = backend if valid_combo else 'auto'
        else:
            validated['backend'] = backend if backend in self.valid_backends else 'auto'
        
        return validated
    
    def _fallback_optimization(self, query: str) -> dict:
        """Fallback optimization when main logic fails"""
        return {
            "query": query.strip(),
            "region": "us-en",
            "safesearch": "moderate",
            "timelimit": None,
            "max_results": 10,
            "backend": "auto"
        }


def optimize_query(user_query: str) -> dict:
    optimizer = RuleBasedDDGSOptimizer()
    return optimizer.optimize_query(user_query)