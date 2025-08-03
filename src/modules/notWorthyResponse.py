from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

def not_worthy_response(description: str, category: str) -> dict:
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=0.3
        )
        parser = JsonOutputParser()

        prompt = PromptTemplate.from_template("""
        You are an assistant that helps summarize light or entertaining content that is not worth fact-checking.

        Given a detailed video description and its category, generate a clear and short summary of the video meant for end users.
        Also explain in one line why it's not fact-checkable content.

        Output ONLY in the following JSON format:
        {{
        "summary": "<core message of the video in simple terms>",
        "reason": "<why it doesn't require fact-checking>",
        "category": "{category}"
        }}

        Description:
        \"\"\"{description}\"\"\"
        """)
        chain = prompt | llm | parser
        result = chain.invoke({"description": description, "category": category})
        return result

    except Exception as e:
        return {
            "error": str(e),
            "fallback": {
                "summary": "This is a general entertainment video.",
                "reason": "No factual claims are made in this type of content.",
                "category": category
            }
        }
