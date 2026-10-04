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

# Motor.spin_for / spin_to_position / position / is_done / timeout on PORT1. World: test world.
m = Motor(Ports.PORT1, GearSetting.RATIO_18_1, False)
m.set_velocity(50, PERCENT)

m.spin_for(FORWARD, 360, DEGREES)
check('spin_for_360_DEGREES', m.position(DEGREES), 360, 15)
check('position_TURNS', m.position(TURNS), 1.0, 0.05)
m.spin_for(FORWARD, 1, TURNS)
check('spin_for_1_TURNS', m.position(DEGREES), 720, 25)
m.spin_to_position(0, DEGREES)
check('spin_to_position_0', m.position(DEGREES), 0, 15)
m.set_position(100, DEGREES)
check('set_position_100', m.position(DEGREES), 100, 0.5)
m.reset_position()
check('reset_position', m.position(DEGREES), 0, 0.5)

r = m.spin_for(FORWARD, 720, DEGREES, 50, PERCENT, wait=False)
check_eq('wait_False_returns_False', r, False)
check_eq('is_done_while_moving', m.is_done(), False)
check_eq('is_spinning_while_moving', m.is_spinning(), True)
while not m.is_done():
    wait(20, MSEC)
check('wait_False_completes', m.position(DEGREES), 720, 20)

m.reset_position()
r = m.spin_for(FORWARD, 360, DEGREES, 50, PERCENT, wait=True)
check_eq('wait_True_returns_True', r, True)

m.set_timeout(200, MSEC)
check('get_timeout_ms', m.get_timeout(), 200, 0.01)
m.reset_position()
r = m.spin_for(FORWARD, 3600, DEGREES, 50, PERCENT)
check_eq('timeout_returns_False', r, False)
check('timeout_stops_early_deg', m.position(DEGREES), 80, 60)
summary('t_motor_spin_for')
