﻿import argparse
import cv2
import numpy as np
import math
import time
import picamera
import picamera.array
from picamera.array import PiMotionAnalysis
from picamera.array import PiRGBArray
from io import BytesIO
from PIL import Image

(x, y, h, w) = (0, 0, 0, 0)

class DetectMotion(PiMotionAnalysis):
    # Analyze motion data to determine current location of intruder
    def analyze(self, motion_data):
        global x
        global y
        global h
        global w
        motion_data = np.sqrt(
            np.square(motion_data['x'].astype(np.float)) +
            np.square(motion_data['y'].astype(np.float))
            ).clip(0, 255).astype(np.uint8)
        if (motion_data > 50).sum() > 10:
            (x, y, h, w) = (50, 50, 50, 50)

with picamera.PiCamera() as camera:
    with DetectMotion(camera) as output:
        stream = BytesIO()
        camera.resolution = (640, 480)
        camera.framerate = 15
        rawCapture = PiRGBArray(camera, size=(640, 480))
        camera.start_recording('/dev/null', format='h264', splitter_port=0, motion_output=output)
        # allow the camera to warmup
        time.sleep(0.1)
 
        # capture frames from the camera
        for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True, splitter_port=1):
            #(x, y, w, h) = cv2.boundingRect(c)
            #cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

	        # grab the raw NumPy array representing the image, then initialize the timestamp
	        # and occupied/unoccupied text
            image = frame.array
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
	        # show the frame
            cv2.imshow("Frame", image)
            key = cv2.waitKey(1) & 0xFF
 
	        # clear the stream in preparation for the next frame
            rawCapture.truncate(0)
 
	        # if the `q` key was pressed, break from the loop
            if key == ord("q"):
                break
