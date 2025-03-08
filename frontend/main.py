import os
import json
from flask import Flask, render_template, request, jsonify, send_from_directory
from dotenv import load_dotenv
from subprocess import check_output, CalledProcessError

# Load environment variables from .env
load_dotenv()

########################################
# JSON file helpers: load and save records
########################################
# Updated JSON file locations (only index.html is used)
JSON_FILES = {
    "index.html": "output/5html_converted_content.json"
}

QA_JSON_FILE = "output/6email_feedback.json"

def load_records(template):
    # Force using "index.html"
    json_file = JSON_FILES["index.html"]
    print("Loading JSON from:", json_file)  # Debug line
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
        # Call the Azure Speech script using azure-speech.js
        check_output(["node", "frontend/azure-speech.js", text])
        return jsonify({
            "status": "success",
            "message": "Speech synthesized",
            "audioUrl": "/output/speech.wav"
        })
    except CalledProcessError as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5100, debug=True)