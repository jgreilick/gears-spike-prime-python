# Drive a 300 mm square twice: open-loop (no sensor), then SmartDrive (inertial).
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
open_loop = DriveTrain(left_drive_smart, right_drive_smart, 157.08, 120, 50.8, MM, 1)


def square(dt):
    for side in range(4):
        dt.drive_for(FORWARD, 300, MM, 50, PERCENT)
        dt.turn_for(RIGHT, 90, DEGREES, 50, PERCENT)
    wait(500, MSEC)


def heading_error():
    return (drivetrain_inertial.heading(DEGREES) + 180) % 360 - 180


drivetrain_inertial.set_heading(0, DEGREES)
square(open_loop)
brain.screen.print("Open-loop square, heading error: ", heading_error(), " deg")
brain.screen.next_row()

drivetrain_inertial.set_heading(0, DEGREES)
square(drivetrain)
brain.screen.print("SmartDrive square, heading error: ", heading_error(), " deg")
brain.screen.next_row()
