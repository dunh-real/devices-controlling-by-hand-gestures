from flask import Flask, render_template, Response
from flask_socketio import SocketIO, emit
import cv2
import base64
import numpy as np
from gesture_recognizer import GestureRecognizer
from device_controller import DeviceController

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Khởi tạo
gesture_recognizer = GestureRecognizer()
device_controller = DeviceController()

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('state_update', device_controller.get_state())

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('frame')
def handle_frame(data):
    """Nhận frame từ client, xử lý và gửi kết quả"""
    try:
        # Decode base64 image
        img_data = base64.b64decode(data['image'].split(',')[1])
        nparr = np.frombuffer(img_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Xử lý gesture
        gesture_data, processed_frame = gesture_recognizer.process_frame(frame)
        
        # Cập nhật device state
        state = device_controller.process_gesture(gesture_data)
        
        # Encode processed frame
        _, buffer = cv2.imencode('.jpg', processed_frame)
        processed_img = base64.b64encode(buffer).decode('utf-8')
        
        # Gửi kết quả về client
        emit('processed_frame', {
            'image': f'data:image/jpeg;base64,{processed_img}',
            'gesture_data': {
                'hand_detected': gesture_data['hand_detected'],
                'finger_count': gesture_data['finger_count'],
                'gesture': gesture_data['gesture']
            },
            'state': state
        })
        
    except Exception as e:
        print(f"Error processing frame: {e}")

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)