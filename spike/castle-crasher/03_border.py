# Castle Crasher border: no walls. The down eye sees the red band past y = -1000 mm, and a
# robot that keeps going drives off the edge (-1150 mm) and falls.
import simPython, time

L = simPython.Motor('outA')
R = simPython.Motor('outB')
gyro = simPython.GyroSensor('in1')
gps = simPython.GPSSensor('in2')
eye = simPython.ColorSensor('in7')

def check(name, ok, detail):
    print(('PASS ' if ok else 'FAIL ') + name + ': ' + detail)

def is_red(hsv):
    return (hsv[0] < 20 or hsv[0] > 340) and hsv[1] > 50

def run(left, right):
    L.speed_sp(left); R.speed_sp(right)
    L.command('run-forever'); R.command('run-forever')

# Turn around to face -Y, so the down eye leads toward the near edge.
yaw0 = gyro.yawAngleAndRate(True)[0]
run(200, -200)
while gyro.yawAngleAndRate(True)[0] - yaw0 < 178:
    time.sleep(0.005)
run(0, 0)
time.sleep(0.3)

check('floor at start is white', not is_red(eye.valueHSV()), 'hsv=%s' % [round(v) for v in eye.valueHSV()])
run(300, 300)
t0 = time.time()
red_at = None
while time.time() - t0 < 6:
    if is_red(eye.valueHSV()):
        red_at = gps.position()[2] * 10
        break
    time.sleep(0.005)
# Facing -Y the eye is 35 mm ahead of the GPS, so expect GPS y near -965 when the eye crosses -1000.
check('down eye finds the red border', red_at is not None and -995 < red_at < -935,
      'GPS y = %s mm, eye at about %s mm' % (red_at and round(red_at), red_at and round(red_at - 35)))

t0 = time.time()
while time.time() - t0 < 4 and gps.position()[1] > -5:
    time.sleep(0.01)
run(0, 0)
_, alt, y = gps.position()
check('falls off the edge (no wall)', alt < -5, 'altitude %d mm at y = %d mm' % (round(alt * 10), round(y * 10)))
