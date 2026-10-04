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

# One trial: 4 x (drive 300 mm, turn right 90) open-loop. World: test world.
dt = DriveTrain(left_drive_smart, right_drive_smart, 157.08, 120, 50.8, MM, 1)
p0 = pos_mm()
y0 = yaw()
for side in range(4):
    dt.drive_for(FORWARD, 300, MM, 50, PERCENT)
    dt.turn_for(RIGHT, 90, DEGREES, 50, PERCENT)
wait(500, MSEC)
print('MEASURE square_open_heading_error_deg %.2f' % (yaw() - y0 - 360))
print('MEASURE square_open_position_error_mm %.1f' % travelled_mm(p0, pos_mm()))
