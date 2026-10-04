# Draw a blue square with the pen (simulator only: vexsim).
# World: spike/castle-crasher-world.json. Robot: spike/vr-robot.json.
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


def calibrate_drivetrain():
    wait(200, MSEC)
    brain.screen.print("Calibrating")
    brain.screen.next_row()
    drivetrain_inertial.calibrate()
    while drivetrain_inertial.is_calibrating():
        wait(25, MSEC)
    brain.screen.clear_screen()

calibrate_drivetrain()
#endregion VEXcode Generated Robot Configuration

# Your code here
from vexsim import *

pen = Pen()
pen.set_pen_color(BLUE)
pen.set_pen_width(MEDIUM)
pen.move(DOWN)
for side in range(4):
    drivetrain.drive_for(FORWARD, 300, MM, 50, PERCENT)
    drivetrain.turn_for(RIGHT, 90, DEGREES, 50, PERCENT)
pen.move(UP)
