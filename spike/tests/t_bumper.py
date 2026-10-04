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

# Bumpers on 3-wire A/B. Square hit presses both; 25 deg angled hit presses left only.
# World: test world (wall face 1900 mm ahead).
check_eq('left_released_at_start', left_bumper.pressing(), False)
check_eq('right_released_at_start', right_bumper.pressing(), False)
drivetrain.drive_for(FORWARD, 1650, MM, 100, PERCENT)

def drive_until_bump():
    drivetrain.drive(FORWARD, 20, PERCENT)
    t = Timer()
    while not (left_bumper.pressing() or right_bumper.pressing()) and t.time(SECONDS) < 6:
        wait(5, MSEC)
    wait(300, MSEC)
    l, r = left_bumper.pressing(), right_bumper.pressing()
    drivetrain.stop()
    return l, r

l, r = drive_until_bump()
check_eq('square_hit_left', l, True)
check_eq('square_hit_right', r, True)
drivetrain.drive_for(REVERSE, 200, MM, 50, PERCENT)
wait(200, MSEC)
check_eq('left_released_after_backoff', left_bumper.pressing(), False)
check_eq('right_released_after_backoff', right_bumper.pressing(), False)
drivetrain.turn_for(RIGHT, 25, DEGREES, 30, PERCENT)
l, r = drive_until_bump()
check_eq('angled_hit_left', l, True)
check_eq('angled_hit_right', r, False)
summary('t_bumper')
