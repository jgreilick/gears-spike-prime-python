#region VEXcode Generated Robot Configuration
from vex import *

brain = Brain()

left_drive_smart = Motor(Ports.PORT1, GearSetting.RATIO_18_1, False)
right_drive_smart = Motor(Ports.PORT10, GearSetting.RATIO_18_1, True)
drivetrain_inertial = Inertial(Ports.PORT3)
drivetrain = SmartDrive(left_drive_smart, right_drive_smart, drivetrain_inertial, 157.08, 120, 50.8, MM, 1)
distance = Distance(Ports.PORT4)
left_bumper = Bumper(brain.three_wire_port.a)
right_bumper = Bumper(brain.three_wire_port.b)
#endregion VEXcode Generated Robot Configuration

from vex import SimNotAvailable
from vextest import *

# vexsim Pen state via the raw pen on in8; the trace itself is checked from JS. World: test world.
import simPython
from vexsim import *
raw = simPython.Pen('in8')


def is_down():
    # simPython.Pen.isDown() returns a raw JS boolean; `not` turns it into a Python bool.
    return not (not raw.isDown())

pen = Pen()
check_eq('up_at_start', is_down(), False)
pen.move(DOWN)
check_eq('move_DOWN', is_down(), True)
for c in (BLACK, RED, GREEN, BLUE):
    pen.set_pen_color(c)
    check_eq('set_pen_color_' + repr(c) + '_keeps_down', is_down(), True)
for w in (EXTRA_THIN, THIN, MEDIUM, WIDE, EXTRA_WIDE):
    pen.set_pen_width(w)
    check_eq('set_pen_width_' + repr(w), is_down(), True)
pen.set_pen_color_rgb(225, 112, 52, 100)
check_eq('set_pen_color_rgb_100', is_down(), True)
pen.set_pen_color(BLUE)
pen.set_pen_width(MEDIUM)
drivetrain.drive_for(FORWARD, 200, MM, 50, PERCENT)
pen.move(UP)
check_eq('move_UP', is_down(), False)

def bad_color():
    pen.set_pen_color('blue')
def bad_width():
    pen.set_pen_width(3)
def bad_move():
    pen.move(True)
def rgb_range():
    pen.set_pen_color_rgb(300, 0, 0, 100)
check_raises('bad_color', bad_color, ValueError)
check_raises('bad_width', bad_width, ValueError)
check_raises('bad_move', bad_move, ValueError)
check_raises('rgb_out_of_range', rgb_range, ValueError)
summary('t_pen')
