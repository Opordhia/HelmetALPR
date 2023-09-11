# HelmetALPR
Machine learning assisted real time ALPR (automatic license plate recognition) for helmet and dash cameras.

A Luxonis DepthAI device is used to capture video and detect license plates and parse the plate numbers in real time. 

It is also possible to plug in a matrix LED display (set of 8x8 panels) to a raspberry pi and have it output the most recent recognized plate number.

A Yolov5n object detection model is used for both the plate detection and recognition. The weights used are specific to USA license plates, and are most useful for modern Pennsylvania passenger base plates since the majority of training images came from my own helmet cam videos.

Required:

A DepthAI capable device with a color camera. They start at less than $100. Get a fixed focus model.

Some options are:

  * Oak-1, Oak-1-Lite
  * Oak-D, Oak-D-Lite

Also needed is a single board computer and a power source. USB-3 is strongly recommended.

Installation instructions for Windows or Linux:

* Install Python 3.9, 3.10 or 3.11 
* Install depthai api and sdk
* Optional: install Luma.led-matrix

Flags:
`code`
--vis

        Make a visualizer widow
        
--record <file>

        Record video output
        
---matrix

        Display decoded plates on 8x8x4 LED matrix
        
---out

        Print results to console
        
--fps

        Display FPS on console
        
--play <file>

        Use video file as input
        
--conf <conf>

        Confidence percent under which results are ignored, int between 0 and 100
        
--recnn <json>

         Use custom recognition model. Requires json file
         
--detnn <json>

         Use custom detection model. Requires json file


