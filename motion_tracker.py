import numpy as np
import picamera
import picamera.array
from PIL import Image

motion_detected = False

start_x = 0
start_y = 0
end_x = 0
end_y = 0

class MotionDetector(picamera.array.PiMotionAnalysis):
    def analyze(self, a):
        global motion_detected
        global start_x
        global start_y
        global end_x
        global end_y
        a = np.sqrt(
            np.square(a['x'].astype(np.float)) +
            np.square(a['y'].astype(np.float))
            ).clip(0, 255).astype(np.uint8)
        # If there're more than 10 vectors with a magnitude greater
        # than 60, then a motion has been detected
        if (a > 60).sum() > 10:
            for i in range(a):
                for i in range(a[i]):
                    if a[i][j] > 50:
                        start_x = 1280 / a.shape(0) * j
                        start_y = 720 / a.shape(1) * i
            for i in range(reversed(a)):
                for j in range(reversed(a[i])):
                    if a[i][j] > 50:
                        end_x = 1280 / a.shape(0) * j
                        end_y = 720 / a.shape(1) * i
            motion_detected = True
            # Pretend we wrote all the bytes of s
        return len(s)

with picamera.PiCamera() as camera:
    with picamera.array.PiMotionAnalysis(camera) as output:
        camera.resolution = (1280, 720)
        camera.framerate = 30
        camera.start_preview()
        camera.start_recording('/dev/null', format='h264', motion_output=output)
        while 1:
            try:
                if motion_detected:
                    # maybe I should synchronize that
                    motion_detected = False
                    # Create an array representing a 1280x720 image of
                    # a cross through the center of the display. The shape of
                    # the array must be of the form (height, width, color)
                    a = np.zeros((720, 1280, 3), dtype=np.uint8)
                    x = start_x
                    y = start_y
                    while x <= end_x:
                        a[start_y][x] = 0xff
                        a[end_y][x] = 0xff
                        x += 1
                    while y <= end_y:
                        a[y][start_x] = 0xff
                        a[y][end_x] = 0xff
                        y += 1
                    # Add the overlay directly into layer 3 with transparency;
                    # we can omit the size parameter of add_overlay as the
                    # size is the same as the camera's resolution
                    o = camera.add_overlay(np.getbuffer(a), layer=3, alpha=64)
                    # sleep until the next frame occurs (for 30 fps)
                    # does not guarantee that the next frame has been analyzed!
                    sleep(0.033)
                    camera.remove_overlay(o)
            except KeyboardInterrupt:
                break
        camera = picamera.PiCamera()
        camera.stop_recording()
        camera.stop_preview()