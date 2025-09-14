from flask import Flask, render_template, request, jsonify, send_file
from moviepy.editor import VideoFileClip, AudioFileClip
import os
import uuid
import tempfile

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


@app.route("/")
def home():
    return render_template("index.html")


# 1️⃣ Upload files
@app.route("/upload", methods=["POST"])
def upload_files():
    if "video_file" not in request.files or "audio_file" not in request.files:
        return jsonify({"status": "failed", "error": "Both video_file and audio_file are required"}), 400

    video_file = request.files["video_file"]
    audio_file = request.files["audio_file"]

    if video_file.filename == "" or audio_file.filename == "":
        return jsonify({"status": "failed", "error": "Empty filename"}), 400

    # Save with unique names
    video_path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}_{video_file.filename}")
    audio_path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}_{audio_file.filename}")

    video_file.save(video_path)
    audio_file.save(audio_path)

    return jsonify({
        "status": "success",
        "message": "Files uploaded successfully",
        "video_path": video_path,
        "audio_path": audio_path
    }), 200


# 2️⃣ Merge video + audio
@app.route("/merge", methods=['POST'])
def merge_video_audio():
    try:
        # Check if files are uploaded
        if 'video_file' not in request.files or 'audio_file' not in request.files:
            return jsonify({"status": "failed", "error": "Video or audio file missing"}), 400

        video_file = request.files['video_file']
        audio_file = request.files['audio_file']

        # Save uploaded files temporarily
        temp_dir = tempfile.mkdtemp()
        video_path = os.path.join(temp_dir, video_file.filename)
        audio_path = os.path.join(temp_dir, audio_file.filename)
        output_path = os.path.join(temp_dir, "merged_output.mp4")

        video_file.save(video_path)
        audio_file.save(audio_path)

        # Merge video and audio
        video_clip = VideoFileClip(video_path)
        audio_clip = AudioFileClip(audio_path)

        # Ensure video matches audio duration (or trim audio if needed)
        final_clip = video_clip.set_audio(audio_clip).set_duration(min(video_clip.duration, audio_clip.duration))

        # Export merged video
        final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")

        # Return file for download
        return send_file(output_path, as_attachment=True, download_name="merged_video.mp4")

    except Exception as e:
        return jsonify({"status": "failed", "error": str(e)}), 500



@app.route("/download/<filename>", methods=["GET"])
def download_file(filename):
    filepath = os.path.join(OUTPUT_FOLDER, filename)
    if not os.path.exists(filepath):
        return jsonify({"status": "failed", "error": "File not found"}), 404
    return send_file(filepath, as_attachment=True)


if __name__  == "__main__":
    app.run(host='0.0.0.0', debug=True, port=5002)