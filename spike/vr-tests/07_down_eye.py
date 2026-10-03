# Down eye (in7, downward ColorSensor): plain floor at the start, then the green patch at y = 17..23.
import simPython, time

L = simPython.Motor('outA')
R = simPython.Motor('outB')
eye = simPython.ColorSensor('in7')

def check(name, ok, detail):
    print(('PASS ' if ok else 'FAIL ') + name + ': ' + detail)

def is_green(hsv):
    return 90 < hsv[0] < 150 and hsv[1] > 50

time.sleep(0.3)
hsv = eye.valueHSV()
check('floor at start is not green', not is_green(hsv), 'hsv=%s' % [round(x) for x in hsv])

L.speed_sp(200); R.speed_sp(200)
L.command('run-forever'); R.command('run-forever')
t0 = time.time()
found = None
while time.time() - t0 < 5:
    hsv = eye.valueHSV()
    if is_green(hsv):
        found = hsv
        break
    time.sleep(0.005)
L.command('stop'); R.command('stop')
check('finds green patch', found is not None,
      'hsv=%s after %.2f s' % (found and [round(x) for x in found], time.time() - t0))
