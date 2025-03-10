import os
import json
from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for
from dotenv import load_dotenv
from subprocess import check_output, CalledProcessError
import werkzeug

# Load environment variables from .env
load_dotenv()

########################################
# JSON file helpers: load and save records
########################################
# Define file locations (these replace hardcoded JSON_FILES and QA_JSON_FILE)
MAIN_JSON_FILE = os.path.join("output", "5html_converted_content.json")
FEEDBACK_JSON_FILE = os.path.join("output", "6email_feedback.json")

def load_records(template):
    # Force using "index.html"
    json_file = MAIN_JSON_FILE
    print("Loading JSON from:", json_file)  # Debug line
    if os.path.exists(json_file):
        with open(json_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_records(template, records):
    json_file = MAIN_JSON_FILE
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=4, ensure_ascii=False)

def load_feedback_records():
    if os.path.exists(FEEDBACK_JSON_FILE):
        with open(FEEDBACK_JSON_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_feedback_records(records):
    with open(FEEDBACK_JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=4, ensure_ascii=False)

########################################
# Flask App & Routes
########################################
app = Flask(__name__)

# Serve output folder files
@app.route('/output/<path:filename>')
def serve_output(filename):
    output_dir = os.path.join(app.root_path, '../output')
    return send_from_directory(output_dir, filename)

# Main UI route with template selection
@app.route("/")
@app.route("/<template>")
def index(template="index.html"):
    records = load_records("index.html")
    return render_template("index.html", records=records)

# Auto-update endpoint for live changes in record fields
@app.route("/update_record", methods=["POST"])
def update_record():
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No data received."}), 400

    record_index = data.get("index")
    updated_record = data.get("record")  # Expecting record as a complete object following your schema

    if not updated_record:
        return jsonify({"status": "error", "message": "No record provided."}), 400

    try:
        idx = int(record_index)
    except (ValueError, TypeError):
        return jsonify({"status": "error", "message": "Invalid record index."}), 400

    records = load_records("index.html")
    if idx < 0 or idx >= len(records):
        return jsonify({"status": "error", "message": "Record index out of range."}), 400

    # Replace the record completely with the updated record
    records[idx] = updated_record
    save_records("index.html", records)
    return jsonify({"status": "success", "message": "Record updated successfully."})

@app.route("/update_feedback", methods=["POST"])
def update_feedback():
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No data received."}), 400

    record_index = data.get("index")
    updated_record = data.get("record")
    if not updated_record:
        return jsonify({"status": "error", "message": "No record provided."}), 400

    try:
        idx = int(record_index)
    except (ValueError, TypeError):
        return jsonify({"status": "error", "message": "Invalid record index."}), 400

    records = load_feedback_records()
    if idx < 0 or idx >= len(records):
        return jsonify({"status": "error", "message": "Record index out of range."}), 400

    records[idx] = updated_record
    save_feedback_records(records)
    return jsonify({"status": "success", "message": "QA feedback updated successfully."})

@app.route("/synthesizeSpeech", methods=["POST"])
def synthesize_speech():
    data = request.get_json()
    text = data.get("text", "Hello from Azure TTS!")
    try:
        import azure.cognitiveservices.speech as speechsdk
        # Use the correct variable names from .env
        subscription_key = os.environ.get("AZURE_SPEECH_SUBSCRIPTION_KEY")
        region = os.environ.get("AZURE_SPEECH_SERVICE_REGION")
        if region:
            region = region.strip()
            
        if not subscription_key or not region:
            raise Exception("Missing Azure Speech credentials from environment variables.")
            
        speech_config = speechsdk.SpeechConfig(subscription=subscription_key, region=region)
        speech_config.speech_synthesis_voice_name = 'en-US-AvaMultilingualNeural'
        output_path = os.path.join("output", "speech.wav")
        audio_config = speechsdk.audio.AudioOutputConfig(filename=output_path)
        synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
        
        result = synthesizer.speak_text_async(text).get()
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            return jsonify({
                "status": "success",
                "message": "Speech synthesized",
                "audioUrl": "/output/speech.wav"
            })
        else:
            return jsonify({"status": "error", "message": "Speech synthesis error"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

########################################
# New Endpoints for File Upload/Download
########################################

@app.route("/upload_main", methods=["POST"])
def upload_main():
    if "file" not in request.files:
        return "No file part", 400
    file = request.files["file"]
    if file.filename == "":
        return "No selected file", 400
    try:
        # Ignore the input filename; always save as 5html_converted_content.json
        file.save(MAIN_JSON_FILE)
        return redirect(url_for("index"))
    except Exception as e:
        return str(e), 500

@app.route("/upload_feedback", methods=["POST"])
def upload_feedback():
    if "file" not in request.files:
        return "No file part", 400
    file = request.files["file"]
    if file.filename == "":
        return "No selected file", 400
    try:
        # Ignore the input filename; always save as 6email_feedback.json
        file.save(FEEDBACK_JSON_FILE)
        return redirect(url_for("index"))
    except Exception as e:
        return str(e), 500

@app.route("/download_main", methods=["GET"])
def download_main():
    try:
        output_dir = os.path.join(app.root_path, "../output")
        file_path = os.path.join(output_dir, "5html_converted_content.json")
        # Debug: check if the file exists
        if not os.path.exists(file_path):
            raise Exception(f"File not found: {file_path}")
        return send_from_directory(directory=output_dir,
                                   path="5html_converted_content.json",
                                   as_attachment=True)
    except Exception as e:
        print("Download Main Error:", e)
        return str(e), 500

@app.route("/download_feedback", methods=["GET"])
def download_feedback():
    try:
        output_dir = os.path.join(app.root_path, "../output")
        return send_from_directory(directory=output_dir,
                                   path="6email_feedback.json",
                                   as_attachment=True)
    except Exception as e:
        return str(e), 500

########################################
# New Endpoint for Resetting Files
########################################

@app.route("/reset_files", methods=["POST"])
def reset_files():
    try:
        # Reset main and feedback JSON files to empty lists
        with open(MAIN_JSON_FILE, "w", encoding="utf-8") as f:
            f.write("[]")
        with open(FEEDBACK_JSON_FILE, "w", encoding="utf-8") as f:
            f.write("[]")
        return redirect(url_for("index"))
    except Exception as e:
        return str(e), 500

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5100, debug=True)