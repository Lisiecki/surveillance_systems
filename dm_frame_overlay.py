﻿import argparse
import cv2
import numpy as np
import math
import picamera
import picamera.array
from picamera.array import PiRGBArray
from io import BytesIO
from PIL import Image

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-vd", "--vdirection", default=40, required=False, type=int, help="the vertical direction whereto the camera looks in degrees")
ap.add_argument("-hd", "--hdirection", default=0, required=False, type=int, help="the horizontal direction whereto the camera looks in degrees")
ap.add_argument("-vp", "--vview", default=40, required=False, type=int, help="vertical field of view of the camera")
ap.add_argument("-hp", "--hview", default=50, required=False, type=int, help="horizontal field of view of the camera")
ap.add_argument("-lh", "--lheight", default=2.41, required=False, type=float, help="the height of the camera's lense in meter")
ap.add_argument("-rw", "--reswidth", default=640, required=False, type=int, help="resolution width of the video stream")
ap.add_argument("-rh", "--resheight", default=480, required=False, type=int, help="resolution height of the video stream")
ap.add_argument("-gr", "--grows", default=5, required=False, type=int, help="preview grid rows")
ap.add_argument("-gc", "--gcolumns", default=9, required=False, type=int, help="preview grid columns")
ap.add_argument("-f", "--framerate", default=15, required=False, type=int, help="framerate of the video stream")
args = vars(ap.parse_args())

# MPEG macro-block represents a 16x16 pixel region of the frame
MACRO_BLOCK_PIXELS = 16

# get the parsed arguments and assign them
VERTICAL_DIRECTION = args["vdirection"]
HORIZONTAL_DIRECTION = args["hdirection"]
VERTICAL_FIELD_OF_VIEW = args["vview"]
HORIZONTAL_FIELD_OF_VIEW = args["hview"]
LENSE_HEIGHT = args["lheight"]
RES_WIDTH = args["reswidth"]
RES_HEIGHT = args["resheight"]
PREVIEW_GRID_ROWS = args["grows"]
PREVIEW_GRID_COLUMNS = args["gcolumns"]
FRAMERATE = args["framerate"]

# equivalent to size of motion-data array
# Motion data is calculated at the macro-block level (an MPEG macro-block represents a 16x16 pixel region of the frame), 
# and includes one extra column of data (source: http://picamera.readthedocs.io/en/latest/recipes2.html#recording-motion-vector-data)
VERTICAL_VIEW_POINTS = RES_HEIGHT / MACRO_BLOCK_PIXELS
HORIZONTAL_VIEW_POINTS = RES_WIDTH / MACRO_BLOCK_PIXELS

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
for i in range(np.shape(distances)[0]):
    v_direction = float(VERTICAL_DIRECTION + float(VERTICAL_FIELD_OF_VIEW) / 2.0 - float(VERTICAL_VIEW_POINTS_INTERVAL) / 2.0 - i * float(VERTICAL_VIEW_POINTS_INTERVAL))
    # Calculate diagonal distance by definition cos(angle) = adjacent leg / hypotenuse
    d_distance = LENSE_HEIGHT / math.cos(math.radians(v_direction))
    # Calculate horizontal distance with pythagoras' theorem
    h_distance = math.sqrt((d_distance * d_distance) + (LENSE_HEIGHT * LENSE_HEIGHT))
    # Then calculate the distance of each block based on distance = vertical distance / cos(horizontal angle)
    # from j to the amount of points on the x-axis
    for j in range(np.shape(distances)[1]):
        # Determine the horizontal direction (in degrees) of point(j, i)
        h_direction = float(j * HORIZONTAL_VIEW_POINTS_INTERVAL - HORIZONTAL_FIELD_OF_VIEW / 2.0 + HORIZONTAL_VIEW_POINTS_INTERVAL / 2.0)
        # Calculate actual distance from the camera to the monitored object by definition cos(angle) = adjacent leg / hypotenuse
        # If alpha is negative then negate alpha for this operation
        directions[j] = h_direction
        if h_direction < 0:
            distances[i][j] = h_distance / math.cos(math.radians(-h_direction))
        else:
            distances[i][j] = h_distance / math.cos(math.radians(h_direction))

class DetectMotion(picamera.array.PiMotionAnalysis):
    # Analyze motion data to determine current location of intruder
    def analyze(self, motion_data):
        if (motion_data > 50).sum() > 10:
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
            # Determine the boundaries of an intruder as rectangle in the motion data
            # start_x: first column with enough SADs >= threshold
            for x1 in range(np.shape(motion_data)[1]):
                if (motion_data[:, x1] > 50).sum() > 10:
                    start_x = x1
                    break
            # start_y: first row with enough SADs >= threshold
            for y1 in range(np.shape(motion_data)[0]):
                if (motion_data[y1, :] > 50).sum() > 10:
                    start_y = y1
                    break
            # end_x: last column with enough SADs >= threshold
            for x2 in reversed(range(np.shape(motion_data)[1])):
                if (motion_data[:, x2] > 50).sum() > 10:
                    end_x = x2
                    break
            # end_y: last row with enough SADs | >= threshold
            for y2 in reversed(range(np.shape(motion_data)[0])):
                if (motion_data[y2, :] > 50).sum() > 10:
                    end_y = y2
                    break
            # Get the horizontal center of the moving object
            x = start_x + (end_x - start_x) / 2
            # Determine the position of the intruder based on his/her position in the the distances array
            intruder_distance = distances[end_y][x]
            intruder_direction = directions[x]
            w = end_x-start_x
            h = end_y-start_y
            # draw the original bounding boxes
            #for (start_x, start_y, w, h) in rects:
                #cv2.rectangle(orig, (start_x, start_y), (start_x + w, start_y + h), (0, 0, 255), 2)

with picamera.PiCamera() as camera:
    with DetectMotion(camera) as output:
        stream = BytesIO()
        camera.resolution = (RES_WIDTH, RES_HEIGHT)
        camera.framerate = FRAMERATE
        rawCapture = PiRGBArray(camera, size=(640, 480))

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
            camera.stop_preview()
            camera.stop_recording()
