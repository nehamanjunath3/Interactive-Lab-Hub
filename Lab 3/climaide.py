from vosk import Model, KaldiRecognizer
import wave
import json
import os
import sys
import time
import subprocess
import digitalio
import board
import qwiic_button
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789
from time import strftime, sleep
from random import randint
import busio
from i2c_button import I2C_Button
#from __future__ import print_function
i2c = busio.I2C(board.SCL, board.SDA)
while not i2c.try_lock():
        pass
devices = i2c.scan()
i2c.unlock()
print('I2C devices found:', [hex(n) for n in devices])
default_addr = 0x6f
if default_addr not in devices:
        print('warning: no device at the default button address', default_addr)

# initialize the button
button = I2C_Button(i2c)

def image_resize(image):
        image = image.convert('RGB')
        image_ratio = image.width / image.height
        screen_ratio = width / height
        if screen_ratio < image_ratio:
                scaled_width = image.width * height // image.height
                scaled_height = height
        else:
                scaled_width = width
                scaled_height = image.height * width // image.width
        image = image.resize((scaled_width, scaled_height), Image.BICUBIC)
        # Crop and center the image
        x = scaled_width // 2 - width // 2
        y = scaled_height // 2 - height // 2
        image = image.crop((x, y, x + width, y + height))
        return image

button.led_bright = randint(0, 255)
button.led_gran = randint(0, 1)
button.led_cycle_ms = randint(250, 2000)
button.led_off_ms = randint(100, 500)

cs_pin = digitalio.DigitalInOut(board.CE0)
dc_pin = digitalio.DigitalInOut(board.D25)
reset_pin = None

# Config for display baudrate (default max is 24mhz):
BAUDRATE = 64000000

# Setup SPI bus using hardware SPI:
spi = board.SPI()

# Create the ST7789 display:
disp = st7789.ST7789(
    spi,
    cs=cs_pin,
    dc=dc_pin,
    rst=reset_pin,
    baudrate=BAUDRATE,
    width=135,
    height=240,
    x_offset=53,
    y_offset=40,
)

# Create blank image for drawing.
# Make sure to create image with mode 'RGB' for full color.
height = disp.width  # we swap height/width to rotate it to landscape!
width = disp.height
image = Image.new("RGB", (width, height))
rotation = 90

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

# Draw a black filled box to clear the image.
draw.rectangle((0, 0, width, height), outline=0, fill=(0, 0, 0))
disp.image(image, rotation)
# Draw some shapes.
# First define some constants to allow easy resizing of shapes.
padding = -2
top = padding
bottom = height - padding
# Move left to right keeping track of the current x position for drawing shapes.
x = 0

# Alternatively load a TTF font.  Make sure the .ttf font file is in the
# same directory as the python script!
# Some other nice fonts to try: http://www.dafont.com/bitmap.php
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
# Turn on the backlight
backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output()
backlight.value = True


subprocess.call("~/Interactive-Lab-Hub/Lab\ 3/occasion.sh", shell=True)

subprocess.call("~/Interactive-Lab-Hub/Lab\ 3/options.sh", shell=True)

if not os.path.exists("model"):
    print ("Please download the model from https://github.com/alphacep/vosk-api/blob/master/doc/models.md and unpack as 'model' in the current folder.")
    exit (1)

wf = wave.open(sys.argv[1], "rb")
if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
    print ("Audio file must be WAV format mono PCM.")
    exit (1)

model = Model("model")
# Large vocabulary free form recognition
rec = KaldiRecognizer(model, wf.getframerate(), '["oh one two three four five six seven eight nine zero date school class party running workout going on to a", "[unk]"]')
final_text = ""

while True:
    data = wf.readframes(4000)
    if len(data) == 0:
        break
    if rec.AcceptWaveform(data):
        res = json.loads(rec.Result())
        # print(res)
        # print(res['text'])
        final_text += res['text']

occasion_map = ['date', 'party', 'running', 'workout', 'class', 'school']
occasion = final_text.split()


while True:

    for c in occasion_map:
        if c == 'date':
            subprocess.call("~/Interactive-Lab-Hub/Lab\ 3/date.sh", shell=True)
            subprocess.call("~/Interactive-Lab-Hub/Lab\ 3/options.sh", shell=True)
            
            button.clear() # status must be cleared manually
            time.sleep(1)
            #print('status', button.status)
            #if button.status.is_pressed == 1:
            if button.is_button_pressed() == True:
                image2 = Image.open('date.jpeg')
                break

        if c == 'running' or c == 'workout':
            subprocess.call("~/Interactive-Lab-Hub/Lab\ 3/workout.sh", shell=True)
            subprocess.call("~/Interactive-Lab-Hub/Lab\ 3/options.sh", shell=True)
            
            button.clear() # status must be cleared manually
            time.sleep(1)
            #print('status', button.status)
            #if button.status.is_pressed == 1:
            if button.is_button_pressed() == True:
                image2 = Image.open('workout.jpeg')
                break
        
        else:
            subprocess.call("~/Interactive-Lab-Hub/Lab\ 3/didnt_understand.sh", shell=True)
            break

        image2= image_resize(image2)
        disp.image(image2, rotation)

        subprocess.call("~/Interactive-Lab-Hub/Lab\ 3/weather.sh", shell=True)
        image3 = Image.open('winter.jpg')
        image3= image_resize(image3)
        disp.image(image3, rotation)




    time.sleep(1)

            



