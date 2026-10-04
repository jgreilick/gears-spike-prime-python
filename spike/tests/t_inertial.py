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

# Inertial heading/rotation/offsets against the raw gyro. Clockwise positive. World: test world.
check_eq('calibrate_returns', drivetrain_inertial.calibrate(), None)
check_eq('is_calibrating_False', drivetrain_inertial.is_calibrating(), False)
check('heading_at_start_error', (drivetrain_inertial.heading() + 180) % 360 - 180, 0, 0.5)
check('rotation_at_start', drivetrain_inertial.rotation(), 0, 0.5)
y0 = yaw()
drivetrain.turn_for(RIGHT, 90, DEGREES, 30, PERCENT)
wait(300, MSEC)
check('rotation_matches_gyro', drivetrain_inertial.rotation(), yaw() - y0, 0.2)
check('heading_right_positive', drivetrain_inertial.heading(), 90, 3)
check('heading_TURNS', drivetrain_inertial.heading(TURNS), 0.25, 0.01)
drivetrain.turn_for(LEFT, 120, DEGREES, 30, PERCENT)
wait(300, MSEC)
check('heading_wraps_to_330', drivetrain_inertial.heading(), 330, 3)
check('rotation_negative', drivetrain_inertial.rotation(), -30, 3)
drivetrain_inertial.set_heading(90, DEGREES)
check('set_heading', drivetrain_inertial.heading(), 90, 0.2)
check('set_heading_keeps_rotation', drivetrain_inertial.rotation(), -30, 3)
drivetrain_inertial.set_rotation(-180, DEGREES)
check('set_rotation', drivetrain_inertial.rotation(), -180, 0.2)
drivetrain_inertial.set_rotation(1, TURNS)
check('set_rotation_TURNS', drivetrain_inertial.rotation(), 360, 0.2)
drivetrain_inertial.reset_heading()
check('reset_heading', drivetrain_inertial.heading(), 0, 0.2)
drivetrain_inertial.reset_rotation()
check('reset_rotation', drivetrain_inertial.rotation(), 0, 0.2)
y1 = yaw()
drivetrain.turn_for(RIGHT, 45, DEGREES, 30, PERCENT)
wait(300, MSEC)
check('after_reset_tracks_gyro', drivetrain_inertial.rotation(), yaw() - y1, 0.2)
summary('t_inertial')
