from app.steps.step_1_get_url_from_link import get_link_from_url
from app.steps.step_2_save_video_and_audio_locally import save_video_and_audio_locally
from app.steps.step_3_get_audio_transcription import audio_to_text
from app.steps.step_4_get_video_analysis import generate_description_from_video
from app.steps.step_5_if_not_worthy_response import not_worthy_response
from app.steps.step_6_if_worthy_response import if_worthy_response
import json

def check_authenticity(url: str, log: bool = False):
    if log:
        results = {}

    # get the link from the url
    if log:
        print("Getting link from url")
    link = get_link_from_url(url)
    if log:
        results['link'] = link
        if link.get('success'):
            print("Link found")
        else:
            print("Link not found")
    if not link.get('success'):
        if log:
            results['final'] = link
            return results
        return link

    # save the video and audio locally
    if log:
        print("Saving video and audio locally")
    video_and_audio = save_video_and_audio_locally(link['videoUrl'], link['filename'], log)
    if log:
        results['video_and_audio'] = video_and_audio
        if video_and_audio.get('success'):
            print("Video and audio saved locally")
        else:
            print("Failed to save video and audio locally")
    if not video_and_audio.get('success'):
        if log:
            results['final'] = video_and_audio
            return results
        return video_and_audio

    # get the transcription of the audio
    if log:
        print("Getting transcription of audio")
    transcription = audio_to_text(video_and_audio['audio'])
    if log:
        results['transcription'] = transcription
        if transcription:
            print("Transcription generated")
        else:
            print("Failed to get transcription")
    if not transcription:
        fail_msg = {'success': False, 'message': 'Failed to get transcription'}
        if log:
            results['final'] = fail_msg
            return results
        return fail_msg

    # get the analysis of the video
    if log:
        print("Getting analysis of video")
    description = generate_description_from_video(video_and_audio['video'], transcription)
    if log:
        results['description'] = description
        if description.get('success'):
            print("Analysis generated")
        else:
            print("Failed to get analysis")
    if not description.get('success'):
        fail_msg = {'success': False, 'message': 'Failed to get description'}
        if log:
            results['final'] = fail_msg
            return results
        return fail_msg

    # if the video is not worthy, get the not worthy response
    if not description['analysis']['is_worthy']:
        if log:
            print("Video is not worthy")
        not_worthy_response_data = not_worthy_response(description['analysis'], description['analysis']['category'])
        if log:
            print("Not worthy response generated")
            results['not_worthy_response'] = not_worthy_response_data
            results['final'] = not_worthy_response_data
            return {'worthy': False, 'response': results}
        return {'worthy': False, 'response': not_worthy_response_data}

    # if the video is worthy, get the if worthy response
    if log:
        print("Video is worthy")
    if_worthy_response_data = if_worthy_response(description['analysis']['claims'], log)
    if log:
        print("If worthy response generated")
        results['if_worthy_response'] = if_worthy_response_data
        results['final'] = if_worthy_response_data
        return {'worthy': True, 'response': results}
    return {'worthy': True, 'response': if_worthy_response_data}


async def check_authenticity_websocket(websocket, url: str):
    """
    WebSocket version of check_authenticity that sends progress updates
    """
    try:
        # get the link from the url
        await websocket.send_text(json.dumps({"step": "getting_link", "message": "Getting link from url"}))
        
        link = get_link_from_url(url)
        
        if link['success']:
            await websocket.send_text(json.dumps({"step": "link_found", "message": "Link found"}))
        else:
            await websocket.send_text(json.dumps({"step": "link_not_found", "message": "Link not found"}))
            await websocket.send_text(json.dumps({"step": "error", "data": link}))
            return
        
        if not link['success']:
            await websocket.send_text(json.dumps({"step": "error", "data": link}))
            return
        
        # save the video and audio locally
        await websocket.send_text(json.dumps({"step": "saving_media", "message": "Saving video and audio locally"}))
        
        video_and_audio = save_video_and_audio_locally(link['videoUrl'], link['filename'], False)
        
        if video_and_audio['success']:
            await websocket.send_text(json.dumps({"step": "media_saved", "message": "Video and audio saved locally"}))
        else:
            await websocket.send_text(json.dumps({"step": "media_save_failed", "message": "Failed to save video and audio locally"}))
            await websocket.send_text(json.dumps({"step": "error", "data": video_and_audio}))
            return
        
        if not video_and_audio['success']:
            await websocket.send_text(json.dumps({"step": "error", "data": video_and_audio}))
            return
        
        # get the transcription of the audio
        await websocket.send_text(json.dumps({"step": "transcribing", "message": "Getting transcription of audio"}))
        
        transcription = audio_to_text(video_and_audio['audio'])
        
        if transcription:
            await websocket.send_text(json.dumps({"step": "transcription_generated", "message": "Transcription generated"}))
        else:
            await websocket.send_text(json.dumps({"step": "transcription_failed", "message": "Failed to get transcription"}))
            await websocket.send_text(json.dumps({"step": "error", "data": {'success': False, 'message': 'Failed to get transcription'}}))
            return
        
        if not transcription:
            await websocket.send_text(json.dumps({"step": "error", "data": {'success': False, 'message': 'Failed to get transcription'}}))
            return
        
        # get the analysis of the video
        await websocket.send_text(json.dumps({"step": "analyzing_video", "message": "Getting analysis of video"}))
        
        description = generate_description_from_video(video_and_audio['video'], transcription)
        
        if description['success']:
            await websocket.send_text(json.dumps({"step": "analysis_generated", "message": "Analysis generated"}))
        else:
            await websocket.send_text(json.dumps({"step": "analysis_failed", "message": "Failed to get analysis"}))
            await websocket.send_text(json.dumps({"step": "error", "data": {'success': False, 'message': 'Failed to get description'}}))
            return
        
        if not description['success']:
            await websocket.send_text(json.dumps({"step": "error", "data": {'success': False, 'message': 'Failed to get description'}}))
            return
        
        # if the video is not worthy, get the not worthy response
        if not description['analysis']['is_worthy']:
            await websocket.send_text(json.dumps({"step": "not_worthy", "message": "Video is not worthy"}))
            
            not_worthy_response_data = not_worthy_response(description['analysis'], description['analysis']['category'])
            
            await websocket.send_text(json.dumps({"step": "not_worthy_response_generated", "message": "Not worthy response generated"}))
            await websocket.send_text(json.dumps({"step": "completed", "data": not_worthy_response_data}))
            return
        
        # if the video is worthy, get the if worthy response
        await websocket.send_text(json.dumps({"step": "worthy", "message": "Video is worthy"}))
        
        if_worthy_response_data = if_worthy_response(description['analysis']['claims'], False)
        
        await websocket.send_text(json.dumps({"step": "worthy_response_generated", "message": "If worthy response generated"}))
        await websocket.send_text(json.dumps({"step": "completed", "data": if_worthy_response_data}))
        
    except Exception as e:
        await websocket.send_text(json.dumps({"step": "error", "message": f"An error occurred: {str(e)}"}))
