import pygame.midi
from time import sleep, time_ns
import sys

class analog:
    cc: int
    value: float
    prev_value: float
    division: float = 8
    scaling: int = 127

    def __init__(self, cc: int, start_value: float = 0.5, division: int = 8, scaling: int = 127):
        self.value = start_value
        self.cc = cc
        self.prev_value = start_value

    def update(self, value):
        self.value = clamp(self.value + value / self.division, 0, 1)

class bt_state:
    state: bool = False
    prev_state: bool = False
    button_index: int
    joystick: pygame.joystick = None

    def __init__(self, joystick, index):
        self.button_index = index
        self.joystick = joystick

    def __bool__(self):
        return self.state

    def update(self):
        self.state = self.joystick.get_button(self.button_index) == 1

    def post_update(self):
        self.prev_state = self.state

    @property
    def changed(self):
        return self.state != self.prev_state

class button:
    note: int
    value: bool
    prev_value: bool
    last_on_time: int
    selected: bool = False
    state: bt_state

    def __init__(self, note, bt: bt_state):
        self.note = note
        self.value = False
        self.prev_value = False
        self.last_on_time = time_ns()
        self.state = bt

    def select(self):
        self.selected = True

    def update(self):
        value = self.state.state
        if value and not self.selected:
            return
        self.selected = False
        if value != self.prev_value:
            if time_ns() - self.last_on_time < 10000000: # 10ms debounce
                return
            else:
                self.last_on_time = time_ns()
                self.value = value

    @property
    def changed(self):
        return self.value != self.prev_value

def clamp(n, smallest, largest): return max(smallest, min(n, largest))

pygame.joystick.init()
pygame.display.init()
pygame.midi.init()
pygame.event.pump()

print("\n")

joysticks = [pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())]
for k, v in enumerate(joysticks):
    print(f"JOYSTICK DEVICE {k}: {v.get_name()}")
index = int(input("Please enter a device id: "))
selected_joystick = joysticks[index]
print(f"Selected {selected_joystick.get_name()}")

midi_outputs = [(pygame.midi.get_device_info(x), x) for x in range(pygame.midi.get_count()) if pygame.midi.get_device_info(x)[3] == 1]
for k, v in enumerate(midi_outputs):
    print(f"MIDI DEVICE {k}: {v[0][1]}")
index = int(input("Please enter an output device id: "))
selected_output = pygame.midi.Output(midi_outputs[index][1])

c1_pitch = 0.5
c1_scratching = False
c2_scratching = False
c2_pitch = 0.5

bank2 = False

analogs = {}
analogs["channel1_fx"] = analog(22)
analogs["channel1_lpf"] = analog(23)
analogs["channel2_fx"] = analog(24)
analogs["channel2_lpf"] = analog(25)
analogs["crossfader"] = analog(26, division=4)

bts = {}
bt_start = bts["bt_start"] = bt_state(selected_joystick, 0)
bt_a = bts["bt_a"] = bt_state(selected_joystick, 1)
bt_b = bts["bt_b"] = bt_state(selected_joystick, 2)
bt_c = bts["bt_c"] = bt_state(selected_joystick, 3)
bt_d = bts["bt_d"] = bt_state(selected_joystick, 4)
bt_fx_l = bts["bt_fx_l"] = bt_state(selected_joystick, 5)
bt_fx_r = bts["bt_fx_r"] = bt_state(selected_joystick, 6)
bt_upper_left = bts["bt_upper_left"] = bt_state(selected_joystick, 7)
bt_lower_left = bts["bt_lower_left"] = bt_state(selected_joystick, 8)
bt_coin = bts["bt_coin"] = bt_state(selected_joystick, 9)

buttons = {}
buttons["channel1_play"] = button(0, bt_lower_left)
buttons["channel1_fxtoggle"] = button(2, bt_b)
buttons["channel2_play"] = button(1, bt_coin)
buttons["channel2_fxtoggle"] = button(3, bt_c)

buttons["switch_bank"] = button(127, bt_upper_left)  # shouldn't be mapped but go for it

buttons["bt_a_bank1"] = button(4, bt_a)
buttons["bt_b_bank1"] = button(5, bt_b)
buttons["bt_c_bank1"] = button(6, bt_c)
buttons["bt_d_bank1"] = button(7, bt_d)

