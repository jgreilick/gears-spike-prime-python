# Bumpers (in3 left, in4 right): released at start, both pressed after driving square into
# the red wall. Then back off, angle right 25 deg, and check the left corner hits alone.
import simPython, time

L = simPython.Motor('outA')
R = simPython.Motor('outB')
left = simPython.TouchSensor('in3')
right = simPython.TouchSensor('in4')
gyro = simPython.GyroSensor('in1')

def check(name, ok, detail):
    print(('PASS ' if ok else 'FAIL ') + name + ': ' + detail)

def drive(speed):
    L.speed_sp(speed); R.speed_sp(speed)
    L.command('run-forever'); R.command('run-forever')

def stop():
    L.command('stop'); R.command('stop')

def drive_until_bump(speed):
    drive(speed)
    t0 = time.time()
    while not (left.isPressed() or right.isPressed()) and time.time() - t0 < 5:
        time.sleep(0.002)

time.sleep(0.2)
check('released at start', not left.isPressed() and not right.isPressed(),
      'L=%s R=%s' % (left.isPressed(), right.isPressed()))

drive_until_bump(300)
time.sleep(0.3)
l, r = left.isPressed(), right.isPressed()
stop()
check('square hit presses both', l and r, 'L=%s R=%s' % (l, r))

drive(-300); time.sleep(1.0); stop(); time.sleep(0.3)
check('released after backing off', not left.isPressed() and not right.isPressed(),
      'L=%s R=%s' % (left.isPressed(), right.isPressed()))

yaw0 = gyro.yawAngleAndRate(True)[0]
L.speed_sp(150); R.speed_sp(-150)
L.command('run-forever'); R.command('run-forever')
while gyro.yawAngleAndRate(True)[0] - yaw0 < 25:
    time.sleep(0.005)
stop(); time.sleep(0.3)
drive_until_bump(200)
l, r = left.isPressed(), right.isPressed()
stop()
check('angled hit: left only', l and not r, 'L=%s R=%s' % (l, r))
