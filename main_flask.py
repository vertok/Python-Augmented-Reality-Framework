# This programm was created by Alexey Obukhov vertok@hotmail.com
# it casts OpenGL graphical objects over local network withing Flask and therefore is asseccible from any device
# if needed one could use smartphone with its camera after installing some app like DroidCam for using 
# its camera as IP Webcam. This programm was created after inspiration by
# https://rdmilligan.wordpress.com/2015/10/15/augmented-reality-using-opencv-opengl-and-blender/
# and https://www.pyimagesearch.com/2019/09/02/opencv-stream-video-to-web-browser-html-page/
# please press CTRL+C in case to quit the programm

from ctypes import c_uint, c_ubyte
from OpenGL.GLUT import *
from OpenGL.GLU import *

from webcam import WebcamVideoStream

import cv2
import cv2.aruco as aruco
from PIL import Image
import numpy as np
import constants as cnst
from pygame import *
from obj_loader import *

from flask import Response, request
from flask import Flask
from flask import render_template

import threading
import time
import signal
import gc

import os
import sys

# initialize the output frame and a lock used to ensure thread-safe
# exchanges of the output frames (useful for multiple browsers/tabs
# are viewing the stream) and define size of the image to work with
outputFrame = None
lock = threading.Lock()
WIDTH = 1280
HEIGHT = 1040

# see https://github.com/ajaymin28/Aruco_python/ for more details
ARUCO_DICT = aruco.Dictionary_get(aruco.DICT_4X4_50)
ARUCO_PARAMETERS = aruco.DetectorParameters_create()

# for increasing camera FPS
PREV = 0

