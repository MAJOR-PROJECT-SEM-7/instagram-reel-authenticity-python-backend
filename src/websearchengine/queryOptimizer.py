from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from core.config import settings

def optimize_query(query: str) -> str:
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemma-3-12b-it",
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.1
        )
        prompt = ChatPromptTemplate.from_template(
            """
You are an assistant that helps optimize queries for web search engines.
Given a user query, rewrite it to be concise, clear, and effective for web search.
Return ONLY the optimized query, nothing else.

User Query: {query}
Optimized Query:
            """
        )
        chain = prompt | llm
        response = chain.invoke({"query": query})
        # If the response is a dict with 'content', extract it, else return as string
        if isinstance(response, dict) and "content" in response:
            return response["content"].strip()
        if hasattr(response, "content"):
            return response.content.strip()
        return str(response).strip()
    except Exception as e:
        # Fallback: just return the original query if optimization fails
        return query
