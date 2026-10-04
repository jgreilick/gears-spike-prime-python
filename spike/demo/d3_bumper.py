# Bump and turn: drive until a bumper hits, back up 200 mm, turn right, repeat for 20 s.
# World: spike/vr-test-world.json (walled arena). Robot: spike/vr-robot.json.
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
bumps = 0
brain.timer.clear()
while brain.timer.time(SECONDS) < 20:
    drivetrain.drive(FORWARD, 40, PERCENT)
    if left_bumper.pressing() or right_bumper.pressing():
        bumps = bumps + 1
        brain.screen.print("Bump ", bumps)
        brain.screen.next_row()
        drivetrain.drive_for(REVERSE, 200, MM, 40, PERCENT)
        drivetrain.turn_for(RIGHT, 90, DEGREES, 30, PERCENT)
    wait(20, MSEC)
drivetrain.stop()
brain.screen.print("Done after ", bumps, " bumps")
brain.screen.next_row()
