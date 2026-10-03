# Electromagnet (outC): turn left to face the magnetic disc 30 cm away, energise,
# drive onto it, then reverse back to the start. The disc should come back with the robot.
# Proof: the disc's world position afterwards (from JS, or by eye).
import simPython, time

L = simPython.Motor('outA')
R = simPython.Motor('outB')
magnet = simPython.Motor('outC')
gyro = simPython.GyroSensor('in1')
gps = simPython.GPSSensor('in2')

def drive(speed):
    L.speed_sp(speed); R.speed_sp(speed)
    L.command('run-forever'); R.command('run-forever')

def stop():
    L.command('stop'); R.command('stop')

yaw0 = gyro.yawAngleAndRate(True)[0]
L.speed_sp(-150); R.speed_sp(150)
L.command('run-forever'); R.command('run-forever')
while gyro.yawAngleAndRate(True)[0] - yaw0 > -89:
    time.sleep(0.005)
stop(); time.sleep(0.3)

magnet.speed_sp(1050)
magnet.command('run-forever')     # energise
drive(200)
while gps.position()[0] > -20:    # magnet is then centred over the disc at x = -30
    time.sleep(0.005)
stop(); time.sleep(0.5)
drive(-200)
while gps.position()[0] < 0:
    time.sleep(0.005)
stop(); time.sleep(0.5)
print('robot x = %.1f; disc should be under the magnet, near x = -6.6' % gps.position()[0])
magnet.command('stop')            # release
