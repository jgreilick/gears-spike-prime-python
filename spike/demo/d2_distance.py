# Drive toward the center castle and stop 150 mm in front of it.
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
brain.screen.print("Start: ", distance.object_distance(MM), " mm")
brain.screen.next_row()
drivetrain.drive(FORWARD, 30, PERCENT)
while distance.object_distance(MM) >= 150:
    wait(20, MSEC)
drivetrain.stop()
wait(500, MSEC)
brain.screen.print("Stopped at: ", distance.object_distance(MM), " mm")
brain.screen.next_row()
