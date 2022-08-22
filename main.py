import pygame.midi
from time import sleep
import sys

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
print(f"{selected_joystick.get_numaxes()} axes available")
print("Please move the axis to use for scratching")
axis_values = []
for i in range(selected_joystick.get_numaxes()):
    axis_values.append(selected_joystick.get_axis(i))
selected_axis = 2
# while True:
#     pygame.event.pump()
#     breakout = False
#     for i in range(selected_joystick.get_numaxes()):
#         if abs(selected_joystick.get_axis(i) - axis_values[i]) >= 0.5:
#             selected_axis = i
#             breakout = True
#             break
#     if breakout:
#         break

print(f"Selected axis: {selected_axis}\n")

midi_outputs = [(pygame.midi.get_device_info(x), x) for x in range(pygame.midi.get_count()) if pygame.midi.get_device_info(x)[3] == 1]
for k, v in enumerate(midi_outputs):
    print(f"MIDI DEVICE {k}: {v[0][1]}")
index = int(input("Please enter an output device id: "))
selected_output = pygame.midi.Output(midi_outputs[index][1])

c1_pitch = 0.5
c2_pitch = 0.5
filter_freq = 0.5

left_knob_prev = 0
right_knob_prev = 0
bt_start_prev = False
bt_a_prev = False
bt_b_prev = False
bt_c_prev = False
bt_d_prev = False
bt_fx_l_prev = False
bt_fx_r_prev = False
bt_coin_prev = False
prevScratchValue = 0
base = 0
while True:
    pygame.event.pump()
    currentValue = int(((selected_joystick.get_axis(selected_axis)+1)/2)*64)

    bt_start = selected_joystick.get_button(0)
    bt_a = selected_joystick.get_button(1)
    bt_b = selected_joystick.get_button(2)
    bt_c = selected_joystick.get_button(3)
    bt_d = selected_joystick.get_button(4)
    bt_fx_l = selected_joystick.get_button(5)
    bt_fx_r = selected_joystick.get_button(6)
    bt_coin = selected_joystick.get_button(9)

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

    #channel 1 scratching
    if bt_fx_l:
        selected_output.write_short(0xb0, 63, 64 + int((left_knob - left_knob_prev) * 4 * 64))

    if bt_fx_l != bt_fx_l_prev:
        if bt_fx_l:
            selected_output.write_short(0xb0, 62, 127)
        else:
            selected_output.write_short(0xb0, 62, 0x00)

    #channel 2 scratching
    if bt_fx_r:
        selected_output.write_short(0xb0, 64, 64+int((right_knob-right_knob_prev)*4*64))
    if bt_fx_r != bt_fx_r_prev:
        if bt_fx_r:
            selected_output.write_short(0xb0, 3, 127)
        else:
            selected_output.write_short(0xb0, 3, 0x00)

    if bt_a != bt_a_prev:
        if bt_a:
            selected_output.write_short(0x9c, 1, 127)
        else:
            selected_output.write_short(0x8c, 1, 127)

    if bt_b != bt_b_prev:
        if bt_b:
            selected_output.write_short(0x9c, 2, 127)
        else:
            selected_output.write_short(0x8c, 2, 127)

    if bt_c != bt_c_prev:
        if bt_c:
            selected_output.write_short(0x9c, 3, 127)
        else:
            selected_output.write_short(0x8c, 3, 127)

    if bt_d != bt_d_prev:
        if bt_d:
            selected_output.write_short(0x9c, 4, 127)
        else:
            selected_output.write_short(0x8c, 4, 127)

    if not bt_fx_l and not bt_fx_r:
        if bt_start:
            c1_pitch = clamp(c1_pitch+knob_left_delta/8, 0, 1)
            c2_pitch = clamp(c2_pitch+knob_right_delta/8, 0, 1)
            if abs(knob_left_delta) > 0:
                selected_output.write_short(0xb0, 20, int(c1_pitch*127))
            if abs(knob_right_delta) > 0:
                selected_output.write_short(0xb0, 21, int(c2_pitch*127))
        else:
            filter_freq = clamp(filter_freq+knob_left_delta/8, 0, 1)
            if abs(knob_left_delta) > 0:
                selected_output.write_short(0xb0, 22, int(filter_freq*127))


    # if bt_start and not bt_start_prev:
    #     print("pressed start")
    # if bt_a and not bt_a_prev:
    #     print("pressed a")
    # if bt_b and not bt_b_prev:
    #     print("pressed b")
    # if bt_c and not bt_c_prev:
    #     print("pressed c")
    # if bt_d and not bt_d_prev:
    #     print("pressed d")
    # if bt_fx_l and not bt_fx_l_prev:
    #     print("pressed fx l")
    # if bt_fx_r and not bt_fx_r_prev:
    #     print("pressed fx r")
    # if bt_coin and not bt_coin_prev:
    #     print("pressed coin insert")

    bt_start_prev = bt_start
    bt_a_prev = bt_a
    bt_b_prev = bt_b
    bt_c_prev = bt_c
    bt_d_prev = bt_d
    bt_fx_l_prev = bt_fx_l
    bt_fx_r_prev = bt_fx_r
    bt_coin_prev = bt_coin
    left_knob_prev = left_knob
    right_knob_prev = right_knob
    sleep(0.001)
