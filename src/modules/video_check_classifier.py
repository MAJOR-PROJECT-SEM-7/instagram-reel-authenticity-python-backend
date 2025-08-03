
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

def get_video_check_info(description: str) -> dict:
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=0.2
        )

        # Define the output format parser
        parser = JsonOutputParser()

        # Prompt Template
        prompt = PromptTemplate.from_template("""
You are a helpful content categorizer and fact-checking prefilter.

Given the video description below, categorize the type of video and determine if it contains fact-checkable claims worth verifying.

Return your response ONLY in the following JSON format:
{{
  "category": "<one of: advertisement, meme, comedy, news, opinion, political, educational, music video, vlog, dance, tutorial, review, story, inspirational, other>",
  "isWorthChecking": <true or false>
}}

Description:
\"\"\"{description}\"\"\"
""")

        # LangChain runnable chain
        chain = prompt | llm | parser

        # Invoke the chain with input
        result = chain.invoke({"description": description})
        return result

    except Exception as e:
        return {"error": str(e)}
