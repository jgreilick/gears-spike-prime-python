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

# SmartDrive closed-loop turn_for on the inertial. World: test world.
drivetrain.set_turn_velocity(50, PERCENT)

def turn_wait_false():
    drivetrain.turn_for(RIGHT, 90, DEGREES, wait=False)

y0 = yaw()
check_eq('turn_for_returns_True', drivetrain.turn_for(RIGHT, 90, DEGREES), True)
wait(300, MSEC)
y1 = yaw()
check('turn_for_RIGHT_90', y1 - y0, 90, 3)
drivetrain.turn_for(LEFT, 90, DEGREES)
wait(300, MSEC)
y2 = yaw()
check('turn_for_LEFT_90', y2 - y1, -90, 3)
drivetrain.turn_for(RIGHT, 180, DEGREES, 30, PERCENT)
wait(300, MSEC)
y3 = yaw()
check('turn_for_RIGHT_180_at_30pct', y3 - y2, 180, 3)
drivetrain.turn_for(LEFT, 0.5, TURNS)
wait(300, MSEC)
y4 = yaw()
check('turn_for_LEFT_0.5_TURNS', y4 - y3, -180, 3)
drivetrain.set_turn_threshold(5)
drivetrain.turn_for(RIGHT, 90, DEGREES)
wait(300, MSEC)
y5 = yaw()
check('turn_threshold_5', y5 - y4, 90, 6)
drivetrain.set_turn_threshold(1)
check('rotation_matches_gyro', drivetrain.rotation(), y5 - y0, 0.5)
check_raises('wait_False_not_available', turn_wait_false, SimNotAvailable,
             'SmartDrive turns with wait=False is not available in the simulator.')
summary('t_smartdrive_turn')
