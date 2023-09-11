from depthai_sdk import OakCamera
from depthai_sdk.classes import TwoStagePacket
import depthai as dai
import datetime
from depthai_sdk.fps import FPSHandler
import time
import shutil
import os
import getopt
import sys

# Command line flags
short_options = "hvrmofpcnd:"
long_options = ["help", "vis", "record=", "matrix", "out", "fps", "play=", "conf=", "recnn=", "detnn="]

# Defaults
vis = False
recordToggle = False
record = ''
out = False
showFPSToggle = False
playToggle = False
play = ''
detnn = ''
detToggle = False
recnn = ''
recToggle = False
matrix = False
conf = 0.85
confToggle = False
fps = FPSHandler()

def print_help_and_exit():
    print("--vis\n	Make a visualizer widow")
    print("--record <file>\n	Record video output")
    print("--matrix\n	Display decoded plates on 8x8x4 LED matrix")
    print("--out\n	Print results to console")
    print("--fps\n	Display FPS on console")
    print("--play <file>\n	Use video file as input")
    print("--conf <conf>\n	Confidence percent under which results are ignored, int between 0 and 100")			
    print("--recnn <json>\n        Use custom recognition model. Requires json file")
    print("--detnn <json>\n        Use custom detection model. Requires json file")
    sys.exit(1)    

try:
    opts, args = getopt.getopt(sys.argv[1:], short_options, long_options)
except getopt.GetoptError:
    print("Error: invalid argument")
    sys.exit(2)

for opt, arg in opts:
    if opt in ("-h", "--help"):
        print_help_and_exit()
    elif opt in ("-v", "--vis"):
        vis = True
        print(f"Show visualizer windows: {vis}")
    elif opt in ("-r", "--record"):
        recordToggle = True
        record = str(arg)
        print(f"Record path: {record}")
    elif opt in ("-m", "--matrix"):
        matrix = True
        print(f"Use LED matrix: {matrix}")
    elif opt in ("-o", "--out"):
        out = True
        print(f"Show output on console: {out}")
    elif opt in ("-f", "--fps"):
        showFPSToggle = True
        print(f"Show FPS: {showFPSToggle}")
    elif opt in ("-p", "--play"):
        play = str(arg)
        playToggle = True
        print(f"Video path: {play}")
    elif opt in ("-c", "--conf"):
        conf = str(arg)
        if conf.strip(): conf = float(conf)
        else: conf = 0.50
        print(f"Confidence: {conf}") 
    elif opt in ("-n", "--recnn"):
        recnn = str(arg)
        RecToggle = True
        print(f"Rec NN: {recnn}")
    elif opt in ("-d", "--detnn"):
        detnn = str(arg)
        detToggle = True
        print(f"Det NN: {detnn}")
    

#reset flags; depthai uses arguments in imported libraries which
#get confused if you add your own
sys.argv = [sys.argv[0]] 

# This function copies and renames the video to be played to color.mp4
# because depthai won't play it otherwise
def make_stream(filePath):
    dir_path, filename = os.path.split(filePath)
    print(f"Directory: {dir_path}")
    print(f"Filename: {filename}")
    if filename == "color.mp4":
        return filePath
    color_video = "color.mp4"
    new_path = os.path.join(dir_path, color_video)
    print(f"New Path: {new_path}")
    if os.path.exists(new_path):
        added_time = datetime.time()
        formatted_date = added_time.strftime("%H%d%m%Y")
        new_filename = "color_" + formatted_date + ".mp4"
        renamed = os.path.join(dir_path, new_filename)
        print(f"Moving {new_path} to {renamed}")
        shutil.move(new_path, renamed)
    shutil.copyfile(filePath, new_path)
    return new_path


if playToggle:
    stream = make_stream(play)
    oak = OakCamera(replay = stream)
else:
    oak = OakCamera()


#pattern = r"\b[A-Z0-9]{5,7}\b"

