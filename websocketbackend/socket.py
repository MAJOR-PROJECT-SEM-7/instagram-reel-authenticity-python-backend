from fastapi import WebSocket
from app.steps.step_1_get_url_from_link import get_link_from_url
from app.steps.step_2_save_video_and_audio_locally import save_video_and_audio_locally
from app.steps.step_3_get_audio_transcription import audio_to_text
from app.steps.step_4_get_video_analysis import generate_description_from_video
from src.modules.notWorthyResponse import not_worthy_response
from app.steps.step_6_if_worthy_response import if_worthy_response
import json

async def websocket_backend(websocket: WebSocket, url: str):
    try:
        await websocket.send_text(json.dumps({"step": "processing", "message": "Extracting link from url"}))
        link = get_link_from_url(url)
        if not link.get('success'):
            await websocket.send_text(json.dumps({"step": "error", "message": "Invalid URL"}))
            await websocket.close()
            return
        else:
            await websocket.send_text(json.dumps({"step": "success", "message": "Extracted link from url"}))
        
        await websocket.send_text(json.dumps({"step": "processing", "message": "Saving video and audio locally"}))
        video_and_audio = save_video_and_audio_locally(link['videoUrl'], link['filename']) 
        if not video_and_audio.get('success'):
            await websocket.send_text(json.dumps({"step": "error", "message": "Failed to save video and audio locally"}))
            await websocket.close()
            return
        else:
            await websocket.send_text(json.dumps({"step": "success", "message": "Video and audio saved locally"}))
        
        await websocket.send_text(json.dumps({"step": "processing", "message": "Getting audio transcription"}))
        audio_transcription = audio_to_text(video_and_audio['audio'])
        if not audio_transcription:
            await websocket.send_text(json.dumps({"step": "warning", "message": "Failed to get audio transcription, proceeding with video analysis"}))
        await websocket.send_text(json.dumps({"step": "success", "message": "Audio transcription generated"}))
        
        await websocket.send_text(json.dumps({"step": "processing", "message": "Generating video analysis"}))
        video_analysis = generate_description_from_video(video_and_audio['video'], audio_transcription)
        if not video_analysis.get('success'):
            await websocket.send_text(json.dumps({"step": "error", "message": "Failed to generate video analysis"}))
            await websocket.close()
            return
        else:
            await websocket.send_text(json.dumps({"step": "success", "message": "Video analysis generated"}))
        
        if not video_analysis['analysis']['is_worthy']:
            await websocket.send_text(json.dumps({"step": "success", "message": "There is no claim that is worth verifying"}))
            not_worthy_response_data = not_worthy_response(video_analysis['analysis'], video_analysis['analysis']['category'])
            await websocket.send_text(json.dumps({"step": "completed","success": False, "message": "Not worthy response generated" , "response": not_worthy_response_data}))
            await websocket.close()
            return
        else:
            await websocket.send_text(json.dumps({"step": "success", "message": f"There are {len(video_analysis['analysis']['claims'])} claims made in the video"}))
            if_worthy_response_data = await if_worthy_response(video_analysis['analysis']['claims'], websocket=websocket)
            await websocket.send_text(json.dumps({"step": "completed", "success": True, "message": "If worthy response generated" , "response": if_worthy_response_data}))
            await websocket.close()
            return
    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        try:
            await websocket.send_text(json.dumps({"step": "error", "message": error_message}))
        except:
            pass
        try:
            await websocket.close()
        except:
            pass

    