buttons["bt_a_bank2"] = button(8, bt_a)
buttons["bt_b_bank2"] = button(9, bt_b)
buttons["bt_c_bank2"] = button(10, bt_c)
buttons["bt_d_bank2"] = button(11, bt_d)

left_knob_prev = 0
right_knob_prev = 0

while True:
    pygame.event.pump()
    currentValue = int(((selected_joystick.get_axis(selected_axis)+1)/2)*64)
    for bt in bts.values():
        bt.update()

    left_knob = selected_joystick.get_axis(0) # LEFT 0, RIGHT - 1
    right_knob = selected_joystick.get_axis(1) # LEFT 0, RIGHT - 1
    knob_left_delta = left_knob-left_knob_prev
    knob_right_delta = right_knob-right_knob_prev

    # correct for wrap-around
    if knob_left_delta > 1.0:
        knob_left_delta -= 2
    elif knob_left_delta < -1.0:
        knob_left_delta += 2
    if knob_right_delta > 1.0:
        knob_right_delta -= 2
    elif knob_right_delta < -1.0:
        knob_right_delta += 2

    if c1_scratching:
        if not bt_a:
            c1_scratching = False
            selected_output.write_short(0xb0, 62, 0x00)
        else:
            selected_output.write_short(0xb0, 63, 64 + int((left_knob - left_knob_prev) * 4 * 64))

    if c2_scratching and not bt_d:
        if not bt_d:
            c2_scratching = False
            selected_output.write_short(0xb0, 3, 0x00)
        else:
            selected_output.write_short(0xb0, 64, 64 + int((right_knob - right_knob_prev) * 4 * 64))

    if bt_start:
        if bt_a and not bt_a:
            c1_pitch = clamp(c1_pitch-knob_left_delta/8, 0, 1)
            if abs(knob_left_delta) > 0:
                selected_output.write_short(0xb0, 20, int(c1_pitch*127))
        elif bt_a.changed:
            if bt_a:
                c1_scratching = True
                selected_output.write_short(0xb0, 62, 127)
        if bt_c and not bt_d:
            c2_pitch = clamp(c2_pitch-knob_right_delta/8, 0, 1)
            if abs(knob_right_delta) > 0:
                selected_output.write_short(0xb0, 21, int(c2_pitch*127))
        elif bt_d.changed:
            if bt_d:
                c2_scratching = True
                selected_output.write_short(0xb0, 3, 127)
    elif bt_fx_l and bt_fx_r:
        analogs["crossfader"].update(knob_left_delta)
    elif bt_fx_l:
        if bt_a:
            analogs["channel1_fx"].update(knob_left_delta)
            analogs["channel1_lpf"].update(knob_right_delta)
        buttons["channel1_fxtoggle"].select()
    elif bt_fx_r:
        if bt_d:
            analogs["channel2_fx"].update(knob_right_delta)
            analogs["channel2_lpf"].update(knob_left_delta)
        buttons["channel2_fxtoggle"].select()
    else:
        buttons["channel1_play"].select()
        buttons["channel2_play"].select()
        buttons["switch_bank"].select()
        if not bank2:
            buttons["bt_a_bank1"].select()
            buttons["bt_b_bank1"].select()
            buttons["bt_c_bank1"].select()
            buttons["bt_d_bank1"].select()
        else:  # TODO: SELECTION TREE MODEL
            buttons["bt_a_bank2"].select()
            buttons["bt_b_bank2"].select()
            buttons["bt_c_bank2"].select()
            buttons["bt_d_bank2"].select()

    for button in buttons.values():
        button.update()

    for cc in analogs.values():
        if cc.value != cc.prev_value:
            selected_output.write_short(0xb0, cc.cc, int(cc.value * cc.scaling))
        cc.prev_value = cc.value

    for button in buttons.values():
        if button.value != button.prev_value:
            if button.value:
                selected_output.write_short(0x9c, button.note, 127)
                if button is buttons["switch_bank"]:
                    bank2 = not bank2
                    print(f"bank2: {bank2}")
            else:
                selected_output.write_short(0x8c, button.note, 127)
        button.prev_value = button.value

    for bt in bts.values():
        bt.post_update()

    left_knob_prev = left_knob
    right_knob_prev = right_knob

    sleep(0.001)
