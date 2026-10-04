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

# Open-loop DriveTrain turns from track width (no gyro). Direction must be right; size is
# approximate, as on a real gyro-less V5 (tolerance 20 deg). World: test world.
dt = DriveTrain(left_drive_smart, right_drive_smart, 157.08, 120, 50.8, MM, 1)
dt.set_turn_velocity(50, PERCENT)

y0 = yaw()
check_eq('turn_for_returns_True', dt.turn_for(RIGHT, 90, DEGREES), True)
wait(300, MSEC)
y1 = yaw()
check('turn_for_RIGHT_90', y1 - y0, 90, 20)
dt.turn_for(LEFT, 90, DEGREES)
wait(300, MSEC)
y2 = yaw()
check('turn_for_LEFT_90', y2 - y1, -90, 20)
dt.turn_for(RIGHT, 0.25, TURNS)
wait(300, MSEC)
y3 = yaw()
check('turn_for_0.25_TURNS', y3 - y2, 90, 20)
dt.turn_for(RIGHT, -90, DEGREES)
wait(300, MSEC)
y4 = yaw()
check('turn_for_RIGHT_negative_angle', y4 - y3, -90, 20)
dt.turn(RIGHT, 30, PERCENT)
wait(500, MSEC)
dt.stop()
wait(300, MSEC)
check('turn_RIGHT_rotates_clockwise', sign(yaw() - y4), 1, 0)
y5 = yaw()
dt.turn(LEFT, 30, PERCENT)
wait(500, MSEC)
dt.stop()
wait(300, MSEC)
check('turn_LEFT_rotates_anticlockwise', sign(yaw() - y5), -1, 0)
summary('t_turn_for_open')
