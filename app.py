from flask import Flask, render_template, Response, request, jsonify
from video_sources import get_stream
import cv2
import requests
import base64
import os
import random
import time

app = Flask(__name__)

# Video sources
video_sources = {
    "local": 0,
    "http": "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4",
    "rtsp": "rtsp://rtsp.stream/pattern"
}

# Roboflow API config
ROBOFLOW_API_KEY = "your_roboflow_api_key"
ROBOFLOW_MODEL_URL = "https://detect.roboflow.com/YOUR_MODEL_NAME/1"

# Store OpenCV capture objects
current_caps = {}

# Folder to save frames
output_folder = "frames"
os.makedirs(output_folder, exist_ok=True)

# Frame counter
frame_count = 1
last_save_time = 0
save_interval = 1  # seconds between frame saves


def get_cv2_cap(source_key):
    """Create or reuse an OpenCV capture object for a source."""
    if source_key not in current_caps:
        src = video_sources.get(source_key, 0)
        current_caps[source_key] = cv2.VideoCapture(src)
    return current_caps[source_key]

def generate_and_save_frames(source_key):
    """Generator for streaming video and saving frames in real time."""
    global frame_count, last_save_time
    cap = get_cv2_cap(source_key)
    save_interval = random.randint(30, 40)  # set initial interval

    while True:
        success, frame = cap.read()
        if not success:
            break

        current_time = time.time()
        if current_time - last_save_time >= save_interval:
            filename = os.path.join(output_folder, f"frame_{frame_count}.jpg")
            cv2.imwrite(filename, frame)
            print(f"Saved: {filename}")
            frame_count += 1
            last_save_time = current_time
            save_interval = random.randint(30, 40)  # randomize next interval

        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/video_feed')
def video_feed():
    source_key = request.args.get('source', 'local')
    return Response(generate_and_save_frames(source_key),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/detect')
def detect():
    source_key = request.args.get('source', 'local')
    cap = get_cv2_cap(source_key)
    ret, frame = cap.read()

    if not ret:
        return jsonify({"error": "Failed to capture frame"}), 500

    _, buffer = cv2.imencode('.jpg', frame)
    img_base64 = base64.b64encode(buffer).decode('utf-8')

    response = requests.post(
        f"{ROBOFLOW_MODEL_URL}?api_key={ROBOFLOW_API_KEY}",
        data=img_base64,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    try:
        result = response.json()
        return jsonify(result)
    except:
        return jsonify({"error": "Invalid response from Roboflow"}), 500


@app.route('/hls')
def hls():
    return render_template('hls.html')


if __name__ == '__main__':
    app.run(debug=True)
