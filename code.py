import board
import displayio
import terminalio
import time
import digitalio

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
display = HX8357(display_bus, width=480, height=320)

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
sensorText.y = 30
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
        print("Too close to PC, only allow UFI")
        abiOut.value = False
        return False
    elif distance < 145 and direction == "UFI":
        print("Too high up, only allow ABI")
        ufiOut.value = False
        return False
    return True

def automaticGotoDest(desiredDeskHeight):
    distance = 0
    timeStart = time.monotonic()
    while distance - desiredDeskHeight < 1:
        try:
            distance = distSensor.distance
            print("Distance:", distance)
            sensorText.text = f"Distance: {distance:.2f} cm"
        except RuntimeError:
            # On timeout, don’t crash—just skip this cycle
            print("Retrying!")
            pass
        # Move down
        abiOut.value = True
        ufiOut.value = False
        time.sleep(0.05)
        if time.monotonic() - timeStart > 5:
            print("Stopping automatic movement after 5 seconds")
            break
    while distance - desiredDeskHeight > -1:
        try:
            distance = distSensor.distance
            print("Distance:", distance)
            sensorText.text = f"Distance: {distance:.2f} cm"
        except RuntimeError:
            # On timeout, don’t crash—just skip this cycle
            print("Retrying!")
            pass
        # Move up
        ufiOut.value = True
        abiOut.value = False
        time.sleep(0.05)
        if time.monotonic() - timeStart > 5:
            print("Stopping automatic movement after 5 seconds")
            break
    # Stop both outputs
    ufiOut.value = False
    abiOut.value = False
    return
    
#automaticGotoDest(147)  # Example: move to desk height of 150 cm
        
# Main loop
while True:
    if counter % 10 == 0:
        touch = touchSensor.touch_point
        if touch:
            x, y, z = touch
            print("Touch at:", touch)
                # Check each button’s .contains(x, y)
            if ufiButton.contains((x, y)):# and constraintsMet("UFI"):
                ufiOut.value = True
                abiOut.value = False
                if not buttonVisualized:
                    ufiButton.label = "(UFI)"
                    abiButton.label = "ABI"
            elif abiButton.contains((x, y)):# and constraintsMet("ABI"):
                print("Right button touched")
                ufiOut.value = False
                abiOut.value = True
                if not buttonVisualized:
                    ufiButton.label = "UFI"
                    abiButton.label = "(ABI)"
            else:
                # Touched outside both buttons
                print("Touched outside buttons")
                ufiOut.value = False
                abiOut.value = False
                if not buttonVisualized:
                    ufiButton.label = "UFI"
                    abiButton.label = "ABI"
            buttonVisualized = True
        else:
            if buttonVisualized:
                #text_area.text = "Hello World! No Touch"
                # Optionally, clear button “checkmarks” when not touching:
                ufiButton.label = "UFI"
                abiButton.label = "ABI"
                buttonVisualized = False
            ufiOut.value = False
            abiOut.value = False

    if counter % 20 == 0:
        # Distance reading (unchanged)
        try:
            distance = distSensor.distance
            print("Distance:", distance)
            sensorText.text = f"Distance: {distance:.2f} cm"
        except RuntimeError:
            # On timeout, don’t crash—just skip this cycle
            print("Retrying!")
            pass
    
    counter += 1
    time.sleep(0.005)
