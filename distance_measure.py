import numpy as np
import picamera
import picamera.array
from PIL import Image

# rows represent y coordinates of points
# columns represent x coordinates of points
distances = np.zeros((picture_rows_count, picture_columns_count))
monitored_points_json = []
monitored_points = []
v_angle = 1.1
h_angle = 1.1
# Calculate the distance from the camera to each monitored point(j, i) in the camera's view
# from i to the amount of points on the y-axis
for i in range(np.shape(distances)[0]):
    v_angle = float(angle + float(VERTICAL_ANGLE) / 2.0 - float(VERTICAL_ANGLE_INTERVAL) / 2.0 - i * float(VERTICAL_ANGLE_INTERVAL))
    v_distance = sensor_height / math.cos(math.radians(v_angle))
    # Then calculate the distance of each block based on distance = vertical distance / cos(horizontal angle)
    # from j to the amount of points on the x-axis
    for j in range(np.shape(distances)[1]):
        # Determine the horizontal direction (in degrees) of point(j, i)
        h_angle = float(j * HORIZONTAL_ANGLE_INTERVAL - HORIZONTAL_ANGLE / 2.0 + HORIZONTAL_ANGLE_INTERVAL / 2.0)
        # Calculate total distance of point(j, i) by distance = c / cos(alpha)
        # If alpha is negative then negate alpha for this operation
        if h_angle < 0:
            distances[i][j] = v_distance / math.cos(math.radians(-h_angle))
        else:
            distances[i][j] = v_distance / math.cos(math.radians(h_angle))

class MotionDetector(picamera.array.PiMotionAnalysis):
    def analyze(self, a):
        start_x = 0
        start_y = 0
        end_x = 0
        end_y = 0
        # Load the motion data from the string to a numpy array
        motion_data = np.fromstring(s, dtype=motion_dtype)
        # Re-shape it and calculate the magnitude of each vector
        motion_data = motion_data.reshape((self.rows, self.cols))
        motion_data = np.sqrt(
            np.square(motion_data['x'].astype(np.float)) +
            np.square(motion_data['y'].astype(np.float))
            ).clip(0, 255).astype(np.uint8)

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
        while 1:
            try:
                i =0
            except KeyboardInterrupt:
                break
        camera.stop_recording()
        camera.stop_preview()