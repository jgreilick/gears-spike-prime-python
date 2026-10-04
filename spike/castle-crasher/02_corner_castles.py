# Castle Crasher: reach and ram all four corner castles in one run, steering by gyro + GPS.
# Load spike/vr-robot.json and spike/castle-crasher-world.json, reset, then run.
# The route stays well clear of the centre castle. Positions are VEX mm (GPS cm x 10).
# Python can't see world objects, so check_castles.js reports which castles fell.
import simPython, time, math

L = simPython.Motor('outA')
R = simPython.Motor('outB')
gyro = simPython.GyroSensor('in1')
gps = simPython.GPSSensor('in2')
left_bumper = simPython.TouchSensor('in3')
right_bumper = simPython.TouchSensor('in4')

YAW0 = gyro.yawAngleAndRate(True)[0]

def check(name, ok, detail):
    print(('PASS ' if ok else 'FAIL ') + name + ': ' + detail)

def location():
    x, _, y = gps.position()
    return x * 10, y * 10

def heading():
    return gyro.yawAngleAndRate(True)[0] - YAW0      # clockwise positive, 0 = +Y

def wrap(a):
    return (a + 180) % 360 - 180

def run(left, right):
    L.speed_sp(left); R.speed_sp(right)
    L.command('run-forever'); R.command('run-forever')

def stop():
    L.command('stop'); R.command('stop')
    time.sleep(0.2)

def bumped():
    return left_bumper.isPressed() or right_bumper.isPressed()

def bearing_to(x, y):
    px, py = location()
    return math.degrees(math.atan2(x - px, y - py)), math.hypot(x - px, y - py)

def turn_to(target, timeout=5):
    t0 = time.time()
    while time.time() - t0 < timeout:
        err = wrap(target - heading())
        if abs(err) < 2:
            break
        s = max(60, min(300, abs(err) * 6)) * (1 if err > 0 else -1)
        run(s, -s)
        time.sleep(0.01)
    stop()

def drive_to(x, y, stop_mm, ram=False, speed=350, timeout=15):
    """Drive toward (x, y) mm until within stop_mm, or (ram) until a bumper hits."""
    turn_to(bearing_to(x, y)[0])
    t0 = time.time()
    while time.time() - t0 < timeout:
        b, d = bearing_to(x, y)
        if (ram and bumped()) or d < stop_mm:
            break
        err = wrap(b - heading())
        run(speed + err * 8, speed - err * 8)
        time.sleep(0.01)
    hit = bumped()
    if ram and hit:
        run(speed, speed)            # keep shoving for a moment
        time.sleep(1.0)
    stop()
    return hit, bearing_to(x, y)[1]

def back_up(mm):
    deg = mm / (math.pi * 50) * 360
    for m in (L, R):
        m.speed_sp(400); m.position_sp(-deg); m.command('run-to-rel-pos')
    time.sleep(0.05)
    while L.state() in ('running', 'ramping') or R.state() in ('running', 'ramping'):
        time.sleep(0.01)
    time.sleep(0.2)

# name, castle centre (mm), half-size (mm), waypoints to reach first
CASTLES = [
    ('bottom-right', (730, -745), 120, [(400, -650)]),
    ('top-right',    (755, 730),   65, [(550, -400), (550, 400)]),
    ('top-left',     (-765, 750), 150, [(400, 450), (-300, 450)]),
    ('bottom-left',  (-765, -730), 65, [(-450, 300), (-450, -400)]),
]

x0, y0 = location()
check('start position', abs(x0) < 10 and abs(y0 + 800) < 10, '(%d, %d) mm' % (round(x0), round(y0)))
for name, (cx, cy), half, waypoints in CASTLES:
    for wx, wy in waypoints:
        drive_to(wx, wy, 60)
    hit, d = drive_to(cx, cy, 0, ram=True)
    px, py = location()
    # GPS sits over the axle, about 85 mm behind the bumper face
    check('reached ' + name, hit and d < half + 200,
          'bumper hit at (%d, %d), %d mm from castle centre' % (round(px), round(py), round(d)))
    back_up(200)
print('DONE')
