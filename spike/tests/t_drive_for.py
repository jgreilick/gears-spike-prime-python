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

# DriveTrain distance moves, checked against GPS. World: test world (1.9 m clear ahead).
dt = DriveTrain(left_drive_smart, right_drive_smart, 157.08, 120, 50.8, MM, 1)
dt.set_drive_velocity(50, PERCENT)

p0 = pos_mm()
check_eq('drive_for_returns_True', dt.drive_for(FORWARD, 500, MM), True)
wait(300, MSEC)
p1 = pos_mm()
check('drive_for_500_MM', p1[1] - p0[1], 500, 15)
check('drive_for_500_MM_lateral', p1[0] - p0[0], 0, 20)
dt.drive_for(REVERSE, 300, MM)
wait(300, MSEC)
p2 = pos_mm()
check('drive_for_REVERSE_300_MM', p2[1] - p1[1], -300, 15)
dt.drive_for(FORWARD, 10, INCHES)
wait(300, MSEC)
p3 = pos_mm()
check('drive_for_10_INCHES', p3[1] - p2[1], 254, 15)
dt.drive_for(FORWARD, -200, MM)
wait(300, MSEC)
p4 = pos_mm()
check('drive_for_negative_distance', p4[1] - p3[1], -200, 15)
dt.drive_for(FORWARD, 300, MM, 100, PERCENT)
wait(300, MSEC)
p5 = pos_mm()
check('drive_for_300_at_100pct', p5[1] - p4[1], 300, 20)
r = dt.drive_for(FORWARD, 300, MM, 50, PERCENT, wait=False)
check_eq('wait_False_returns_False', r, False)
check_eq('is_moving_after_wait_False', dt.is_moving(), True)
while not dt.is_done():
    wait(20, MSEC)
wait(300, MSEC)
p6 = pos_mm()
check('wait_False_completes', p6[1] - p5[1], 300, 15)
dt.drive(FORWARD, 50, PERCENT)
wait(1000, MSEC)
check('drive_velocity_PERCENT', dt.velocity(PERCENT), 50, 5)
dt.stop()
wait(300, MSEC)
check('drive_1s_at_50pct_mm', pos_mm()[1] - p6[1], 175, 40)
check_eq('stop_is_done', dt.is_done(), True)
summary('t_drive_for')
