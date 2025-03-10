import os
import json
from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for
from dotenv import load_dotenv
from subprocess import check_output, CalledProcessError
import azure.cognitiveservices.speech as speechsdk
from speech_synthesizer import synthesize  # uses our SSML builder with rate control

# Load environment variables from .env
load_dotenv()

########################################
# JSON file helpers: load and save records (from main copy.py)
########################################
JSON_FILES = {
    "index.html": "output/5html_converted_content.json"
}
QA_JSON_FILE = "output/6email_feedback.json"

def load_records(template):
    # Force using "index.html"
    json_file = JSON_FILES["index.html"]
    print("Loading JSON from:", json_file)
    if os.path.exists(json_file):
        with open(json_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_records(template, records):
    json_file = JSON_FILES["index.html"]
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=4, ensure_ascii=False)

def load_feedback_records():
    if os.path.exists(QA_JSON_FILE):
        with open(QA_JSON_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_feedback_records(records):
    with open(QA_JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=4, ensure_ascii=False)

########################################
# Flask App & Routes (from main copy.py)
########################################
app = Flask(__name__)

@app.route('/output/<path:filename>')
def serve_output(filename):
    output_dir = os.path.join(app.root_path, '../output')
    return send_from_directory(output_dir, filename)

@app.route("/")
@app.route("/<template>")
def index(template="index.html"):
    records = load_records("index.html")
    return render_template("index.html", records=records)

@app.route("/update_record", methods=["POST"])
def update_record():
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
    records = load_records("index.html")
    if idx < 0 or idx >= len(records):
        return jsonify({"status": "error", "message": "Record index out of range."}), 400
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
    """
    This endpoint now preserves the original feature of reading the text,
    voice, and speech rate from the front end and passes them to our 
    synthesize() function (which builds the SSML with rate control).
    """
    data = request.get_json()
    text = data.get("text", "Hello from Azure TTS!")
    voice = data.get("voice", "en-US-AriaNeural")
    rate = data.get("rate", "0%")
    try:
        # Set output path for the WAV file
        output_path = os.path.join("output", "speech.wav")
        result = synthesize(text, voice, rate, output_file=output_path)
        if result.reason == getattr(speechsdk, "ResultReason").SynthesizingAudioCompleted:
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
        file.save(JSON_FILES["index.html"])
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
        file.save(QA_JSON_FILE)
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
        with open(JSON_FILES["index.html"], "w", encoding="utf-8") as f:
            f.write("[]")
        with open(QA_JSON_FILE, "w", encoding="utf-8") as f:
            f.write("[]")
        return redirect(url_for("index"))
    except Exception as e:
        return str(e), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5100, debug=True)