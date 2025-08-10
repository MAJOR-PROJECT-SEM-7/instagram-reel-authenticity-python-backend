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
        prompt = ChatPromptTemplate.from_template("""
You are an assistant that rewrites user queries for DuckDuckGo to get the most relevant, recent results.
Rules:
- Keep exact names, places, and key facts from the original query.
- Add words like 'news', 'latest', or 'breaking' if the query is about an event.
- Remove unrelated words that do not help in search.
- Return ONLY the optimized query.

User Query: {query}
Optimized Query:
        """)

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
