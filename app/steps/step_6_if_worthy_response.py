from typing import Dict, Any, List
from app.steps.substeps.step_6a_can_llm_check import can_verify_with_llm
from app.steps.substeps.step_6b_check_with_llm import verify_claim_with_llm
from app.steps.substeps.step_6c_check_on_web import verify_claim_with_web_search
from app.steps.substeps.step_6d_generate_overall_results import generate_overall_assessment
from fastapi import WebSocket
import json

async def if_worthy_response(claims: List[Dict[str, Any]],log: bool = False, websocket: WebSocket = None) -> Dict[str, Any]:
    """Generate a response for a worthy video."""
    claim_results = []
    if log:
        print(f'Verifying {len(claims)} claims')
    if websocket:
        await websocket.send_text(json.dumps({"step": "processing", "message": f"Verifying {len(claims)} claims"}))
    for claim in claims:
        if claim['is_worth_verifying']:
            can_llm_verify = can_verify_with_llm(claim['claim'])
            if can_llm_verify['can_verify_with_llm']:
                if log:
                    print(f"Verifying claim: {claim['claim']} with LLM")
                if websocket:
                    await websocket.send_text(json.dumps({"step": "processing", "message": f"Verifying claim: {claim['claim']} with LLM"}))
                claim_result = verify_claim_with_llm(claim['claim'], claim['evidence'])
            else:
                if log:
                    print(f"Verifying claim: {claim['claim']} with web search")
                if websocket:
                    await websocket.send_text(json.dumps({"step": "processing", "message": f"Verifying claim: {claim['claim']} with web search"}))
                claim_result = await verify_claim_with_web_search(claim['claim'], claim['evidence'], websocket)
            claim_results.append(claim_result)
        else:
            if log:
                print(f"Skipping claim: {claim['claim']}")
            claim_results.append({
                "claim": claim.get("claim", ""),
                "can_verify_with_llm": False,
                "verification_method": "skipped",
                "authenticity_score": 1.0,
                "authenticity_label": "Not Verified",
                "explanation": "This claim was deemed not significant enough for verification.",
                "evidence_sources": None,
                "confidence": 1.0
            })
        if websocket:
            truncated_claim = claim['claim'][:100] + "..." if len(claim['claim']) > 100 else claim['claim']
            await websocket.send_text(json.dumps({"step": "success", "message": f"Claim: {truncated_claim} verified with {claim_result['verification_method']}"}))
    if log:
        print(f'Generated {len(claim_results)} claim results')
    overall_assessment = generate_overall_assessment(claim_results)
    if log:
        print(f'Generated overall assessment')
    return overall_assessment



    #         {
    #             "claim": string,
    #             "evidence": string,
    #             "is_worth_verifying": boolean
    #         }
    #     ]