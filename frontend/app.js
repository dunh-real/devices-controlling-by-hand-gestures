const socket = io('http://localhost:5000');
const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const processedImg = document.getElementById('processed');
const ctx = canvas.getContext('2d');

let isProcessing = false;

// Khởi tạo camera
async function initCamera() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({
            video: { width: 640, height: 480 }
        });
        video.srcObject = stream;
        
        video.onloadedmetadata = () => {
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            processFrames();
        };
    } catch (err) {
        console.error('Camera error:', err);
        alert('Không thể truy cập camera!');
    }
}

// Gửi frame lên server
function processFrames() {
    if (isProcessing) return;
    
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const imageData = canvas.toDataURL('image/jpeg', 0.8);
    
    isProcessing = true;
    socket.emit('frame', { image: imageData });
    
    setTimeout(processFrames, 100); // 10 FPS
}

// Nhận kết quả từ server
socket.on('processed_frame', (data) => {
    isProcessing = false;
    
    // Hiển thị frame đã xử lý
    processedImg.src = data.image;
    
    // Cập nhật gesture info
    const gestureData = data.gesture_data;
    document.getElementById('finger-count').textContent = gestureData.finger_count;
    document.getElementById('gesture').textContent = gestureData.gesture || '-';
    
    // Cập nhật state
    updateDevicesUI(data.state);
});

// Cập nhật UI thiết bị
function updateDevicesUI(state) {
    // Cập nhật mode
    const modeText = state.mode === 'SELECT_DEVICE' ? 'Chọn thiết bị' : 'Điều khiển';
    document.getElementById('mode').textContent = modeText;
    
    // Highlight thiết bị được chọn
    document.querySelectorAll('.device').forEach(el => {
        el.classList.remove('selected');
    });
    
    if (state.selected_device) {
        document.getElementById(`device-${state.selected_device}`).classList.add('selected');
    }
    
    // Cập nhật trạng thái từng thiết bị
    Object.entries(state.devices).forEach(([id, device]) => {
        const deviceEl = document.getElementById(`device-${id}`);
        const powerStatus = deviceEl.querySelector('.power-status');
        
        powerStatus.textContent = device.power ? 'ON' : 'OFF';
        powerStatus.className = device.power ? 'power-status on' : 'power-status';
        
        // Cập nhật giá trị cụ thể
        if (device.name === 'ac') {
            deviceEl.querySelector('.temp').textContent = device.temperature;
        } else if (device.name === 'fan') {
            deviceEl.querySelector('.speed').textContent = device.speed;
        } else if (device.name === 'tv') {
            deviceEl.querySelector('.channel').textContent = device.channel;
        } else if (device.name === 'light') {
            deviceEl.querySelector('.brightness').textContent = device.brightness;
            // Điều chỉnh độ sáng background
            if (device.power) {
                deviceEl.style.opacity = 0.5 + (device.brightness / 200);
            }
        }
    });
}

// Khởi động
initCamera();