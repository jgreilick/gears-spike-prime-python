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

# Distance (laser): far wall, near wall, nothing in range. Expected values come from GPS:
# wall face at Y = 400 mm, laser ray starts 77 mm ahead of the GPS (FINDINGS 8).
# V5 accuracy: +-15 mm below 200 mm, 5% above. No object -> 9999 mm (PROS firmware docs).
# World: test world.
WALL_Y = 400.0
LASER_AHEAD = 77.0

def expected():
    return WALL_Y - pos_mm()[1] - LASER_AHEAD

e = expected()
check('far_wall_MM', distance.object_distance(MM), e, 0.05 * e)
check('far_wall_INCHES', distance.object_distance(INCHES), e / 25.4, 0.05 * e / 25.4)
check('default_units_MM', distance.object_distance(), e, 0.05 * e)
check_eq('far_wall_detected', distance.is_object_detected(), True)

drivetrain.drive_for(FORWARD, 1200, MM, 100, PERCENT)
wait(300, MSEC)
e = expected()
check('mid_wall_MM', distance.object_distance(MM), e, 0.05 * e)

drivetrain.drive_for(FORWARD, e - 150, MM, 30, PERCENT)
wait(300, MSEC)
e = expected()
check('near_wall_MM', distance.object_distance(MM), e, 15)
check('near_wall_about_150', e, 150, 25)
check_eq('near_wall_detected', distance.is_object_detected(), True)

drivetrain.turn_for(RIGHT, 180, DEGREES, 30, PERCENT)
wait(300, MSEC)
check_eq('nothing_in_range_MM', distance.object_distance(MM), 9999.0)
check('nothing_in_range_INCHES', distance.object_distance(INCHES), 9999.0 / 25.4, 0.01)
check_eq('nothing_detected', distance.is_object_detected(), False)
summary('t_distance')
