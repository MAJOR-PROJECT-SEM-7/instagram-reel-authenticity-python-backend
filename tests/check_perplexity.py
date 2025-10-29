import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.steps.substeps.step_6e_verify_claim_with_perplexity import verify_claim_with_perplexity
import asyncio
async def test_verify_claim_with_perplexity():
    claim = "The development of the Chroma AI model was funded by money from people online and the creator's own savings."
    result = await verify_claim_with_perplexity(claim)
    print(result)

if __name__ == "__main__":
    asyncio.run(test_verify_claim_with_perplexity())