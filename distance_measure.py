import numpy as np
import math
import picamera
import picamera.array
from PIL import Image

# !!! only temporary for testing !!!
# TODO: enter values on setup and define default values for testing or as default setup
angle = 40
sensor_height = 1.5
picture_rows_count = 5
picture_columns_count = 9
HORIZONTAL_ANGLE = 50
VERTICAL_ANGLE = 45

RES_WIDTH = 1280
RES_HEIGHT = 720

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
intruder_direction = 0
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

class DetectMotion(picamera.array.PiMotionAnalysis):
    # Analyze motion data to determine current location of intruder
    def analyze(self, motion_data):
        global intruder_direction
        global intruder_distance
        start_x = 0
        start_y = 0
        end_x = 0
        end_y = 0
        motion_data = np.sqrt(
            np.square(motion_data['x'].astype(np.float)) +
            np.square(motion_data['y'].astype(np.float))
            ).clip(0, 255).astype(np.uint8)
        # Determine the boundaries of an intruder in the motion data
        # start_x: first column with enough SADs >= threshold
        for i in range(picture_columns_count):
            if (motion_data[i] > 50).sum() > 10:
                start_x = i
        # start_y: first row with enough SADs >= threshold
        for i in range(picture_rows_count):
            if (motion_data[:][i] > 50).sum() > 10:
                start_y = i
        # end_x: last column with enough SADs >= threshold
        for i in reversed(range(picture_columns_count)):
             if (motion_data[i] > 50).sum() > 10:
                 end_x = i
        # end_y: last row with enough SADs | >= threshold
        for i in reversed(range(picture_rows_count)):
            if (motion_data[:][i] > 50).sum() > 10:
                end_y = i
        # Get the horizontal center of the moving object
        x = end_x - (start_x / 2)
        # Determine the position of the intruder based on his/her position in the the distances array
        intruder_distance = distances[end_y][x]
        intruder_direction = directions[x]

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
        try:
            # TODO: add grids and (if possible) distances+directions to the preview
            while 1:
                i = 1
                camera.annotate_text = str(intruder_distance) + ' meters ' + str(int(intruder_direction)) + ' degrees'
        except KeyboardInterrupt:
            camera.stop_preview()
            camera.stop_recording()
