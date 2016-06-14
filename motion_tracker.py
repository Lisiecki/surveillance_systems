import numpy as np
import picamera
import picamera.array
from PIL import Image

class MotionDetector(picamera.array.PiMotionAnalysis):
    def analyze(self, a):
        start_x = 0
        start_y = 0
        end_x = 0
        end_y = 0
        camera = picamera.PiCamera()
        # Load the motion data from the string to a numpy array
        motion_data = np.fromstring(s, dtype=motion_dtype)
        # Re-shape it and calculate the magnitude of each vector
        motion_data = motion_data.reshape((self.rows, self.cols))
        motion_data = np.sqrt(
            np.square(motion_data['x'].astype(np.float)) +
            np.square(motion_data['y'].astype(np.float))
            ).clip(0, 255).astype(np.uint8)
        for i in range(motion_data):
            for j in range(motion_data[i]):
                if data[i][j] > 50:
                    start_x = 1280 / motion_data.shape(0) * j
                    start_y = 720 / motion_data.shape(1) * i
        for i in range(reversed(motion_data)):
            for j in range(reversed(motion_data[i])):
                if motion_data[i][j] > 50:
                    end_x = 1280 / motion_data.shape(0) * j
                    end_y = 720 / motion_data.shape(1) * i

        # Create an array representing a 1280x720 image of
        # a cross through the center of the display. The shape of
        # the array must be of the form (height, width, color)
        a = np.zeros((720, 1280, 3), dtype=np.uint8)
        i = start_x
        j = start_y
        while x <= end_x:
            a[start_y][x] = 0xff
            a[end_y][x] = 0xff
            i += 1
        while y <= end_y:
            a[y][start_x] = 0xff
            a[y][end_x] = 0xff
            y += 1
        # Add the overlay directly into layer 3 with transparency;
        # we can omit the size parameter of add_overlay as the
        # size is the same as the camera's resolution
        o = camera.add_overlay(np.getbuffer(a), layer=3, alpha=64)
        sleep(0.033)
        camera.remove_overlay(o)
        # Pretend we wrote all the bytes of s
        return len(s)

with picamera.PiCamera() as camera:
    with DetectMotion(camera) as output:
        camera.resolution = (1280, 720)
        camera.framerate = 30
        camera.start_preview()
        camera.start_recording(
                    # Throw away the video data, but make sure we're using H.264
                    '/dev/null', format='h264',
                    # Record motion data to our custom output object
                    motion_output=output
                    )
        camera.close()
        while 1:
            try:
                i =0
            except KeyboardInterrupt:
                break
        camera = picamera.PiCamera()
        camera.stop_recording()
        camera.stop_preview()