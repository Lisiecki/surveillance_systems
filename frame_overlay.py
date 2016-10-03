import argparse
import cv2
import numpy as np
import math
import time
import picamera
import picamera.array
from picamera.array import PiMotionAnalysis
from io import BytesIO
from PIL import Image

frame = 0

class DetectMotion(PiMotionAnalysis):
    # Analyze motion data to determine current location of intruder
    def analyze(self, motion_data):
        global frame
        motion_data = np.sqrt(
            np.square(motion_data['x'].astype(np.float)) +
            np.square(motion_data['y'].astype(np.float))
            ).clip(0, 255).astype(np.uint8)
        frame = motion_data


with picamera.PiCamera() as camera:
    with DetectMotion(camera) as output:
        stream = BytesIO()
        camera.resolution = (640, 480)
        camera.framerate = 15
        camera.start_recording(
            # Throw away the video data, but make sure we're using H.264
            '/dev/null', format='h264',
            # Record motion data to our custom output object
            motion_output=output
            )

        # allow the camera to warmup
        time.sleep(0.1)
        while 1:
            try:            
                # show the frame
                cv2.imshow("Frame", frame)
                time.sleep(0.1)
            except KeyboardInterrupt:
                cv2.destroyAllWindows()
                camera.stop_recording()
