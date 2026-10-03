# Gyro (in1): closed-loop 90 deg right turn; yaw must read ~+90 (clockwise positive, like VEX VR).
import simPython, time

L = simPython.Motor('outA')
R = simPython.Motor('outB')
gyro = simPython.GyroSensor('in1')

def check(name, ok, detail):
    print(('PASS ' if ok else 'FAIL ') + name + ': ' + detail)

yaw0 = gyro.yawAngleAndRate(True)[0]
L.speed_sp(200); R.speed_sp(-200)
L.command('run-forever'); R.command('run-forever')
while gyro.yawAngleAndRate(True)[0] - yaw0 < 88:
    time.sleep(0.005)
L.command('stop'); R.command('stop')
time.sleep(0.5)
yaw = gyro.yawAngleAndRate(True)[0] - yaw0
check('right turn reads positive ~90', 85 < yaw < 100, 'yaw = %.1f' % yaw)
