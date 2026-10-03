# Drivetrain (outA/outB): one wheel revolution should move the robot ~pi*5 = 15.7 cm.
# Run on spike/vr-test-world.json with spike/vr-robot.json loaded.
import simPython, time, math

L = simPython.Motor('outA')
R = simPython.Motor('outB')
gps = simPython.GPSSensor('in2')

def check(name, ok, detail):
    print(('PASS ' if ok else 'FAIL ') + name + ': ' + detail)

x0, _, y0 = gps.position()
for m in (L, R):
    m.speed_sp(400)
    m.position_sp(360)
    m.command('run-to-rel-pos')
time.sleep(0.05)
while L.state() in ('running', 'ramping') or R.state() in ('running', 'ramping'):
    time.sleep(0.01)
time.sleep(0.3)
x1, _, y1 = gps.position()
moved = math.sqrt((x1 - x0) ** 2 + (y1 - y0) ** 2)
check('drive 360 deg', abs(moved - math.pi * 5) < 2.0,
      'moved %.2f cm (expect ~15.71), encoders L=%d R=%d' % (moved, int(L.position()), int(R.position())))
check('drives straight', abs(x1 - x0) < 1.0, 'lateral drift %.2f cm' % (x1 - x0))
