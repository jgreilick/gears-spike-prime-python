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

# brain.screen print/next_row/clear_screen text. Captures the shim's console writes. World: any.
import vex

out = []
def capture(*args, **kwargs):
    out.append(' '.join([str(a) for a in args]) + kwargs.get('end', '\n'))
vex.print = capture

def take():
    s = ''.join(out)
    del out[:]
    return s

brain.screen.print('Hello')
check_eq('print_no_newline', take(), 'Hello')
brain.screen.print('a', 1, 2.345)
check_eq('print_default_sep_empty_precision_2', take(), 'a12.35')
brain.screen.print('a', 1, sep=' ')
check_eq('print_sep', take(), 'a 1')
brain.screen.print(3.14159, precision=4)
check_eq('print_precision', take(), '3.1416')
brain.screen.print(7)
check_eq('print_int_unchanged', take(), '7')
brain.screen.next_row()
check_eq('next_row_newline', take(), '\n')
brain.screen.new_line()
check_eq('new_line_newline', take(), '\n')
brain.screen.clear_screen()
check_eq('clear_screen_newline', take(), '\n')
del vex.print
summary('t_screen')
