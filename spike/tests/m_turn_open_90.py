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

# One trial: open-loop DriveTrain.turn_for(RIGHT, 90) at 50%. World: test world.
dt = DriveTrain(left_drive_smart, right_drive_smart, 157.08, 120, 50.8, MM, 1)
y0 = yaw()
dt.turn_for(RIGHT, 90, DEGREES, 50, PERCENT)
wait(500, MSEC)
print('MEASURE turn_open_90_error_deg %.2f' % (yaw() - y0 - 90))
