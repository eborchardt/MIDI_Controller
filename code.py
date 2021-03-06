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

toggles = [board.GP16, board.GP17, board.GP18, board.GP19]
momentaries = [board.GP12, board.GP13, board.GP14, board.GP15]
buttons = []
# There is no safeguard in place if you go over the number of available MIDI controls
# Be sure to pay attention to how many buttons you have connected
midicontrols = [3,9,14,15,20,21,22,23,24,25,26,27,28,29,30,31]
nextcontrol = 0

class Button:
    def __init__(
            self,
            mode,
            pin,
            midicontrol
    ):
        self.mode = mode
        self.pin = digitalio.DigitalInOut(pin)
        self.pin.direction = digitalio.Direction.INPUT
        self.pin.pull = digitalio.Pull.DOWN
        self.state = Debouncer(self.pin)
        self.togglestate = 0
        self.midicontrol = midicontrol

    def check():
        for each in buttons:
            each.state.update()
            if each.state.rose:
                # print("button press", each.mode)
                each.togglestate = ~each.togglestate
                each.togglestate = each.togglestate & 0x7F
                midi.send(ControlChange(each.midicontrol, each.togglestate))
                print("CC:", each.midicontrol, each.togglestate)
            if each.state.fell:
                # print("button released", each.mode)
                if each.mode == "momentary":
                    each.togglestate = ~each.togglestate
                    each.togglestate = each.togglestate & 0x7F
                    midi.send(ControlChange(each.midicontrol, each.togglestate))
                    print("CC:", each.midicontrol, each.togglestate)

for each in toggles:
    newbutton = Button("toggle", each, midicontrols[nextcontrol])
    nextcontrol += 1
    buttons.append(newbutton)

for each in momentaries:
    newbutton = Button("momentary", each, midicontrols[nextcontrol])
    nextcontrol += 1
    buttons.append(newbutton)

# Initialize the LED
# I'm not currently using the LED for anything other than a debugging tool at this time
led = digitalio.DigitalInOut(board.GP25)
led.direction = digitalio.Direction.OUTPUT

# Initialize the rotary encoder
encoder = rotaryio.IncrementalEncoder(board.GP21, board.GP22)
last_position = encoder.position

def midireceive():
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


# Main Loop
while True:
    Button.check()
    midireceive()

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
