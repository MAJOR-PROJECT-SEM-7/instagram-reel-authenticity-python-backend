import time
from typing import Dict, Any
from src.modules.getLinkFromUrl import get_link_from_url
from src.modules.downloadAndCompress import download_and_compress_video
from src.modules.getDescription import generate_description_from_video
from src.modules.notWorthyResponse import not_worthy_response
from src.modules.videotoaudio import video_to_text
from src.modules.claimVerification import verify_all_claims

def process_reel(url: str) -> Dict[str, Any]:
    start_time = time.time()
    
    link: dict = get_link_from_url(url)
    print(f"Get link time: {time.time() - start_time:.2f} seconds")
    
    saved_link = download_and_compress_video(link["videoUrl"], link["filename"])
    print(f"Download and compress time: {time.time() - start_time:.2f} seconds")
    
    audio_transcript = video_to_text(saved_link)
    print(f"Audio transcription time: {time.time() - start_time:.2f} seconds")
    
    description = generate_description_from_video(saved_link, audio_transcript)
    print(f"Generate description time: {time.time() - start_time:.2f} seconds")
    
    
    description["audioTranscript"] = audio_transcript
    description["category"] = description.get("analysis").get("category")
    description["analysis"] = description.get("analysis")
    description["isWorthChecking"] = description.get("analysis").get("is_worthy")
    description["claims"] = description.get("analysis").get("claims")
    
    if not description.get("isWorthChecking"):
        description["notWorthyResponse"] = not_worthy_response(description.get("analysis"), description.get("category"))
        print(f"Not worthy response time: {time.time() - start_time:.2f} seconds")
    else:
        # Video is worth verifying - perform claim-by-claim verification
        print("Starting claim verification process...")
        verification_start = time.time()
        
        # Get claims from the analysis
        analysis = description.get("analysis", {})
        claims = analysis.get("claims", [])
        
        if claims:
            # Verify all claims
            verification_result = verify_all_claims(claims)
            description["verificationResult"] = verification_result
            print(f"Claim verification completed in {time.time() - verification_start:.2f} seconds")
        else:
            # No claims found, but video was marked as worth verifying
            description["verificationResult"] = {
                "overall_authenticity": "No Specific Claims Found",
                "overall_score": 0.8,
                "summary": "While this video was identified as potentially worth verifying, no specific factual claims were extracted for verification.",
                "individual_claims": [],
                "recommendation": "The video may contain general information but lacks specific verifiable claims."
            }
            print("No claims found for verification")
    
    print(f"Total processing time: {time.time() - start_time:.2f} seconds")
    return description