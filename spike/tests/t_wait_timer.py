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

# wait() units and brain.timer / Timer. World: any.
import time

t0 = time.time()
wait(500, MSEC)
check('wait_500_MSEC_ms', (time.time() - t0) * 1000, 500, 40)
t0 = time.time()
wait(0.5, SECONDS)
check('wait_0.5_SECONDS_ms', (time.time() - t0) * 1000, 500, 40)
t0 = time.time()
wait(300)
check('wait_default_units_MSEC_ms', (time.time() - t0) * 1000, 300, 40)

brain.timer.clear()
wait(300, MSEC)
check('timer_time_default_MSEC', brain.timer.time(), 300, 40)
check('timer_time_SECONDS', brain.timer.time(SECONDS), 0.3, 0.04)
brain.timer.clear()
check('timer_clear_resets', brain.timer.time(MSEC), 0, 20)

t = Timer()
wait(200, MSEC)
check('Timer_new_counts_from_create', t.time(MSEC), 200, 40)
summary('t_wait_timer')
