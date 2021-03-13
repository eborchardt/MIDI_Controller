import digitalio
import board
import usb_midi
import adafruit_midi
from adafruit_midi.control_change import ControlChange
from adafruit_debouncer import Debouncer
import rotaryio
import simpleio

# Initialize midi in/out on channel 1
midi = adafruit_midi.MIDI(midi_in=usb_midi.ports[0],
                          midi_out=usb_midi.ports[1],
                          in_channel=0,
                          out_channel=0)

# Initialize the toggle type buttons
# TODO: Use a matrix here
foot_left = digitalio.DigitalInOut(board.D7)
foot_left.switch_to_input(pull=digitalio.Pull.DOWN)
foot_right = digitalio.DigitalInOut(board.D8)
foot_right.switch_to_input(pull=digitalio.Pull.DOWN)
br = False
bl = False

# Initialize the momentary type buttons
# Define the pins here
button_pins = [board.D3, board.D4]
# Define some matrixes to hold the buttons and button states
buttons = []
buttons_state = []
# Populate matrixes
for pin in button_pins:
    button_pin = digitalio.DigitalInOut(pin)
    button_pin.switch_to_input(pull=digitalio.Pull.DOWN)
    buttons.append(button_pin)
    button_state = Debouncer(button_pin)
    buttons_state.append(button_state)

# Initialize the LED
led = digitalio.DigitalInOut(board.D6)
led.direction = digitalio.Direction.OUTPUT

# Initialize the rotary encoder
encoder = rotaryio.IncrementalEncoder(board.D1, board.D2)
last_position = encoder.position


# Functions Begin Here

# This function will scan all button states for changes
def checkForButtonPress():
        for i in range(2):
            buttons_state[i].update()
            thebutton = buttons_state[i]
            if thebutton.rose:
                #  if button is pressed...
                print("button pressed: ", i)
            if thebutton.fell:
                #  if the button is released...
                print("button released: ", i)

# Main Loop
while True:
    checkForButtonPress()

    # TODO: Make a toggle button function
    if foot_left.value:
        br = ~br
        br = br & 0x7F
        midi.send(ControlChange(48, br))
        print('48', br)
        while foot_left.value:
            pass

    if foot_right.value:
        br = ~br
        br = br & 0x7F
        midi.send(ControlChange(49, br))
        print('49', br)
        while foot_right.value:
            pass

    # TODO: Make a MIDI receive function
    msg = midi.receive()
    if isinstance(msg, ControlChange):
        print("control=", msg.control)
        print("value=", msg.value)
        print("channel=", msg.channel)
        if msg.control == 47:
            if msg.value == 127:
                led.value = True
            if msg.value == 0:
                led.value = False
    # Print all MIDI messages for debugging
    elif msg is None:
        pass
    else:
        print(msg)

    # This rotary encoder will send out a
    # range of 0-127 on MIDI ControlChange 20
    # TODO: Make this into a function for additional encoders
    position = encoder.position
    potSimPosition = int(simpleio.map_range(position, 0, 15, 0, 127))
    if position < 0:
        position = 0
        encoder.position = 0
    if position > 15:
        position = 15
        encoder.position = 15
    if last_position is None or position != last_position:
        midi.send(ControlChange(20, potSimPosition))
        # print(position)
        print(potSimPosition)
    last_position = position