# This list maps to the index on the nnData.Img_Detections.detections.labels
# The rec nn has a label for every alphanumber which is the index number in this list
chars = ["0","1","2","3","4","5","6","7","8","9","A","B","C","D","E","F","G","H","I","J","K","L","M","N","O","P","Q","R","S","T","U","V","W","X","Y","Z","FP"]

plate_list = ['']

# LED matrix display -- connected via SPI to the GPIO headers
# Will scroll plate numbers as they are detected by calling 'show_message' 
# Scrolling proceeds indefinitely until a new plate is detected
if matrix: 
    from luma.led_matrix.device import max7219
    from luma.core.render import canvas
    from luma.core.interface.serial import spi, noop
    from luma.core.legacy import show_message, text
    from luma.core.legacy.font import proportional, LCD_FONT, TINY_FONT
    from luma.led_matrix.device import max7219

    serial = spi(port=0, device=0, gpio=noop())
    device = max7219(serial, cascaded=4, block_orientation = -90)  #cascaded is number of 8x8 blocks, orientation is dependent on the device
    show_message(device, 'READY...', fill="white", font=proportional(LCD_FONT) )

# When a new plate is recognized display the last plate number added to the plate list
def displayMatrix():
    fps.tick("matrix")
    index = len(plate_list) -1
    message = plate_list[index]
    with canvas(device) as draw:
        text(draw, (2,2), message, fill="white", font=proportional(TINY_FONT))

# Iterate through the detections, which are individual characters 
# The recognized chars are sorted horizontally      
def cb(packet: TwoStagePacket):
    fps.tick("rec")
    plate_number = ''
    total_confidence = sum(img_det.confidence for img_det in packet.img_detections.detections)
    num_detections = len(packet.img_detections.detections)
    average_confidence = (total_confidence / num_detections) if num_detections else 0
    global plate_list
    global current_plate
    for dets in packet.nnData:
        dets: packet.nnData.ImageDetections
        detection = dets.detections
        sorted_detections = sorted(detection, key=lambda det: det.xmin)
        plate_number = ''.join(chars[det.label] for det in sorted_detections)
        if (plate_number in plate_list): return
        if (len(plate_number) >= num_detections and len(plate_number) > 4 and average_confidence >= conf):
            average_confidence = round(average_confidence * 100, 2)
            if out:
                print(f"\nConfidence: {average_confidence}%")
                print(f"Added plate number: {plate_number}")
            plate_list.append(plate_number)

def showFPS():
    fps.tick("total")
    total = round(fps.tickFps("total"), 1)
    print(f"\rTotal FPS: {total}", end="")
    recFPS = round(fps.tickFps("rec"), 1)
    print(f" Rec FPS: {recFPS}", end="")
    if matrix: 
        matrixFPS = round(fps.tickFps("matrix"), 1)
        print(f" Matrix FPS: {matrixFPS}", end="")

with oak:
    color = oak.create_camera('color', resolution=dai.ColorCameraProperties.SensorResolution.THE_1080_P)
    color.config_color_camera(awb_mode=dai.CameraControl.AutoWhiteBalanceMode.OFF, luma_denoise=0, chroma_denoise=1, sharpness=1)
    
    if detToggle: det = oak.create_nn(model=detnn, input=color)
    else: det = oak.create_nn(model='./models/plates.json', input=color)
    
    det.config_nn(resize_mode='crop')
    
    if recToggle: rec = oak.create_nn(model=recnn, input=det)
    else: rec = oak.create_nn(model='./models/ocr.json', input=det)
    
    if vis: 
        print("vis")
        oak.visualize([rec.out.main], fps=True)
    
    oak.callback(rec, callback=cb)
    oak.start() 
    
    while oak.running:
        key = oak.poll()
        if showFPSToggle: showFPS()
        if matrix: displayMatrix()
        time.sleep(0.01)
        if key == ord('q'):
            break
       
     
