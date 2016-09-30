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

class DetectMotion(picamera.array.PiMotionAnalysis):
    # Analyze motion data to determine current location of intruder
    def analyze(self, motion_data):
        if (motion_data > 50).sum() > 10:
            motion_data = np.sqrt(
                np.square(motion_data['x'].astype(np.float)) +
                np.square(motion_data['y'].astype(np.float))
                ).clip(0, 255).astype(np.uint8)



with picamera.PiCamera() as camera:
    with DetectMotion(camera) as output:
        stream = BytesIO()
        camera.resolution = (RES_WIDTH, RES_HEIGHT)
        camera.framerate = FRAMERATE
        rawCapture = PiMotionAnalysis(camera, size=(640, 480))

        # allow the camera to warmup
        time.sleep(0.1)
        try:
            # capture frames from the camera
            for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
	            # grab the raw NumPy array representing the image, then initialize the timestamp
	            # and occupied/unoccupied text
                image = frame.array

	            # show the frame
                cv2.imshow("Frame", image)
                key = cv2.waitKey(1) & 0xFF

	            # clear the stream in preparation for the next frame
                rawCapture.truncate(0)

	            # if the `q` key was pressed, break from the loop
                if key == ord("q"):
                    break
        except KeyboardInterrupt:
            vidstream.release()
            cv2.destroyAllWindows()
            camera.stop_recording()
