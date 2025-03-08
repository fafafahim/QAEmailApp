// Install the Azure Speech SDK with: npm install microsoft-cognitiveservices-speech-sdk
require('dotenv').config();
const sdk = require("microsoft-cognitiveservices-speech-sdk");
const fs = require("fs");
const path = require("path");

// Use the provided key and extract region from the endpoint (eastus)
const subscriptionKey = process.env.AZURE_SPEECH_SUBSCRIPTION_KEY;
const serviceRegion = process.env.AZURE_SPEECH_SERVICE_REGION; 

// Create a speech configuration using your subscription key and service region
const speechConfig = sdk.SpeechConfig.fromSubscription(subscriptionKey, serviceRegion);
// (Optional) Set a voice name, e.g., "en-US-AriaNeural, en-US-AvaMultilingualNeural, en-US-GuyNeural, en-US-ChristopherNeural"
speechConfig.speechSynthesisVoiceName = "en-US-ChristopherNeural";

// Check and create the output directory before using it
const outputDir = path.join(__dirname, "../output");
if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
}
const outputFile = path.join(outputDir, "speech.wav");

// Create an audio configuration using the output file
const audioConfig = sdk.AudioConfig.fromAudioFileOutput(outputFile);
const synthesizer = new sdk.SpeechSynthesizer(speechConfig, audioConfig);

const text = process.argv[2] || "Hello from Azure TTS!";
const rate = "2"; // You can adjust this value ("1.0" is normal speed, below 1.0 is slower, above 1.0 is faster)

// Wrap your text in SSML with the prosody tag
const ssml = `<speak version="1.0" xml:lang="en-US">
  <voice name="${speechConfig.speechSynthesisVoiceName}">
    <prosody rate="${rate}">
      ${text}
    </prosody>
  </voice>
</speak>`;

synthesizer.speakSsmlAsync(
  ssml,
  (result) => {
    console.log("Speech synthesized to 'output.wav' with rate", rate + ":", text);
    synthesizer.close();
  },
  (err) => {
    console.error(err);
    synthesizer.close();
  }
);