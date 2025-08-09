from app.steps.step_1_get_url_from_link import get_link_from_url
from app.steps.step_2_save_video_and_audio_locally import save_video_and_audio_locally
from app.steps.step_3_get_audio_transcription import audio_to_text
from app.steps.step_4_get_video_analysis import generate_description_from_video
from app.steps.step_5_if_not_worthy_response import not_worthy_response
from app.steps.step_6_if_worthy_response import if_worthy_response

def check_authenticity(url: str,log: bool = False):
    # get the link from the url
    if log:
        print("Getting link from url")
    link = get_link_from_url(url)
    if log:
        if link['success']:
            print("Link found")
        else:
            print("Link not found")
    # """
    # if success:
    # {'filename': string, 'width': number, 'height': number, 'videoUrl': string , 'success': True}
    # if not success:
    # {'success': 'false', 'message': 'error message'}
    # """
    if not link['success']:
        return link
    
    # save the video and audio locally
    if log:
        print("Saving video and audio locally")
    video_and_audio = save_video_and_audio_locally(link['videoUrl'], link['filename'],log)
    if log:
        if video_and_audio['success']:
            print("Video and audio saved locally")
        else:
            print("Failed to save video and audio locally")
    # """
    # if success:
    # {'video': string, 'audio': string, 'success': True}
    # if not success:
    # {'success': 'False'}
    # """
    if not video_and_audio['success']:
        return video_and_audio
    
    # get the transcription of the audio
    if log:
        print("Getting transcription of audio")
    transcription = audio_to_text(video_and_audio['audio'])
    if log:
        if transcription:
            print("Transcription generated")
        else:
            print("Failed to get transcription")
    if not transcription:
        return {'success': False, 'message': 'Failed to get transcription'}
    
    # get the analysis of the video
    if log:
        print("Getting analysis of video")
    description = generate_description_from_video(video_and_audio['video'], transcription)
    if log:
        if description['success']:
            print("Analysis generated")
        else:
            print("Failed to get analysis")
    # """
    # if success:
    # {'success': True, 'analysis':
    # {
    #     "category": string,
    #     "claims": [
    #         {
    #             "claim": string,
    #             "evidence": string,
    #             "is_worth_verifying": boolean
    #         }
    #     ],
    #     "summary": string,
    #     "is_worthy": boolean,
    #     "why_not_worthy": string
    # }
    # }
    # if not success:
    # {'success': 'False'}
    # """
    if not description['success']:
        return {'success': False, 'message': 'Failed to get description'}
    
    # if the video is not worthy, get the not worthy response
    if not description['analysis']['is_worthy']:
        if log:
            print("Video is not worthy")
        not_worthy_response_data = not_worthy_response(description['analysis'], description['analysis']['category'])
        if log:
            print("Not worthy response generated")
        return not_worthy_response_data
    
    # if the video is worthy, get the if worthy response
    if log:
        print("Video is worthy")
    if_worthy_response_data = if_worthy_response(description['analysis']['claims'],log)
    if log:
        print("If worthy response generated")
    return if_worthy_response_data
    # return the description

    









