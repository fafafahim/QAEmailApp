import os
import azure.cognitiveservices.speech as speechsdk

# Ensure you have installed the module via: pip install azure-cognitiveservices-speech

# This example requires environment variables named "AZURE_SPEECH_SUBSCRIPTION_KEY" and "AZURE_SPEECH_SERVICE_REGION"
subscription_key = os.environ.get("AZURE_SPEECH_SUBSCRIPTION_KEY")
region = os.environ.get("AZURE_SPEECH_SERVICE_REGION")
if region:
    region = region.strip()
if not subscription_key or not region:
    raise Exception("Missing AZURE_SPEECH_SUBSCRIPTION_KEY or AZURE_SPEECH_SERVICE_REGION environment variables.")

speech_config = speechsdk.SpeechConfig(subscription=subscription_key, region=region)
audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)

# The neural multilingual voice can speak different languages based on the input text.
speech_config.speech_synthesis_voice_name = 'en-US-AvaMultilingualNeural'

speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

# Get text from the console and synthesize to the default speaker.
print("Enter some text that you want to speak >")
text = input()

speech_synthesis_result = speech_synthesizer.speak_text_async(text).get()

if speech_synthesis_result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
    print("Speech synthesized for text [{}]".format(text))
elif speech_synthesis_result.reason == speechsdk.ResultReason.Canceled:
    cancellation_details = speech_synthesis_result.cancellation_details
    print("Speech synthesis canceled: {}".format(cancellation_details.reason))
    if cancellation_details.reason == speechsdk.CancellationReason.Error:
        if cancellation_details.error_details:
            print("Error details: {}".format(cancellation_details.error_details))
            print("Did you set the speech resource key and region values?")
