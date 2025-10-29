import requests
from core.config import settings
from fastapi import WebSocket
from typing import Dict, Any
import json
import re

async def verify_claim_with_perplexity(claim: str, websocket: WebSocket = None) -> Dict[str, Any]:
    """
    Verify a claim using Perplexity AI as a fallback when web search fails.
    Returns results in the same format as verify_claim_with_web_search.
    """
    try:
        # Set up the API endpoint and headers
        url = "https://api.perplexity.ai/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.PERPLEXITY_KEY}",
            "Content-Type": "application/json"
        }

        # Create a detailed prompt for Perplexity
        prompt = f"""You are an expert fact-checker. Analyze the following claim and provide a detailed fact-check.

Claim: "{claim}"

Provide a thorough fact-check analysis with web-based evidence and respond in valid JSON format with these exact fields:
{{
    "claim": "{claim}",
    "can_verify_with_llm": false,
    "verification_method": "perplexity",
    "authenticity_score": <float between 0.0-1.0>,
    "authenticity_label": "<one of: True, False, Partially True, Misleading, Unverifiable>",
    "explanation": "<detailed explanation based on web evidence with sources>",
    "evidence_sources": ["<list of URLs used for verification>"],
    "confidence": <float between 0.0-1.0>
}}

Important: 
- Provide actual URLs in evidence_sources
- authenticity_score: 1.0 = completely true, 0.0 = completely false, 0.5 = uncertain
- confidence: how confident you are in your assessment
- Include specific facts and sources in your explanation
- Respond ONLY with valid JSON, no additional text"""

        # Define the request payload
        payload = {
            "model": "sonar-pro",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a professional fact-checker that provides responses in valid JSON format only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.1,
            "max_tokens": 2000
        }

        # Send WebSocket update if available
        if websocket:
            await websocket.send_json({
                "type": "status",
                "message": "Using Perplexity AI for verification..."
            })

        # Make the API call
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()

        # Extract the content from response
        response_data = response.json()
        content = response_data["choices"][0]["message"]["content"]

        # Send WebSocket update
        if websocket:
            await websocket.send_json({
                "type": "status",
                "message": "Processing Perplexity response..."
            })

        # Try to extract JSON from the response
        # Sometimes the model might wrap JSON in markdown code blocks
        json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find JSON object directly
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = content

        # Parse the JSON response
        try:
            result = json.loads(json_str)
        except json.JSONDecodeError:
            # If JSON parsing fails, create a structured response from the text
            result = {
                "claim": claim,
                "can_verify_with_llm": False,
                "verification_method": "web_search",
                "authenticity_score": 0.5,
                "authenticity_label": "Unverifiable",
                "explanation": content,
                "evidence_sources": [],
                "confidence": 0.5
            }

        # Ensure all required fields are present with defaults
        required_fields = {
            "claim": claim,
            "can_verify_with_llm": False,
            "verification_method": "web_search",
            "authenticity_score": 0.5,
            "authenticity_label": "Unverifiable",
            "explanation": "No explanation provided",
            "evidence_sources": [],
            "confidence": 0.5
        }

        # Merge result with defaults
        for key, default_value in required_fields.items():
            if key not in result or result[key] is None:
                result[key] = default_value

        # Ensure evidence_sources is a list
        if not isinstance(result.get("evidence_sources"), list):
            result["evidence_sources"] = []

        # Send final WebSocket update
        if websocket:
            await websocket.send_json({
                "type": "status",
                "message": "Verification complete using Perplexity AI"
            })

        return result

    except requests.exceptions.RequestException as e:
        # Handle API request errors
        return create_unverifiable_result(claim, f"Perplexity API request failed: {str(e)}")
    except KeyError as e:
        # Handle missing keys in response
        return create_unverifiable_result(claim, f"Invalid Perplexity API response format: {str(e)}")
    except Exception as e:
        # Handle any other errors
        return create_unverifiable_result(claim, f"Error during Perplexity verification: {str(e)}")