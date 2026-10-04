# Castle Crasher, first challenge: from the start, drive_for 800 mm and crash the centre castle.
# Load spike/vr-robot.json and spike/castle-crasher-world.json, then run.
# Uses simPython directly (the layer the vex shim will sit on). VEX units: mm = GPS cm x 10.
# Python can't see world objects, so whether the castle fell is checked by check_castles.js.
import simPython, time, math

WHEEL_MM = 50.0
SPEED = 400                      # deg/s, about 17.5 cm/s

L = simPython.Motor('outA')
R = simPython.Motor('outB')
gyro = simPython.GyroSensor('in1')
gps = simPython.GPSSensor('in2')
left_bumper = simPython.TouchSensor('in3')
right_bumper = simPython.TouchSensor('in4')

def check(name, ok, detail):
    print(('PASS ' if ok else 'FAIL ') + name + ': ' + detail)

def location_mm():
    x, _, y = gps.position()     # raw order is (x, altitude, y), cm
    return x * 10, y * 10

def drive_for(mm, timeout=8.0):
    deg = mm / (math.pi * WHEEL_MM) * 360
    for m in (L, R):
        m.speed_sp(SPEED)
        m.position_sp(deg)
        m.command('run-to-rel-pos')
    t0 = time.time()
    time.sleep(0.05)
    hit = False
    while L.state() in ('running', 'ramping') or R.state() in ('running', 'ramping'):
        hit = hit or left_bumper.isPressed() or right_bumper.isPressed()
        if time.time() - t0 > timeout:
            L.command('stop'); R.command('stop')
            break
        time.sleep(0.01)
    time.sleep(0.3)
    return hit

x0, y0 = location_mm()
check('start position', abs(x0) < 10 and abs(y0 + 800) < 10, '(%d, %d) mm, expect (0, -800)' % (round(x0), round(y0)))
check('start heading', abs(gyro.yawAngleAndRate(True)[0]) < 1, 'facing +Y')

hit = drive_for(800)
x1, y1 = location_mm()
check('bumpers hit the castle', hit, 'pressed during the drive')
print('INFO travelled %d mm, now at (%d, %d) mm' % (round(y1 - y0), round(x1), round(y1)))

drive_for(-300)
x2, y2 = location_mm()
print('INFO backed off to (%d, %d) mm' % (round(x2), round(y2)))
print('DONE')
