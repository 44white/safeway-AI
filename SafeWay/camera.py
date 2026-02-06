from picamera2 import Picamera2
import time
import cv2

class Camera:
    def __init__(self, width=640, height=480): 
        self.picam2 = Picamera2()
        
        config = self.picam2.create_still_configuration(
            main={"size": (width, height)},
            buffer_count=2
        )
        self.picam2.configure(config)
        self.picam2.start()
        time.sleep(0.5)  # 카메라 워밍업 시간

    def get_frame(self):
        frame = self.picam2.capture_array()
        return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

    def release(self):
        self.picam2.close()
