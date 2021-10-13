***Augmented Reality AR Framework*** written in Python

### Abstract

This project was created during the last sommer 2021 semester as I took a Computer Vision class at my university with the main usage point: to use it as a practical part of my future Bachelor Thesis.

After reading https://rdmilligan.wordpress.com/2015/10/15/augmented-reality-using-opencv-opengl-and-blender/ I was quite surprized how simple that could be. But since I wanted to use this technology from any smartphone there were necessary some improvements.

The whole idea of streaming OpenGL objects over a network was to grab its picture from the buffer right before it goes on the PC screen. We create the OpenGL texture in init with **glTexImage2D** and all further work with texture will be done withing **glTexSubImage2D** in order to not overflow the GPU memory during the long usage of the programm. Then thanks to **Flask** web application framework we send this collected from buffer Illustration of our OpenGL texture over the local network with simple reading pixels using **glReadPixels** and then converting this JPEG image into a binary string that one simply can send to the browser via HTTP. For more details how **Flask** manages this exercise please have a look at https://www.pyimagesearch.com/2019/09/02/opencv-stream-video-to-web-browser-html-page/

The video was recorded on Android smartphone during opening web browser with this stream one can see bellow:

https://user-images.githubusercontent.com/34322911/136968398-6c6f96fb-5532-44a8-8261-29832a2a5bb5.mov


<br />

---

### Installation

python3 -m venv env
source env/bin/activate
python3 -m pip install requests.txt

-then please make sure you've installed DroidCam app on you smartphone (in order you want to use your smartphone camera) and change the IP adress in *WebcamVideoStream()* function to IP address from DroidCam app.
-then you need to print Aruco markers from working directory (or you may simply open them on your device)

and you are ready to go: just type in your console *python3 main_flask.py* and target your camera on the Aruco marker to see how it works. Then you will see on the screen the IP address which you could open from any device in your local network to see this streaming. (please make aware there were predefined only 2 markers DICT_4X4_50_id24 and DICT_4X4_50_id5! In case you want to try use other markers you need to make some changes in the code. Same as you need to use other 3d objects (.obj) -> first predefine according to comments in the source code.

<br />

---

### License

[MIT] License

Copyright (c) 2021 Alexey Obukhov

<br />

---

### Contributing

Thanks for your attention and please don't hesitate to send me any advise, questions or possible improvements.

[MIT]: https://github.com/vertok/Python-Augmented-Reality-Framework/blob/main/LICENSE
