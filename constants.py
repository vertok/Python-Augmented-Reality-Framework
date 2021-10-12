import numpy as np
fx = 552.97442167
fy = 551.57580319
height = 1040
width = 1280
fovy = 2*np.arctan(0.5*height/fy)*180/np.pi
aspect = (width*fy)/(height*fx)
zNear = 0.1
zFar = 100.0