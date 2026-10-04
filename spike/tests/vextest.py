"""Test helpers for the vex shim tests. Loaded as a tab next to vex.py.

Ground truth comes from simPython directly (GPS in2, gyro in1), never from the shim.
Every check prints: PASS|FAIL name measured expected tol
"""
import simPython
import math

_results = []
_gps = simPython.GPSSensor('in2')
_gyro = simPython.GyroSensor('in1')
_wheel_l = simPython.Motor('outA')


def _fmt(v):
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, float):
        return '%.2f' % v
    return str(v)


def _record(ok, name, measured, expected, tol):
    _results.append(ok)
    print('%s %s %s %s %s' % ('PASS' if ok else 'FAIL', name, _fmt(measured), _fmt(expected), _fmt(tol)))
    return ok


def check(name, measured, expected, tol):
    return _record(abs(measured - expected) <= tol, name, float(measured), float(expected), float(tol))


def check_eq(name, measured, expected):
    return _record(measured == expected, name, measured, expected, 0)


def check_raises(name, fn, exc, message=None):
    try:
        fn()
    except exc as e:
        got = e.args[0] if e.args else ''
        if message is None:
            return _record(True, name, 'raised', 'raised', 0)
        return _record(got == message, name, repr(got), repr(message), 0)
    except Exception as e:
        return _record(False, name, type(e).__name__, exc.__name__, 0)
    return _record(False, name, 'no-raise', exc.__name__, 0)


def summary(test):
    passed = len([r for r in _results if r])
    print('SUMMARY %s %d/%d %s' % (test, passed, len(_results), 'OK' if passed == len(_results) else 'FAILED'))


def pos_mm():
    x, _, y = _gps.position()
    return x * 10.0, y * 10.0


def travelled_mm(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])


def yaw():
    return _gyro.yawAngleAndRate(True)[0]


def raw_left_deg():
    return _wheel_l.position()


def sign(v):
    return 1 if v > 0 else (-1 if v < 0 else 0)
