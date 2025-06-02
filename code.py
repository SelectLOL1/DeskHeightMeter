import board
import displayio
import terminalio
import time
import digitalio

import ulab.numpy as np

from adafruit_display_text import label
from fourwire import FourWire
from adafruit_button import Button

from adafruit_hx8357 import HX8357
import adafruit_stmpe610
from adafruit_hcsr04 import HCSR04

# Release any resources currently in use for the display
displayio.release_displays()

# SPI & TFT setup (unchanged)
spi = board.SPI()
tft_cs = board.D9
tft_dc = board.D12
touch_cs = digitalio.DigitalInOut(board.D5)

display_bus = FourWire(spi, command=tft_dc, chip_select=tft_cs)
display = HX8357(display_bus, width=480, height=320, )

# Touch‐controller calibration/flip (unchanged)
touchFlip = (False, True)
touchCalib = ((238, 3863), (329, 3847))
touchSensor = adafruit_stmpe610.Adafruit_STMPE610_SPI(
    spi,
    cs=touch_cs,
    calibration=touchCalib,
    size=(display.width, display.height),
    touch_flip=touchFlip
)

# HC‐SR04 distance sensor (unchanged)
distSensor = HCSR04(trigger_pin=board.D3, echo_pin=board.D4)

class myControlButton():
    def __init__(self, btn) -> None:
        self.btn = btn
        self.btnState = False
    
    @property
    def value(self):
        return self.btn.btnState
    @value.setter
    def value(self, val):
        self.btnState = not val
        self.btn.value = self.btnState
    

# gpios: UFI on D8, ABI on D11 (updated from D6/D10)
ufi = digitalio.DigitalInOut(board.D8)
abi = digitalio.DigitalInOut(board.D11)
ufi.direction = digitalio.Direction.OUTPUT
abi.direction = digitalio.Direction.OUTPUT

ufiOut = myControlButton(ufi)
abiOut = myControlButton(abi)
ufiOut.value = False
abiOut.value = False

# Make the display context
splash = displayio.Group()
display.root_group = splash

# 1) Green background
color_bitmap = displayio.Bitmap(480, 320, 1)
color_palette = displayio.Palette(1)
color_palette[0] = 0xAA0088  # Bright Green
bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
splash.append(bg_sprite)

# 2) Purple inner rectangle
inner_bitmap = displayio.Bitmap(440, 280, 1)
inner_palette = displayio.Palette(1)
inner_palette[0] = 0xAA0088  # Purple
inner_sprite = displayio.TileGrid(inner_bitmap, pixel_shader=inner_palette, x=20, y=20)
splash.append(inner_sprite)

# 3) “Hello World!” label
text_group = displayio.Group(scale=1, x=10, y=160)
#text = "Hello World!"
#text_area = label.Label(terminalio.FONT, text=text, color=0xFFFF00)
#text_group.append(text_area)
splash.append(text_group)

# 4) Distance label
sensorText = label.Label(terminalio.FONT, text="Distance: ", color=0xFFFF00)
sensorText.x = 20
sensorText.y = 130
sensorText.scale = 2
splash.append(sensorText)

# 5) Two on‐screen buttons (left and right)
#    Position them below the purple rectangle (e.g., y=220), each 200×80 pixels.
ufiButton = Button(
    x=20, y=220,                           # 20 px from left edge, 220 px down
    width=200, height=80,
    label="UFI",                            # initial label
    label_font=terminalio.FONT,
    label_scale=2,
    label_color=0xFFFFFF,              
    fill_color=0x4444AA,                   # blueish
    outline_color=0xFFFF00,
    selected_fill=0xAA4444,                # reddish when pressed
    selected_outline=0xFFFFFF
)
abiButton = Button(
    x=260, y=220,                          # 260 px from left edge (20 + 200 + 40 spacing)
    width=200, height=80,
    label="ABI",
    label_font=terminalio.FONT,
    label_scale=2,
    label_color=0xFFFFFF,  
    fill_color=0x4444AA,
    outline_color=0xFFFF00,
    selected_fill=0xAA4444,
    selected_outline=0xFFFFFF
)
splash.append(ufiButton)
splash.append(abiButton)

counter = 0
buttonVisualized = False
distance = 0

def constraintsMet(direction):
    if distance > 150 and direction == "ABI":
        #print("Too close to PC, only allow UFI")
        abiOut.value = False
        return False
    elif distance < 145 and direction == "UFI":
        #print("Too high up, only allow ABI")
        ufiOut.value = False
        return False
    return True

h = [
    0.2,
    0.2,
    0.2,
    0.2,
    0.2,
]

data = np.zeros(len(h), dtype=np.float)

