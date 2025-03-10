import os
import azure.cognitiveservices.speech as speechsdk

def synthesize(text, voice, rate, output_file=None):
    # Fetch credentials at call time
    subscription_key = os.environ.get("AZURE_SPEECH_SUBSCRIPTION_KEY")
    region = os.environ.get("AZURE_SPEECH_SERVICE_REGION")
    if region:
        region = region.strip()
    if not subscription_key or not region:
        raise Exception("Missing AZURE_SPEECH_SUBSCRIPTION_KEY or AZURE_SPEECH_SERVICE_REGION environment variables.")
    
    # Normalize rate to ensure it ends with '%'
    rate = rate.strip()
    if not rate.endswith("%"):
        rate += "%"
    
    speech_config = speechsdk.SpeechConfig(subscription=subscription_key, region=region)
    speech_config.speech_synthesis_voice_name = voice
    if output_file:
        audio_config = speechsdk.audio.AudioOutputConfig(filename=output_file)
    else:
        audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    
    ssml = f"""
<speak version='1.0' xml:lang='en-US'>
    <voice name='{voice}'>
        <prosody rate="{rate}">
            {text}
        </prosody>
    </voice>
</speak>
"""
    result = synthesizer.speak_ssml_async(ssml).get()
    return result
