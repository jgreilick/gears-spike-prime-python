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

# Devices on unused ports, and the wrong device on a used port, raise. World: any.
class Make(object):
    def __init__(self, cls, port):
        self.cls = cls
        self.port = port
    def __call__(self):
        self.cls(self.port)

used = [1, 3, 4, 10]
for i in range(1, 22):
    if i in used:
        continue
    check_raises('Motor_PORT%d' % i, Make(Motor, getattr(Ports, 'PORT%d' % i)), SimNotAvailable,
                 'Nothing is plugged into PORT%d on the sim robot.' % i)
check_raises('Distance_PORT7', Make(Distance, Ports.PORT7), SimNotAvailable,
             'Nothing is plugged into PORT7 on the sim robot.')
check_raises('Inertial_PORT21', Make(Inertial, Ports.PORT21), SimNotAvailable,
             'Nothing is plugged into PORT21 on the sim robot.')
for letter in 'cdefgh':
    check_raises('Bumper_3wire_' + letter, Make(Bumper, getattr(brain.three_wire_port, letter)), SimNotAvailable,
                 'Nothing is plugged into 3-wire port %s on the sim robot.' % letter.upper())
check_raises('Motor_on_inertial_port', Make(Motor, Ports.PORT3), SimNotAvailable,
             'PORT3 on the sim robot is an Inertial, not a Motor.')
check_raises('Inertial_on_motor_port', Make(Inertial, Ports.PORT1), SimNotAvailable,
             'PORT1 on the sim robot is a Motor, not an Inertial.')
check_raises('Distance_on_motor_port', Make(Distance, Ports.PORT10), SimNotAvailable,
             'PORT10 on the sim robot is a Motor, not a Distance.')
check_raises('Motor_bad_port_type', Make(Motor, 1), TypeError)
summary('t_unmapped_port')
