import time

class DeviceController:
    def __init__(self):
        self.state = {
            'mode': 'SELECT_DEVICE',  # hoặc 'CONTROL_DEVICE'
            'selected_device': None,
            'last_gesture_time': time.time(),
            'timeout': 3.0,  # 3 giây không có gesture thì reset
            
            'devices': {
                1: {
                    'name': 'ac',
                    'label': 'Điều hòa',
                    'power': False,
                    'temperature': 25,
                    'min_temp': 16,
                    'max_temp': 30
                },
                2: {
                    'name': 'fan',
                    'label': 'Quạt',
                    'power': False,
                    'speed': 1,
                    'max_speed': 3
                },
                3: {
                    'name': 'tv',
                    'label': 'TV',
                    'power': False,
                    'channel': 1,
                    'max_channel': 99
                },
                4: {
                    'name': 'light',
                    'label': 'Đèn',
                    'power': False,
                    'brightness': 50,
                    'max_brightness': 100
                }
            }
        }
    
    def check_timeout(self):
        """Kiểm tra timeout, reset về chế độ SELECT"""
        if time.time() - self.state['last_gesture_time'] > self.state['timeout']:
            if self.state['mode'] == 'CONTROL_DEVICE':
                self.state['mode'] = 'SELECT_DEVICE'
                self.state['selected_device'] = None
                return True
        return False
    
    def process_gesture(self, gesture_data):
        """Xử lý gesture và cập nhật state"""
        if not gesture_data['hand_detected']:
            self.check_timeout()
            return self.get_state()
        
        self.state['last_gesture_time'] = time.time()
        finger_count = gesture_data['finger_count']
        gesture = gesture_data['gesture']
        
        # Chế độ chọn thiết bị
        if self.state['mode'] == 'SELECT_DEVICE':
            if 1 <= finger_count <= 4:
                self.state['selected_device'] = finger_count
                self.state['mode'] = 'CONTROL_DEVICE'
                print(f"Selected device: {self.state['devices'][finger_count]['label']}")
        
        # Chế độ điều khiển thiết bị
        elif self.state['mode'] == 'CONTROL_DEVICE':
            device_id = self.state['selected_device']
            device = self.state['devices'][device_id]
            
            # Bật/tắt thiết bị (nắm đấm = 0 ngón)
            if finger_count == 0:
                device['power'] = not device['power']
                print(f"{device['label']} {'ON' if device['power'] else 'OFF'}")
            
            # Điều khiển theo từng thiết bị
            elif device['power']:
                if device['name'] == 'light':
                    self._control_light(device, gesture)
                elif device['name'] == 'ac':
                    self._control_ac(device, gesture)
                elif device['name'] == 'fan':
                    self._control_fan(device, gesture)
                elif device['name'] == 'tv':
                    self._control_tv(device, gesture)
        
        return self.get_state()
    
    def _control_light(self, device, gesture):
        """Điều khiển đèn bằng zoom"""
        if gesture == 'zoom_in':
            device['brightness'] = min(
                device['brightness'] + 5, 
                device['max_brightness']
            )
        elif gesture == 'zoom_out':
            device['brightness'] = max(device['brightness'] - 5, 0)
    
    def _control_ac(self, device, gesture):
        """Điều khiển điều hòa bằng xoay tay"""
        if gesture == 'rotate_up':
            device['temperature'] = min(
                device['temperature'] + 1, 
                device['max_temp']
            )
        elif gesture == 'rotate_down':
            device['temperature'] = max(
                device['temperature'] - 1, 
                device['min_temp']
            )
    
    def _control_fan(self, device, gesture):
        """Điều khiển quạt bằng zoom"""
        if gesture == 'zoom_in':
            device['speed'] = min(device['speed'] + 1, device['max_speed'])
        elif gesture == 'zoom_out':
            device['speed'] = max(device['speed'] - 1, 1)
    
    def _control_tv(self, device, gesture):
        """Điều khiển TV bằng swipe"""
        if gesture == 'swipe_right':
            device['channel'] = min(
                device['channel'] + 1, 
                device['max_channel']
            )
        elif gesture == 'swipe_left':
            device['channel'] = max(device['channel'] - 1, 1)
    
    def get_state(self):
        """Lấy state hiện tại để gửi về frontend"""
        return {
            'mode': self.state['mode'],
            'selected_device': self.state['selected_device'],
            'devices': self.state['devices']
        }