from webcam import Webcam
import cv2
from datetime import datetime
import numpy as np
  
webcam = Webcam()
webcam.start()
object_points_array = []
image_points_array = []
# create grid for calibrating the camera
obj_pts = np.zeros((6 * 7, 3), np.float32)
obj_pts[:, :2] = np.mgrid[0:7, 0:6].T.reshape(-1, 2)

criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
i = 0
while i<25:
     
    # get image from webcam
    image = webcam.get_current_frame()
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # display image
    cv2.imshow('grid', image)
    cv2.waitKey(3000)
 
    # save image to file, if pattern found
    ret, corners = cv2.findChessboardCorners(gray, (7,6), None)
 
    if ret:
        object_points_array.append(obj_pts)

        cornersSubPixeled = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
        image_points_array.append(cornersSubPixeled)

        image = cv2.drawChessboardCorners(image, (7, 6), cornersSubPixeled, ret)
        cv2.imshow('image', image)
        cv2.waitKey(500)

        filename = datetime.now().strftime('%Y%m%d_%Hh%Mm%Ss%f') + '.jpg'
        cv2.imwrite("pose/sample_images/" + filename, image)
        print("done")
        i = i + 1

# calibrate webcam and save output
ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(object_points_array, image_points_array, gray.shape[::-1], None, None)
print("ret", ret)
print("mtx", mtx)
print("dist", dist)
print("rvecs", rvecs)
print("tvecs",tvecs)
np.savez("pose/webcam_calibration_ouput", ret=ret, mtx=mtx, dist=dist, rvecs=rvecs, tvecs=tvecs)
print("done")
