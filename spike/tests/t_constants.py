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

# Enums, aliases, ports, and the import * surface. World: any.
import vex

check_eq('FORWARD_is_DirectionType', FORWARD is DirectionType.FORWARD, True)
check_eq('REVERSE_is_DirectionType', REVERSE is DirectionType.REVERSE, True)
check_eq('LEFT_is_TurnType', LEFT is TurnType.LEFT, True)
check_eq('RIGHT_is_TurnType', RIGHT is TurnType.RIGHT, True)
check_eq('PERCENT_is_PercentUnits', PERCENT is PercentUnits.PERCENT, True)
check_eq('VelocityUnits_PERCENT_same', VelocityUnits.PERCENT is PERCENT, True)
check_eq('RPM_is_VelocityUnits', RPM is VelocityUnits.RPM, True)
check_eq('DEGREES_is_RotationUnits_DEG', DEGREES is RotationUnits.DEG, True)
check_eq('TURNS_is_RotationUnits_REV', TURNS is RotationUnits.REV, True)
check_eq('RotationUnits_TURNS_alias', RotationUnits.TURNS is TURNS, True)
check_eq('MM_is_DistanceUnits', MM is DistanceUnits.MM, True)
check_eq('INCHES_is_DistanceUnits_IN', INCHES is DistanceUnits.IN, True)
check_eq('MSEC_is_TimeUnits', MSEC is TimeUnits.MSEC, True)
check_eq('SECONDS_is_TimeUnits', SECONDS is TimeUnits.SECONDS, True)
check_eq('BRAKE_is_BrakeType', BRAKE is BrakeType.BRAKE, True)
check_eq('COAST_is_BrakeType', COAST is BrakeType.COAST, True)
check_eq('HOLD_is_BrakeType', HOLD is BrakeType.HOLD, True)
check_eq('str_FORWARD', str(FORWARD), 'FORWARD')
check_eq('repr_PORT10', repr(Ports.PORT10), 'PORT10')
check_eq('FORWARD_ne_REVERSE', FORWARD == REVERSE, False)

names = ['PORT%d' % i for i in range(1, 22)]
ports = [getattr(Ports, n) for n in names]
check_eq('Ports_PORT1_to_21', len(ports), 21)
check_eq('Ports_distinct', len(set([id(p) for p in ports])), 21)
check_eq('GearSetting_names', ' '.join([str(g) for g in (GearSetting.RATIO_36_1, GearSetting.RATIO_18_1, GearSetting.RATIO_6_1)]),
         'RATIO_36_1 RATIO_18_1 RATIO_6_1')

for n in vex.__all__:
    if not hasattr(vex, n):
        check_eq('all_name_exists_' + n, False, True)
check_eq('all_names_exist', len([n for n in vex.__all__ if hasattr(vex, n)]), len(vex.__all__))
check_eq('all_has_no_private', len([n for n in vex.__all__ if n.startswith('_')]), 0)
check_eq('SimNotAvailable_not_in_all', 'SimNotAvailable' in vex.__all__, False)
check_eq('simPython_not_in_all', 'simPython' in vex.__all__, False)
check_eq('version', vex._VERSION, '0.2')
summary('t_constants')
