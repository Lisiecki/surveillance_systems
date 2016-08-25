import numpy as np
import math
import picamera
import picamera.array
from PIL import Image

# !!! only temporary for testing !!!
angle = 40
sensor_height = 1.5
picture_rows_count = 5
picture_columns_count = 9
HORIZONTAL_ANGLE = 50
VERTICAL_ANGLE = 45

# rows represent y coordinates of points
# columns represent x coordinates of points
directions = np.zeros(picture_columns_count)
distances = np.zeros((picture_rows_count, picture_columns_count))

HORIZONTAL_ANGLE_INTERVAL = float(HORIZONTAL_ANGLE) / float(picture_columns_count)
VERTICAL_ANGLE_INTERVAL = float(VERTICAL_ANGLE) / float(picture_rows_count)

monitored_points_json = []
monitored_points = []
v_angle = 1.1
h_angle = 1.1
intruder_direction = (0, 0)
intruder_distance = 0

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
        directions[j] = h_angle
        if h_angle < 0:
            distances[i][j] = v_distance / math.cos(math.radians(-h_angle))
        else:
            distances[i][j] = v_distance / math.cos(math.radians(h_angle))

class MotionDetector(picamera.array.PiMotionAnalysis):
    def analyze(self, a):
        global intruder_direction
        global intruder_distance
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

        # Determine the boundaries of an intruder in the motion data
        for i in range(motion_data):
            for j in range(motion_data[i]):
                if data[i][j] > 50:
                    # Left boundary
                    start_x = RES_WIDTH / motion_data.shape(0) * j
                    # Upper boundary
                    start_y = RES_HEIGHT / motion_data.shape(1) * i
        for i in range(reversed(motion_data)):
            for j in range(reversed(motion_data[i])):
                if motion_data[i][j] > 50:
                    # Right boundary
                    end_x = RES_WIDTH / motion_data.shape(0) * j
                    # Lower boundary
                    end_y = RES_HEIGHT / motion_data.shape(1) * i
        
        # Get the horizontal center of the moving object
        x = (end_x - start_x) / 2
        # Determine the position of the intruder based on his/her position in the the distances array
        intruder_distance = distances[end_y, x]
        intruder_direction = directions[x]

        # Pretend we wrote all the bytes of s
        return len(s)

with picamera.PiCamera() as camera:
    with DetectMotion(camera) as output:
        camera.resolution = (RES_WIDTH, RES_HEIGHT)
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
                camera.annotate_text = str(intruder_distance) + ' meters ' + str(int(intruder_direction)) + ' degrees'
            except KeyboardInterrupt:
                break
        camera.stop_recording()
        camera.stop_preview()