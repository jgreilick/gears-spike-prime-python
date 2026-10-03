# Distance (in5, LaserRange, read via simPython.UltrasonicSensor): the wall face is 38 cm
# from the start centre and the ray starts ~8.7 cm ahead of it, so expect ~29.3 cm.
import simPython, time

L = simPython.Motor('outA')
R = simPython.Motor('outB')
dist = simPython.UltrasonicSensor('in5')
gyro = simPython.GyroSensor('in1')

def check(name, ok, detail):
    print(('PASS ' if ok else 'FAIL ') + name + ': ' + detail)

time.sleep(0.2)
d = dist.dist()
check('reads wall ahead', abs(d - 29.3) < 1.0, '%.2f cm = %.0f mm' % (d, d * 10))

# The wall is 40 cm wide; at 40 deg right the single ray passes just beyond its corner
# (it would read ~42 cm if it clipped the wall) and hits the arena wall instead (~57 cm).
# A wide beam would still catch the corner; the VEX laser and this ray do not.
yaw0 = gyro.yawAngleAndRate(True)[0]
L.speed_sp(150); R.speed_sp(-150)
L.command('run-forever'); R.command('run-forever')
while gyro.yawAngleAndRate(True)[0] - yaw0 < 40:
    time.sleep(0.005)
L.command('stop'); R.command('stop')
time.sleep(0.3)
d = dist.dist()
check('narrow beam clears wall corner', d > 48, '%.2f cm' % d)
