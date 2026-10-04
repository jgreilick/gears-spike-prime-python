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

# Every SimNotAvailable stub raises with its friendly message. World: test world.
from vexsim import *

def na(what):
    return what + ' is not available in the simulator.'

stubs = [
    ('Motor', left_drive_smart, ['set_max_torque', 'current', 'power', 'torque', 'efficiency', 'temperature', 'installed']),
    ('MotorGroup', MotorGroup(left_drive_smart), ['set_max_torque', 'current', 'power', 'torque', 'efficiency', 'temperature']),
    ('DriveTrain', drivetrain, ['current', 'power', 'torque', 'efficiency', 'temperature']),
    ('Bumper', left_bumper, ['pressed', 'released']),
    ('Distance', distance, ['object_velocity', 'object_size', 'changed', 'installed']),
    ('Inertial', drivetrain_inertial, ['gyro_rate', 'orientation', 'changed', 'installed', 'acceleration',
                                       'collision', 'set_turn_type', 'get_turn_type']),
    ('brain.screen', brain.screen, ['set_cursor', 'clear_row', 'row', 'column', 'print_at', 'get_string_width',
                                    'get_string_height', 'clear_line', 'set_font', 'set_pen_width', 'set_pen_color',
                                    'set_fill_color', 'set_origin', 'draw_pixel', 'draw_line', 'draw_rectangle',
                                    'draw_circle', 'render', 'set_clip_region', 'pressing', 'x_position',
                                    'y_position', 'pressed', 'released']),
    ('brain', brain, ['program_stop']),
    ('brain.timer', brain.timer, ['event']),
]
for label, obj, methods in stubs:
    for name in methods:
        check_raises(label + '.' + name, getattr(obj, name), SimNotAvailable, na(label + '.' + name + '()'))

for cls in (Controller, Competition, Thread, Event, Optical, Gps, Electromagnet, Rotation, Vision, AiVision):
    check_raises(cls.__name__, cls, SimNotAvailable, na(cls.__name__))

pen = Pen()
def pen_fill():
    pen.fill(255, 0, 0, 100)
def pen_rgb_50():
    pen.set_pen_color_rgb(255, 0, 0, 50)
def smart_wait_false():
    drivetrain.turn_to_heading(90, DEGREES, wait=False)
def smart_without_inertial():
    SmartDrive(left_drive_smart, right_drive_smart, distance)
check_raises('Pen.fill', pen_fill, SimNotAvailable, na('Pen.fill()'))
check_raises('Pen.set_pen_color_rgb_opacity_50', pen_rgb_50, SimNotAvailable, na('Pen opacity below 100'))
check_raises('SmartDrive.turn_wait_False', smart_wait_false, SimNotAvailable, na('SmartDrive turns with wait=False'))
check_raises('SmartDrive_needs_Inertial', smart_without_inertial, SimNotAvailable,
             'SmartDrive in the simulator needs an Inertial sensor.')
summary('t_unsupported')
