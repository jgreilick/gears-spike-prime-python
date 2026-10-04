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

# One trial: drive_for 800 mm at 50%. Prints distance and lateral error from GPS. World: test world.
p0 = pos_mm()
drivetrain.drive_for(FORWARD, 800, MM, 50, PERCENT)
wait(500, MSEC)
p1 = pos_mm()
print('MEASURE drive_800_error_mm %.1f' % (p1[1] - p0[1] - 800))
print('MEASURE drive_800_lateral_mm %.1f' % (p1[0] - p0[0]))
