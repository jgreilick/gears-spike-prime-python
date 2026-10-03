# Throwaway probe (not the shim). Injected as two tabs via the browser console:
#   vex.py  = VEX_STUB below    main.py = MAIN below
# Checks: (1) a user tab named vex.py shadows a bundled ./vex.py,
# (2) blocking spin_for over simPython.Motor, (3) encoder-only turn accuracy vs gyro.

VEX_STUB = '''
import simPython, time
SOURCE = "user-tab"
_PORTS = {1: "outA", 2: "outB"}

class Motor:
    def __init__(self, port):
        self._m = simPython.Motor(_PORTS[port])
    def position(self):
        return self._m.position()
    def spin_for(self, deg, dps, wait=True):
        self._m.speed_sp(abs(dps))
        self._m.position_sp(deg if dps >= 0 else -deg)
        self._m.stop_action("brake")
        self._m.command("run-to-rel-pos")
        if wait:
            time.sleep(0.02)
            while "running" in str(self._m.state()) or "ramping" in str(self._m.state()):
                time.sleep(0.01)

def turn_for_open_loop(left, right, angle, wheel_d_cm, track_cm, dps):
    deg = angle * track_cm / wheel_d_cm
    left.spin_for(deg, dps, wait=False)
    right.spin_for(-deg, dps, wait=True)
    time.sleep(0.3)
'''

MAIN = '''
import vex, time, simPython
print("vex source:", vex.SOURCE)
L = vex.Motor(1); R = vex.Motor(2)
t = time.time()
L.spin_for(360, 400, wait=True)
print("blocking spin_for 360 @400dps: %.2fs, pos=%d" % (time.time() - t, L.position()))
gyro = None
try:
    gyro = simPython.GyroSensor("in3")
except Exception as e:
    print("no gyro:", e)
for a in (90, 180):
    g0 = gyro.yawAngleAndRate(True)[0] if gyro else 0
    vex.turn_for_open_loop(L, R, a, 5.6, 15.2, 300)
    if gyro:
        print("asked %d, gyro saw %.1f" % (a, gyro.yawAngleAndRate(True)[0] - g0))
'''
