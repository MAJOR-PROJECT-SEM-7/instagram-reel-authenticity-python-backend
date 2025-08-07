from typing import List, Union
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from core.config import settings


# Initialize the Gemini model (use gemini-pro for best performance)
llm = ChatGoogleGenerativeAI(
    model="gemma-3-12b-it",  # lightweight and fast
    google_api_key=settings.GOOGLE_API_KEY,
    temperature=0.5
)

def summarize_data(text_blocks: List[str], query: str) -> str:
    context = "\n\n".join(text_blocks)

    prompt_template = ChatPromptTemplate.from_template(
        "Summarize the following content based on the query: '{query}'\n\n{context}"
    )
    
    chain = prompt_template | llm
    response = chain.invoke({"query": query, "context": context})
    return response.content
