import argparse
import cv2
import numpy as np
import math
import time
import picamera
import picamera.array
from picamera.array import PiRGBArray
from io import BytesIO
from PIL import Image

class DetectMotion(picamera.array.PiMotionAnalysis):
    # Analyze motion data to determine current location of intruder
    def analyze(self, motion_data):
        if (motion_data > 50).sum() > 10:
            motion_data = np.sqrt(
                np.square(motion_data['x'].astype(np.float)) +
                np.square(motion_data['y'].astype(np.float))
                ).clip(0, 255).astype(np.uint8)
            # grab the raw NumPy array representing the image, then initialize the timestamp
	        # and occupied/unoccupied text
            image = frame.array

	        # show the frame
            cv2.imshow("Frame", image)


with picamera.PiCamera() as camera:
    with DetectMotion(camera) as output:
        stream = BytesIO()
        camera.resolution = (640, 480)
        camera.framerate = 30
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
                i = 1
            except KeyboardInterrupt:
                cv2.destroyAllWindows()
                camera.stop_recording()
