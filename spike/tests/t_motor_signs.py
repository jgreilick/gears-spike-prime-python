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

# Sign table: direction x value sign x velocity sign x reversed, for spin_for and spin.
# Position moves treat velocity as a magnitude (PROS: "maximum allowable velocity").
# spin() with a negative velocity reverses. Motor position is in the motor's own frame;
# the raw outA wheel turns the opposite way when reversed=True. World: test world.
for rev in (False, True):
    m = Motor(Ports.PORT1, GearSetting.RATIO_18_1, rev)
    tag = 'rev' if rev else 'fwd'
    for d in (FORWARD, REVERSE):
        for v in (90, -90):
            for vel in (40, -40):
                exp = (1 if d is FORWARD else -1) * sign(v) * 90
                m.reset_position()
                raw0 = raw_left_deg()
                m.spin_for(d, v, DEGREES, vel, PERCENT)
                name = 'spin_for_%s_%s_%+d_vel%+d' % (tag, d, v, vel)
                check(name + '_position', m.position(DEGREES), exp, 15)
                check(name + '_wheel', raw_left_deg() - raw0, exp * (-1 if rev else 1), 15)
    for d in (FORWARD, REVERSE):
        for vel in (30, -30):
            exp_sign = (1 if d is FORWARD else -1) * sign(vel)
            m.reset_position()
            raw0 = raw_left_deg()
            m.spin(d, vel, PERCENT)
            wait(400, MSEC)
            m.stop()
            wait(200, MSEC)
            name = 'spin_%s_%s_vel%+d' % (tag, d, vel)
            check(name + '_position_sign', sign(m.position(DEGREES)), exp_sign, 0)
            check(name + '_position_moved', abs(m.position(DEGREES)), 80, 50)
            check(name + '_wheel_sign', sign(raw_left_deg() - raw0), exp_sign * (-1 if rev else 1), 0)
summary('t_motor_signs')
