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

# Velocity units: PERCENT = share of the 800 deg/s sim cap, RPM x6, DPS; clamp note once.
# World: test world.
import vex, time

notes = []
def capture(*args, **kwargs):
    s = ' '.join([str(a) for a in args])
    if 'top out' in s:
        notes.append(s)
vex.print = capture

m = Motor(Ports.PORT1, GearSetting.RATIO_18_1, False)

def measure(spin_args, label, expected, tol):
    m.spin(*spin_args)
    wait(500, MSEC)
    p0 = m.position(DEGREES)
    t0 = time.time()
    wait(500, MSEC)
    rate = (m.position(DEGREES) - p0) / (time.time() - t0)
    m.stop()
    wait(300, MSEC)
    check(label, rate, expected, tol)

measure((FORWARD,), 'default_velocity_50pct_dps', 400, 40)
measure((FORWARD, 50, PERCENT), 'PERCENT_50_dps', 400, 40)
measure((FORWARD, 25, PERCENT), 'PERCENT_25_dps', 200, 20)
measure((FORWARD, 100, PERCENT), 'PERCENT_100_dps', 800, 80)
measure((FORWARD, 50, RPM), 'RPM_50_dps', 300, 30)
measure((FORWARD, 50), 'RPM_is_default_units_dps', 300, 30)
measure((FORWARD, 200, VelocityUnits.DPS), 'DPS_200_dps', 200, 20)
m.set_velocity(25, PERCENT)
measure((FORWARD,), 'set_velocity_25pct_dps', 200, 20)
check_eq('no_note_before_clamp', len(notes), 0)
measure((FORWARD, 200, RPM), 'RPM_200_clamped_dps', 800, 80)
measure((FORWARD, 150, PERCENT), 'PERCENT_150_clamped_dps', 800, 80)
check_eq('clamp_note_printed_once', len(notes), 1)

m.spin(FORWARD, 50, RPM)
wait(600, MSEC)
check('velocity_readback_RPM', m.velocity(RPM), 50, 5)
check('velocity_readback_PERCENT', m.velocity(PERCENT), 37.5, 4)
check('velocity_readback_DPS', m.velocity(VelocityUnits.DPS), 300, 30)
m.stop()
del vex.print
summary('t_motor_velocity_units')
