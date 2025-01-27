import time
import subprocess
import digitalio
import board
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789

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


# Configuration for CS and DC pins (these are FeatherWing defaults on M0/M4):
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
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)
font1 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 25)
# Turn on the backlight
backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output()
backlight.value = True

while True:
    # Draw a black filled box to clear the image.
    #draw.rectangle((0, 0, width, height), outline=0, fill=(255,0, 0))

    #TODO: Lab 2 part D work should be filled in here. You should be able to look in cli_clock.py and stats.py 
    hours= int(strftime("%H"))
    minute= int(strftime("%M"))
    if  hours>= 0 and hours <=5 :
        image2 = Image.open("batman_logo.jpg")
        Greet = "Batman is watching you"
    if  hours >= 18 and hours <=23:
        image2 = Image.open ("superman.jpg")
        Greet = "Have a Super awesome day"

    image2 = image_resize(image2)
    draw= ImageDraw.Draw(image2)
    if hours%2 == 1:
        Time=  str(minute)
    else :
        Time= str(minute + 60)
    y = top
    draw.text((x, y), Greet, font=font, fill="#FF0000")
    y += font.getsize(Greet)[1]
    draw.text((x, y), Time, font=font1, fill="#FF0000")
    # Display image.
    disp.image(image2, rotation)    
    time.sleep(1)
