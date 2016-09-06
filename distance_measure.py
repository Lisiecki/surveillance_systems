﻿import argparse
import numpy as np
import math
import picamera
import picamera.array
from PIL import Image

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-vd", "--vdirection", default=45, required=False, type=int, help="the vertical direction whereto the camera looks in degrees")
ap.add_argument("-hd", "--hdirection", default=0, required=False, type=int, help="the horizontal direction whereto the camera looks in degrees")
ap.add_argument("-vv", "--vview", default=40, required=False, type=int, help="vertical field of view of the camera in degrees")
ap.add_argument("-hv", "--hview", default=50, required=False, type=int, help="horizontal field of view of the camera in degrees")
ap.add_argument("-vp", "--vpoints", default=720, required=False, type=int, help="amount of vertical view points. must divide resolution width of the video stream")
ap.add_argument("-hp", "--hpoints", default=360, required=False, type=int, help="amount of horizontal view points. must divide resolution width of the video stream")
ap.add_argument("-lh", "--lheight", default=2.0, required=False, type=float, help="the height of the camera's lense in meter")
ap.add_argument("-rw", "--reswidth", default=1280, required=False, type=int, help="resolution width of the video stream")
ap.add_argument("-rh", "--resheight", default=720, required=False, type=int, help="resolution height of the video stream")
ap.add_argument("-gr", "--grows", default=5, required=False, type=int, help="preview grid rows")
ap.add_argument("-gc", "--gcolumns", default=9, required=False, type=int, help="preview grid columns")
ap.add_argument("-f", "--framerate", default=15, required=False, type=int, help="framerate of the video stream")
args = vars(ap.parse_args())

# get the parsed arguments and assign them
VERTICAL_DIRECTION = args["vdirection"]
HORIZONTAL_DIRECTION = args["hdirection"]
VERTICAL_VIEW_POINTS = args["vview"]
HORIZONTAL_VIEW_POINTS = args["hview"]
HORIZONTAL_FIELD_OF_VIEW = args["vpoints"]
VERTICAL_FIELD_OF_VIEW = args["hpoints"]
LENSE_HEIGHT = args["lheight"]
RES_WIDTH = args["reswidth"]
RES_HEIGHT = args["resheight"]
PREVIEW_GRID_ROWS = args["grows"]
PREVIEW_GRID_COLUMNS = args["gcolumns"]
FRAMERATE = args["framerate"]

# horizontal direction of each view point (we only need the directions for one row)
directions = np.zeros(HORIZONTAL_VIEW_POINTS)
# distance of each view point
# rows represent y coordinates of points
# columns represent x coordinates of points
distances = np.zeros((VERTICAL_VIEW_POINTS, HORIZONTAL_VIEW_POINTS))

HORIZONTAL_VIEW_POINTS_INTERVAL = float(HORIZONTAL_FIELD_OF_VIEW) / float(HORIZONTAL_VIEW_POINTS)
VERTICAL_VIEW_POINTS_INTERVAL = float(VERTICAL_FIELD_OF_VIEW) / float(VERTICAL_VIEW_POINTS)

monitored_points_json = []
monitored_points = []
v_direction = 1.1
h_direction = 1.1
intruder_direction = 0
intruder_distance = 0

# Calculate the distance from the camera to each monitored point(j, i) in the camera's view
# from i to the amount of points on the y-axis
print("57")
for i in range(np.shape(distances)[0]):
    v_direction = float(VERTICAL_DIRECTION + float(VERTICAL_FIELD_OF_VIEW) / 2.0 - float(VERTICAL_VIEW_POINTS_INTERVAL) / 2.0 - i * float(VERTICAL_VIEW_POINTS_INTERVAL))
    v_distance = LENSE_HEIGHT / math.cos(math.radians(v_direction))
    # Then calculate the distance of each block based on distance = vertical distance / cos(horizontal angle)
    # from j to the amount of points on the x-axis
    print("62")
    for j in range(np.shape(distances)[1]):
        # Determine the horizontal direction (in degrees) of point(j, i)
        h_direction = float(j * HORIZONTAL_VIEW_POINTS_INTERVAL - HORIZONTAL_FIELD_OF_VIEW / 2.0 + HORIZONTAL_VIEW_POINTS_INTERVAL / 2.0)
        # Calculate total distance of point(j, i) by distance = c / cos(alpha)
        # If alpha is negative then negate alpha for this operation
        directions[j] = h_direction
        if h_direction < 0:
            print("69")
            distances[i][j] = v_distance / math.cos(math.radians(-h_direction))
        else:
            print("72")
            distances[i][j] = v_distance / math.cos(math.radians(h_direction))

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
        # TODO go through motion_data clusterwise!
        # Determine the boundaries of an intruder as rectangle in the motion data
        # start_x: first column with enough SADs >= threshold
        print("92")
        for i in range(np.shape(motion_data)[0]):
            if (motion_data[i] > 50).sum() > 10:
                start_x = i
        # start_y: first row with enough SADs >= threshold
        print("96")
        for i in range(np.shape(motion_data)[1]):
            print("99")
            print(i)
            print(np.shape(motion_data)[1])
            if (motion_data[:][i] > 50).sum() > 10:
                print("102")
                start_y = i
        # end_x: last column with enough SADs >= threshold
        print("100")
        for i in reversed(range(np.shape(motion_data)[0])):
             if (motion_data[i] > 50).sum() > 10:
                 end_x = i
        # end_y: last row with enough SADs | >= threshold
        print("104")
        for i in reversed(range(np.shape(motion_data)[1])):
            if (motion_data[:][i] > 50).sum() > 10:
                end_y = i
        # Get the horizontal center of the moving object
        x = end_x - (start_x / 2)
        # Determine the position of the intruder based on his/her position in the the distances array
        print("110")
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
        # Create an array representing a 1280x720 image of
        # a cross through the center of the display. The shape of
        # the array must be of the form (height, width, color)
        a = np.zeros((RES_HEIGHT, RES_WIDTH, 3), dtype=np.uint8)
        print("133")
        a[RES_HEIGHT / PREVIEW_GRID_ROWS : RES_HEIGHT : RES_HEIGHT / PREVIEW_GRID_ROWS, :, :] = 0xff
        print("135")
        a[:, RES_WIDTH / PREVIEW_GRID_COLUMNS : RES_WIDTH : RES_WIDTH / PREVIEW_GRID_COLUMNS, :] = 0xff
        # Add the overlay directly into layer 3 with transparency;
        # we can omit the size parameter of add_overlay as the
        # size is the same as the camera's resolution
        o = camera.add_overlay(np.getbuffer(a), layer=3, alpha=64)
        try:
            while 1:
                i = 1
                camera.annotate_text = str(intruder_distance) + ' meters ' + str(int(intruder_direction)) + ' degrees'
        except KeyboardInterrupt:
            camera.stop_preview()
            camera.stop_recording()