class OpenGLGlyphs:

    # initialize a flask object
    if getattr(sys, 'frozen', False):
        template_folder = os.path.join(sys._MEIPASS, 'templates')
        print("###frozen###")
        app = Flask(__name__, template_folder=template_folder)
    else:
        print("###normal###")
        app = Flask(__name__)
   
    # camera warm up
    time.sleep(2.0)

    # constants
    INVERSE_MATRIX = np.array([[ 1.0, 1.0, 1.0, 1.0],
                               [-1.0,-1.0,-1.0,-1.0],
                               [-1.0,-1.0,-1.0,-1.0],
                               [ 1.0, 1.0, 1.0, 1.0]], dtype=np.float16)
 
    def __init__(self):
        # initialise webcam and start thread
        # please write WebcamVideoStream() to use laptop webcam or use your IP from your camera
        self.webcam = WebcamVideoStream("http://192.168.0.106:4747/video")
        self.webcam.start()

        # for sync opengl output<->flask 
        try:
            self.fps = self.webcam.get_fps()
            self.sleeping_time = 1/self.fps
        except:
            print("camera was not found")
            os._exit(0)

        # initialise shapes (just add new one in case it needed)
        self.object_5 = None
        self.object_24 = None

        self.matrix, self.dist = self.get_camera_matrix()
 
    def _init_gl(self, Width, Height):
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glClearDepth(1.0)
        glDepthFunc(GL_LESS)
        glEnable(GL_DEPTH_TEST)
        glShadeModel(GL_SMOOTH)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        # on laptop camera in calibration there was cnst.fovy=~85
        gluPerspective(50, cnst.aspect, cnst.zNear, cnst.zFar)
        glMatrixMode(GL_MODELVIEW)
         
        # assign shapes (just assign new one in case it needed)
        self.object_5 = OBJ('beerbottle_club11.obj')
        self.object_24 = OBJ('Earth.obj',swapyz=True)

        # initialise texture
        self._texture_background = 0
        self.bg_image = 0

        # initialise buffer for reading images
        self.buffer = (c_ubyte*(3*WIDTH*HEIGHT))()

        # assign texture
        glEnable(GL_TEXTURE_2D)

        # create background texture
        self._texture_background = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self._texture_background)
        glEnable(GL_TEXTURE_2D)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB8, 640, 480, 0, GL_RGBA, GL_UNSIGNED_BYTE, self.buffer)
        glGenerateMipmap(GL_TEXTURE_2D)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S,GL_REPEAT)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST_MIPMAP_NEAREST)
        
    def _draw_scene(self):
        global outputFrame, lock, PREV
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
 
        # get image from webcam
        image = self.webcam.read()
        time_elapsed = time.time() - PREV
        
        # https://www.codegrepper.com/code-examples/python/Increasing+Webcam+FPS+Opencv
        if image is not None and time_elapsed > 1./self.fps:
            PREV = time.time()

            # convert image to OpenGL texture format
            bg_image = Image.fromarray(image)
            ix = bg_image.size[0]
            iy = bg_image.size[1]
            bg_image = bg_image.tobytes("raw", "BGRX", 0, 0)

            # draw background
            glBindTexture(GL_TEXTURE_2D, self._texture_background)
            glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, ix, iy, GL_RGBA, GL_UNSIGNED_BYTE, bg_image)
            glPushMatrix()
            glTranslatef(0.0,0.0,-10.0)
            self._draw_background()
            glPopMatrix()

            # handle glyphs
            self._handle_glyphs(image)

            # grab image from buffer https://stackoverflow.com/q/7142169/5870553
            glReadPixels(0,0,WIDTH,HEIGHT,GL_BGR,GL_UNSIGNED_BYTE,self.buffer)
            frame_BGR = Image.frombuffer("RGB",(WIDTH,HEIGHT),self.buffer,"raw","RGB",0,-1)
            frame_BGR = np.array(frame_BGR, dtype=np.int16)

            # send image to Flask for further work
            with lock:
                outputFrame = frame_BGR.copy()
                            
            glutSwapBuffers()

    def get_camera_matrix(self):
        with np.load('webcam_calibration_ouput.npz') as X:
            matrix, dist, _, _ = [X[i] for i in ('mtx','dist','rvecs','tvecs')]
        return matrix,dist

    def _handle_glyphs(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        corners, ids, _ = aruco.detectMarkers(gray, ARUCO_DICT, parameters=ARUCO_PARAMETERS)

        if ids is not None and corners is not None: 
            rvecs,tvecs ,_ = aruco.estimatePoseSingleMarkers(corners[0],1,self.matrix,self.dist)
            # build view matrix
            rmtx = cv2.Rodrigues(rvecs)[0]
            tvecs = tvecs[0]
            view_matrix = np.array([[rmtx[0][0],rmtx[0][1],rmtx[0][2],tvecs[0][0]],
                                    [rmtx[1][0],rmtx[1][1],rmtx[1][2],tvecs[0][1]],
                                    [rmtx[2][0],rmtx[2][1],rmtx[2][2],tvecs[0][2]],
                                    [0.0       ,0.0       ,0.0       ,1.0    ]], dtype=np.float16)


            view_matrix = view_matrix * self.INVERSE_MATRIX
            view_matrix = np.transpose(view_matrix)

            # load view matrix and draw shape
            glPushMatrix()
            glLoadMatrixd(view_matrix)

            currentObject = ids[0][0]
            # currently there was used aruco.DICT_4X4_50 dict therefore it is possible
            # to display 50 different objects which firstly need no be declared in init
            if currentObject == 5:
                glCallList(self.object_5.gl_list)
            elif currentObject == 24:                
                glCallList(self.object_24.gl_list)

            glPopMatrix()
 
    def _draw_background(self):
        # draw background
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 1.0); glVertex3f(-4.0, -3.0, 0.0)
        glTexCoord2f(1.0, 1.0); glVertex3f( 4.0, -3.0, 0.0)
        glTexCoord2f(1.0, 0.0); glVertex3f( 4.0,  3.0, 0.0)
        glTexCoord2f(0.0, 0.0); glVertex3f(-4.0,  3.0, 0.0)
        glEnd( )
 
    def main(self):
        # setup and run OpenGL
        glutInit()
        glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_DEPTH)
        glutInitWindowSize(WIDTH,HEIGHT)
        glutInitWindowPosition(640,480)
        self.window_id = glutCreateWindow("Club11")
        glutDisplayFunc(self._draw_scene)
        glutIdleFunc(self._draw_scene)
        self._init_gl(WIDTH,HEIGHT)
        glutMainLoop()
        
    # Flask part
    @app.route('/')
    def index():
        return render_template('./index.html')

    @staticmethod
    def gen():
        global PREV_flask, outputFrame, lock
        
        while True:

            if 'outputFrame' in globals():
                with lock:
                    frame = outputFrame

                # encode the frame in JPEG format
                encodedImage = cv2.imencode(".JPEG", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])[1].tobytes()

                # Convert this JPEG image into a binary string that one can send to the browser via HTTP
                yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + encodedImage + b'\r\n')

                del outputFrame, frame, encodedImage
                
    @app.route('/video_feed')
    def video_feed():
        return Response(OpenGLGlyphs.gen(),
                        mimetype='multipart/x-mixed-replace; boundary=frame')

    # exit on CTRL + C
    def signal_handler(self, signal, frame):
        print("\nclosing HTTP connection, tiding everything up \nand exiting from the programm...")
        self.webcam.stop()
        gc.collect()
        OpenGLGlyphs.gen().close()
        cv2.destroyAllWindows()
        os._exit(0)

if __name__ == '__main__':
        OpenGLGlyphs = OpenGLGlyphs()
        signal.signal(signal.SIGINT, OpenGLGlyphs.signal_handler)
        # run main body in deamon
        t = threading.Thread(target = OpenGLGlyphs.main)
        t.deamon = True
        t.start()

        # host="0.0.0.0" will make the page accessable from local network by going to http://[ip]:port/ 
        # on any computer in the network.
        OpenGLGlyphs.app.run(host='0.0.0.0', port=5000, threaded=False, use_reloader=False, debug=True)
