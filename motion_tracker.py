import numpy as np
import picamera
import picamera.array
from PIL import Image

with picamera.PiCamera() as camera:
    with picamera.array.PiMotionArray(camera) as stream:
        camera.resolution = (1280, 720)
        camera.framerate = 30
        camera.start_preview()
        camera.start_recording('/dev/null', format='h264', motion_output=stream)
        camera.wait_recording(10)
        camera.stop_recording()
        camera.stop_preview()
        for frame in range(stream.array.shape[0]):
            data = np.sqrt(
                np.square(stream.array[frame]['x'].astype(np.float)) +
                np.square(stream.array[frame]['y'].astype(np.float))
                ).clip(0, 255).astype(np.uint8)
            for i in range(data):
                for j in range(data[i]):
                    if data[i][j] > 50:
                        start_x = 1280 / data.shape(0) * j
                        start_y = 720 / data.shape(1) * i
            for i in range(reversed(data)):
                for j in range(reversed(data[i])):
                    if data[i][j] > 50:
                        end_x = 1280 / data.shape(0) * j
                        end_y = 720 / data.shape(1) * i

            # Create an array representing a 1280x720 image of
            # a cross through the center of the display. The shape of
            # the array must be of the form (height, width, color)
            a = np.zeros((720, 1280, 3), dtype=np.uint8)
            i = start_x
            j = start_y
            while i <= end_x:
                a[start_y][i] = 0xff
                a[end_y][i] = 0xff
                i += 1
            while j <= end_y:
                a[j][start_x] = 0xff
                a[j][end_x] = 0xff
                j += 1
            # Add the overlay directly into layer 3 with transparency;
            # we can omit the size parameter of add_overlay as the
            # size is the same as the camera's resolution
            o = camera.add_overlay(np.getbuffer(a), layer=3, alpha=64)
            camera.remove_overlay(o)

camera = picamera.PiCamera()
camera.resolution = (1280, 720)
camera.framerate = 24
camera.start_preview()
# Add the overlay directly into layer 3 with transparency;
# we can omit the size parameter of add_overlay as the
# size is the same as the camera's resolution
o = camera.add_overlay(np.getbuffer(a), layer=3, alpha=64)
try:
    # Wait indefinitely until the user terminates the script
    while True:
        time.sleep(1)
finally:
    camera.remove_overlay(o)