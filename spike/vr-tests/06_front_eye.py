# Front eye (in6, forward ColorSensor, 30 cm range, 30 deg FOV): sees nothing at the start
# (the wall is just out of range), then sees red once it is close to the wall.
import simPython, time

L = simPython.Motor('outA')
R = simPython.Motor('outB')
eye = simPython.ColorSensor('in6')
dist = simPython.UltrasonicSensor('in5')

def check(name, ok, detail):
    print(('PASS ' if ok else 'FAIL ') + name + ': ' + detail)

time.sleep(0.3)
rgb = eye.value()
check('nothing at start', max(rgb) < 20, 'rgb=%s' % [round(v) for v in rgb])

L.speed_sp(300); R.speed_sp(300)
L.command('run-forever'); R.command('run-forever')
while dist.dist() > 10:
    time.sleep(0.005)
L.command('stop'); R.command('stop')
time.sleep(0.3)
h, s, v = eye.valueHSV()
check('sees red wall', (h < 20 or h > 340) and s > 50, 'hsv=(%.0f, %.0f, %.0f)' % (h, s, v))