def automaticGotoDest(desiredDeskHeight):
    distance = 100
    timeStart = time.monotonic()
    h = [
    0.2,
    0.2,
    0.2,
    0.2,
    0.2,
    ]

    data = np.zeros(len(h), dtype=np.float)
    while True:
        try:
            distance = distSensor.distance
            data = np.roll(data, 1)
            data[-1] = distance
            filtered = np.sum(data * h)
            sensorText.text = f"Distance: {filtered:.2f} cm"
        except RuntimeError:
            pass

        diff = distance - desiredDeskHeight
        if abs(diff) < 0.5:
            break
        elif diff > 0.5:
            # Move up
            abiOut.value = False
            ufiOut.value = True
        else:
            # Move down
            ufiOut.value = False
            abiOut.value = True

        time.sleep(0.05)
        
        if time.monotonic() - timeStart > 5:
            break

    # Stop both outputs
    ufiOut.value = False
    abiOut.value = False
    return
    
#automaticGotoDest(153)  # Example: move to desk height of 150 cm

#time.sleep(2)  # Wait a bit before starting the main loop

#automaticGotoDest(139)

def everythingBlack():
    # Set display background to full black
    color_palette[0] = 0x000000  # Black
    inner_palette[0] = 0x000000  # Black

    ufiButton.fill_color = 0x000000
    ufiButton.outline_color = 0x000000
    ufiButton.selected_fill = 0x000000
    ufiButton.selected_outline = 0x000000
    ufiButton.label_color = 0x000000

    abiButton.fill_color = 0x000000
    abiButton.outline_color = 0x000000
    abiButton.selected_fill = 0x000000
    abiButton.selected_outline = 0x000000
    abiButton.label_color = 0x000000

    sensorText.color = 0x000000
    
def everythingNormal():
    # Set display background to original colors
    color_palette[0] = 0xAA0088  # Bright Green
    inner_palette[0] = 0xAA0088  # Purple

    ufiButton.fill_color = 0x4444AA
    ufiButton.outline_color = 0xFFFF00
    ufiButton.selected_fill = 0xAA4444
    ufiButton.selected_outline = 0xFFFFFF
    ufiButton.label_color = 0xFFFFFF

    abiButton.fill_color = 0x4444AA
    abiButton.outline_color = 0xFFFF00
    abiButton.selected_fill = 0xAA4444
    abiButton.selected_outline = 0xFFFFFF
    abiButton.label_color = 0xFFFFFF

    sensorText.color = 0xFFFF00

# Main loop
time.sleep(1)
lastTouch = time.monotonic()  # Initialize last touch time
currentDisp = "Normal"

while True:
    if counter % 5 == 0:
        touch = touchSensor.touch_point
        if touch:
            x, y, z = touch
            lastTouch = time.monotonic()
            #print("Touch at:", touch)
                # Check each button’s .contains(x, y)
            if ufiButton.contains((x, y)):# and constraintsMet("UFI"):
                ufiOut.value = True
                abiOut.value = False
                if not buttonVisualized and counter % 1 == 0:
                    abiButton.label = "ABI"
                    ufiButton.label = "(UFI)"
            elif abiButton.contains((x, y)):# and constraintsMet("ABI"):
                #print("Right button touched")
                ufiOut.value = False
                abiOut.value = True
                if not buttonVisualized and counter % 1 == 0:
                    ufiButton.label = "UFI"
                    abiButton.label = "(ABI)"
            else:
                # Touched outside both buttons
                #print("Touched outside buttons")
                ufiOut.value = False
                abiOut.value = False
                if not buttonVisualized and counter % 1 == 0:
                    ufiButton.label = "UFI"
                    abiButton.label = "ABI"
            buttonVisualized = True
        else:
            if buttonVisualized and counter % 1 == 0:
                #text_area.text = "Hello World! No Touch"
                # Optionally, clear button “checkmarks” when not touching:
                ufiButton.label = "UFI"
                abiButton.label = "ABI"
                buttonVisualized = False
            ufiOut.value = False
            abiOut.value = False

    # if not touched for 30 seconds
    if counter % 100 == 0:
        if time.monotonic() - lastTouch > 15:
            everythingBlack()
            currentDisp = "Black"
        elif currentDisp == "Black":
            everythingNormal()
            currentDisp = "Normal"
        
    if counter % 5 == 0:
        # Distance reading (unchanged)
        try:
            distance = distSensor.distance
            #print("Distance:", distance)
        except RuntimeError:
            # On timeout, don’t crash—just skip this cycle
            #print("Retrying!")
            pass
        
        data = np.roll(data, 1)
        data[-1] = distance
        
        filtered = np.sum(data * h)
        
        sensorText.text = f"Distance: {filtered:.2f} cm"
        
        #print("Filtered distance:", filtered)
    
    counter += 1
    time.sleep(0.005)
