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

# SmartDrive heading targets: shortest direction for headings, absolute for rotations. World: test world.
drivetrain.set_turn_velocity(50, PERCENT)

def heading_error(target):
    return (drivetrain.heading() - target + 180) % 360 - 180

drivetrain.turn_to_heading(90, DEGREES)
wait(300, MSEC)
check('to_heading_90_error', heading_error(90), 0, 3)
r0 = drivetrain.rotation()
drivetrain.turn_to_heading(0, DEGREES)
wait(300, MSEC)
check('to_heading_0_from_90_turns_left', drivetrain.rotation() - r0, -90, 3)
r0 = drivetrain.rotation()
drivetrain.turn_to_heading(270, DEGREES)
wait(300, MSEC)
check('to_heading_270_from_0_turns_left', drivetrain.rotation() - r0, -90, 3)
check('heading_270_error', heading_error(270), 0, 3)
r0 = drivetrain.rotation()
drivetrain.turn_to_heading(-45, DEGREES)
wait(300, MSEC)
check('to_heading_negative_45_error', heading_error(315), 0, 3)
check('to_heading_negative_45_turns_right', drivetrain.rotation() - r0, 45, 3)
drivetrain.set_rotation(0, DEGREES)
drivetrain.turn_to_rotation(450, DEGREES)
wait(300, MSEC)
check('to_rotation_450', drivetrain.rotation(), 450, 3)
drivetrain.turn_to_rotation(360, DEGREES)
wait(300, MSEC)
check('to_rotation_360_turns_left', drivetrain.rotation(), 360, 3)
drivetrain.turn_to_rotation(1.5, TURNS)
wait(300, MSEC)
check('to_rotation_1.5_TURNS', drivetrain.rotation(TURNS), 1.5, 0.01)
drivetrain.set_heading(90, DEGREES)
check('set_heading_90', drivetrain.heading(), 90, 0.5)
drivetrain.turn_to_heading(0, DEGREES)
wait(300, MSEC)
check('to_heading_0_after_set_heading', heading_error(0), 0, 3)
summary('t_turn_to_heading')
