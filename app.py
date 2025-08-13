from flask import Flask, render_template, Response, request, jsonify
from video_sources import get_stream
import cv2
import requests
import base64

app = Flask(__name__)

# Video sources dictionary
video_sources = {
    "local": 0,
    "http": "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4", 
    "rtsp": "rtsp://rtsp.stream/pattern"   
}

# Roboflow config
ROBOFLOW_API_KEY = "your_roboflow_api_key"
ROBOFLOW_MODEL_URL = "https://detect.roboflow.com/YOUR_MODEL_NAME/1"

# Global cap for detection
current_caps = {}

def get_cv2_cap(source_key):
    """Create or reuse an OpenCV capture object for a source."""
    if source_key not in current_caps:
        src = video_sources.get(source_key, 0)
        current_caps[source_key] = cv2.VideoCapture(src)
    return current_caps[source_key]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    source_key = request.args.get('source', 'local')
    src = video_sources.get(source_key, 0)
    return Response(get_stream(src), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/detect')
def detect():
    source_key = request.args.get('source', 'local')
    cap = get_cv2_cap(source_key)
    ret, frame = cap.read()

    if not ret:
        return jsonify({"error": "Failed to capture frame"}), 500

    # Encode image as JPEG
    _, buffer = cv2.imencode('.jpg', frame)
    img_base64 = base64.b64encode(buffer).decode('utf-8')

    # Send to Roboflow
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
