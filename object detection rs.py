#   Hanny Long
#   5/31/2021
#   This code run an object recognition of the video stream, box the objects,
#   lable it, and try to get the distance to that object
#   Need: 'frozen_inference_graph.pb', 'ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt', "Labels.txt" to run

import cv2
import pyrealsense2 as rs
import numpy as np
import sys

## make a list of all the object class from the list of labels
classLabels = []
file_name = "Labels.txt"    ## 80 in len
with open(file_name, "rt") as fpt:
    classLabels = fpt.read().rstrip("\n").split("\n")

model = cv2.dnn_DetectionModel('frozen_inference_graph.pb', 'ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt')

model.setInputSize(320,320)
model.setInputScale(1.0/(255/2))
model.setInputMean(((255/2),(255/2),(255/2)))
model.setInputSwapRB(True) ##swap red and blue

# Create a pipeline
pipeline = rs.pipeline()

# Create a config and configure the pipeline to stream
#  different resolutions of color and depth streams
config = rs.config()

# Get device product line for setting a supporting resolution
pipeline_wrapper = rs.pipeline_wrapper(pipeline)
pipeline_profile = config.resolve(pipeline_wrapper)
device = pipeline_profile.get_device()
device_product_line = str(device.get_info(rs.camera_info.product_line))

config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)

if device_product_line == 'L500':
    config.enable_stream(rs.stream.color, 960, 540, rs.format.bgr8, 30)
else:
    config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

# Start streaming
profile = pipeline.start(config)

# Getting the depth sensor's depth scale (see rs-align example for explanation)
depth_sensor = profile.get_device().first_depth_sensor()
depth_scale = depth_sensor.get_depth_scale()
print("Depth Scale is: " , depth_scale)

# Create an align object
# rs.align allows us to perform alignment of depth frames to others frames
# The "align_to" is the stream type to which we plan to align depth frames.
align_to = rs.stream.color
align = rs.align(align_to)

#counting frame until passing to object detection
count = 12

# Streaming loop
try:
    while True:
    #for _ in range(30):
        # Get frameset of color and depth
        frames = pipeline.wait_for_frames()
        # frames.get_depth_frame() is a 640x360 depth image

        # Align the depth frame to color frame
        aligned_frames = align.process(frames)

        # Get aligned frames
        aligned_depth_frame = aligned_frames.get_depth_frame() # aligned_depth_frame is a 640x480 depth image
        color_frame = aligned_frames.get_color_frame()

        # Validate that both frames are valid
        if not aligned_depth_frame or not color_frame:
            continue

        depth_image = np.asanyarray(aligned_depth_frame.get_data())
        color_image = np.asanyarray(color_frame.get_data())
        
        #passing the image to the object detection model
        if (count%12 == 0):
            ClassIndex, confidence, bbox = model.detect(color_image, confThreshold = 0.5)
            count = 0
        count = count + 1

        #draw the box around the object and lable it
        if(len(ClassIndex) != 0):
            for ClassInd, conf, boxes in zip(ClassIndex.flatten(), confidence.flatten(), bbox):
                if (ClassInd <= 80):
                    
                    #get distance of the closest point in the bbox of the object detected
                    min_dis = sys.maxsize
                    for i in range(boxes[1], boxes[3]):
                        for j in range(boxes[0], boxes[2]):
                            temp_dis = aligned_depth_frame.get_distance(j,i)
                            if 0 < temp_dis and temp_dis < min_dis:
                                min_dis = temp_dis
                    if min_dis == sys.maxsize:      #if no distance return, return -1
                        min_dis = -1
                    
                    obj_label = classLabels[ClassInd-1] + ' ' + str(min_dis)[:4] + "m"
                    cv2.rectangle(color_image, boxes, (255,0,0), 2)
                    cv2.putText(color_image, obj_label, (boxes[0]+10, boxes[1]+40), cv2.FONT_HERSHEY_PLAIN, fontScale = 3, color = (0,255,0), thickness=3)                    

        # Render images:
        #   depth align to color on left
        #   depth on right
        depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET)
        images = np.hstack((color_image, depth_colormap))

        cv2.namedWindow('Align Example', cv2.WINDOW_NORMAL)
        cv2.imshow('Align Example', images)
        key = cv2.waitKey(1)
        # Press esc or 'q' to close the image window
        if key & 0xFF == ord('q') or key == 27:
            cv2.destroyAllWindows()
            break
finally:
    pipeline.stop()


