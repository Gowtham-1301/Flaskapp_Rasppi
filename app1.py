from flask import Flask, Response, jsonify
import cv2
import requests
import base64

app = Flask(__name__)
cap = cv2.VideoCapture(0)  # Simulates Pi Camera using laptop webcam

# Replace with your Roboflow model URL and API key
ROBOFLOW_API_KEY = "YOUR_API_KEY"
ROBOFLOW_MODEL_URL = "https://detect.roboflow.com/YOUR_MODEL/1"

def gen_frames():
    while True:
        success, frame = cap.read()
        if not success:
            break
        _, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video')
def video():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/detect')
def detect():
    ret, frame = cap.read()
    _, img_encoded = cv2.imencode('.jpg', frame)
    img_base64 = base64.b64encode(img_encoded).decode('utf-8')

    response = requests.post(
        f"{ROBOFLOW_MODEL_URL}?api_key={ROBOFLOW_API_KEY}",
        data=img_base64,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    return jsonify(response.json())

@app.route('/')
def index():
    return """
    <h2>Live Drone Feed Simulation</h2>
    <img src="/video" width="640"><br><br>
    <a href="/detect">Run Roboflow Detection on Current Frame</a>
    """

if __name__ == '__main__':
    app.run(debug=True)
