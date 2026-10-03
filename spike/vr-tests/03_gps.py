# Location (in2): GPS sits over the turning centre, so an in-place 360 spin barely moves it.
# Raw simPython order is (x, altitude, y), in cm, world frame.
import simPython, time, math

L = simPython.Motor('outA')
R = simPython.Motor('outB')
gps = simPython.GPSSensor('in2')
gyro = simPython.GyroSensor('in1')

def check(name, ok, detail):
    print(('PASS ' if ok else 'FAIL ') + name + ': ' + detail)

x0, alt, y0 = gps.position()
check('start on the axle', abs(x0) < 0.5 and abs(y0 - 1.0) < 0.5,
      'x=%.2f y=%.2f alt=%.2f (axle is 1 cm ahead of body centre)' % (x0, y0, alt))
yaw0 = gyro.yawAngleAndRate(True)[0]
L.speed_sp(300); R.speed_sp(-300)
L.command('run-forever'); R.command('run-forever')
while gyro.yawAngleAndRate(True)[0] - yaw0 < 355:
    time.sleep(0.005)
L.command('stop'); R.command('stop')
time.sleep(0.5)
x1, _, y1 = gps.position()
drift = math.sqrt((x1 - x0) ** 2 + (y1 - y0) ** 2)
check('on turning centre', drift < 1.5, 'drift after 360 spin = %.2f cm' % drift)
