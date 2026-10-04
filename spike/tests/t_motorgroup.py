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

# MotorGroup over the two drive motors. World: test world.
g = MotorGroup(left_drive_smart, right_drive_smart)
check_eq('count', g.count(), 2)
g.set_velocity(50, PERCENT)
p0 = pos_mm()
g.spin_for(FORWARD, 360, DEGREES)
wait(300, MSEC)
check('spin_for_360_position', g.position(DEGREES), 360, 15)
check('spin_for_360_drives_forward_mm', pos_mm()[1] - p0[1], 157, 15)
check('left_motor_moved', left_drive_smart.position(DEGREES), 360, 15)
check('right_motor_moved', right_drive_smart.position(DEGREES), 360, 15)
g.set_position(0, DEGREES)
check('set_position', g.position(DEGREES), 0, 0.5)
g.spin_for(REVERSE, 180, DEGREES, wait=False)
check_eq('is_done_while_moving', g.is_done(), False)
while not g.is_done():
    wait(20, MSEC)
check('wait_False_completes', g.position(DEGREES), -180, 15)
g.spin(FORWARD, 30, PERCENT)
wait(500, MSEC)
check_eq('spin_is_spinning', g.is_spinning(), True)
g.stop()
wait(300, MSEC)
check_eq('stop_is_done', g.is_done(), True)
summary('t_motorgroup')
