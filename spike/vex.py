"""VEX V5 Python API subset for the Gears simulator (VEXcode VR-style robot)."""
import simPython
import time
import math

_VERSION = '0.1'
_SENSOR_DELAY = 0.001
_POLL = 0.01
_START_GRACE = 0.06
_SETTLE_MAX = 0.3
_SETTLE_DPS = 5.0
_APPROACH_DECEL = 2000.0
_APPROACH_MIN_DPS = 60.0
_SIM_MAX_DPS = 800.0

__all__ = [
    'DirectionType', 'TurnType', 'VelocityUnits', 'PercentUnits', 'RotationUnits',
    'DistanceUnits', 'TimeUnits', 'BrakeType', 'GearSetting', 'Ports',
    'FORWARD', 'REVERSE', 'LEFT', 'RIGHT', 'PERCENT', 'RPM', 'DEGREES', 'TURNS',
    'MM', 'INCHES', 'MSEC', 'SECONDS', 'BRAKE', 'COAST', 'HOLD',
    'wait', 'Brain', 'Timer', 'Motor', 'MotorGroup', 'DriveTrain', 'SmartDrive',
    'Bumper', 'Distance', 'Inertial',
    'Controller', 'Competition', 'Thread', 'Event', 'Optical', 'Gps',
    'Electromagnet', 'Rotation', 'Vision', 'AiVision',
]


class SimNotAvailable(Exception):
    pass


def _tick():
    time.sleep(_SENSOR_DELAY)


def _na(what):
    raise SimNotAvailable(what + ' is not available in the simulator.')


class _NotAvailable(object):
    def __init__(self, what):
        self.what = what

    def __call__(self, *args, **kwargs):
        _na(self.what)


def _mark_unsupported(cls, names, label=None):
    for n in names:
        setattr(cls, n, _NotAvailable((label or cls.__name__) + '.' + n + '()'))


class _Enum(object):
    def __init__(self, value, name):
        self.value = value
        self.name = name

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name

    def __int__(self):
        return self.value


class DirectionType(_Enum):
    pass

DirectionType.FORWARD = DirectionType(0, 'FORWARD')
DirectionType.REVERSE = DirectionType(1, 'REVERSE')
DirectionType.UNDEFINED = DirectionType(2, 'UNDEFINED')


class TurnType(_Enum):
    pass

TurnType.LEFT = TurnType(0, 'LEFT')
TurnType.RIGHT = TurnType(1, 'RIGHT')
TurnType.UNDEFINED = TurnType(2, 'UNDEFINED')


class PercentUnits(_Enum):
    pass

PercentUnits.PERCENT = PercentUnits(0, 'PERCENT')


class VelocityUnits(_Enum):
    pass

VelocityUnits.PERCENT = PercentUnits.PERCENT
VelocityUnits.RPM = VelocityUnits(1, 'RPM')
VelocityUnits.DPS = VelocityUnits(2, 'DPS')


class RotationUnits(_Enum):
    pass

RotationUnits.DEG = RotationUnits(0, 'DEGREES')
RotationUnits.REV = RotationUnits(1, 'TURNS')
RotationUnits.TURNS = RotationUnits.REV


class DistanceUnits(_Enum):
    pass

DistanceUnits.MM = DistanceUnits(0, 'MM')
DistanceUnits.IN = DistanceUnits(1, 'INCHES')
DistanceUnits.CM = DistanceUnits(2, 'CM')


class TimeUnits(_Enum):
    pass

TimeUnits.SECONDS = TimeUnits(0, 'SECONDS')
TimeUnits.MSEC = TimeUnits(1, 'MSEC')


class BrakeType(_Enum):
    pass

BrakeType.COAST = BrakeType(0, 'COAST')
BrakeType.BRAKE = BrakeType(1, 'BRAKE')
BrakeType.HOLD = BrakeType(2, 'HOLD')


class GearSetting(_Enum):
    pass

GearSetting.RATIO_36_1 = GearSetting(0, 'RATIO_36_1')
GearSetting.RATIO_18_1 = GearSetting(1, 'RATIO_18_1')
GearSetting.RATIO_6_1 = GearSetting(2, 'RATIO_6_1')


class Ports(_Enum):
    pass

for _i in range(1, 22):
    setattr(Ports, 'PORT%d' % _i, Ports(_i - 1, 'PORT%d' % _i))

FORWARD = DirectionType.FORWARD
REVERSE = DirectionType.REVERSE
LEFT = TurnType.LEFT
RIGHT = TurnType.RIGHT
PERCENT = PercentUnits.PERCENT
RPM = VelocityUnits.RPM
DEGREES = RotationUnits.DEG
TURNS = RotationUnits.REV
MM = DistanceUnits.MM
INCHES = DistanceUnits.IN
MSEC = TimeUnits.MSEC
SECONDS = TimeUnits.SECONDS
BRAKE = BrakeType.BRAKE
COAST = BrakeType.COAST
HOLD = BrakeType.HOLD


# Sim robot wiring: V5 port -> (device kind, Gears port).
_SMART_PORTS = {
    'PORT1': ('Motor', 'outA'),
    'PORT10': ('Motor', 'outB'),
    'PORT3': ('Inertial', 'in1'),
    'PORT4': ('Distance', 'in5'),
}
_THREE_WIRE = {'a': ('Bumper', 'in3'), 'b': ('Bumper', 'in4')}
# The right drive motor is mounted mirrored, as on a real V5 drivetrain.
_MIRRORED = ('outB',)


def _a(noun):
    return ('an ' if noun[0] in 'AEIOU' else 'a ') + noun


def _gears_port(port, kind):
    if isinstance(port, _TriPort):
        table, key, label = _THREE_WIRE, port.letter, '3-wire port ' + port.letter.upper()
    elif isinstance(port, Ports):
        table, key, label = _SMART_PORTS, port.name, port.name
    else:
        raise TypeError('%s needs a port like Ports.PORT1, not %r.' % (kind, port))
    if key not in table:
        raise SimNotAvailable('Nothing is plugged into %s on the sim robot.' % label)
    found, gears = table[key]
    if found != kind:
        raise SimNotAvailable('%s on the sim robot is %s, not %s.' % (label, _a(found), _a(kind)))
    return gears


def _sim_device(factory, gears, kind):
    try:
        return factory(gears)
    except Exception:
        raise SimNotAvailable('The loaded robot has no %s on %s. Load the VEX VR robot.' % (kind, gears))


def _seconds(value, units):
    if units == SECONDS:
        return float(value)
    if units == MSEC:
        return value / 1000.0
    raise ValueError('Time units must be MSEC or SECONDS, not %r.' % (units,))


def _degrees(value, units):
    if units == DEGREES:
        return float(value)
    if units == TURNS:
        return value * 360.0
    raise ValueError('Rotation units must be DEGREES or TURNS, not %r.' % (units,))


def _from_degrees(deg, units):
    return deg / 360.0 if units == TURNS else deg


def _mm(value, units):
    if units == MM:
        return float(value)
    if units == INCHES:
        return value * 25.4
    if units == DistanceUnits.CM:
        return value * 10.0
    raise ValueError('Distance units must be MM, INCHES or DistanceUnits.CM, not %r.' % (units,))


_clamp_noted = []


def _to_dps(value, units):
    if units == PERCENT:
        dps = value / 100.0 * _SIM_MAX_DPS
    elif units == RPM:
        dps = value * 6.0
    elif units == VelocityUnits.DPS:
        dps = float(value)
    else:
        raise ValueError('Velocity units must be PERCENT, RPM or VelocityUnits.DPS, not %r.' % (units,))
    if abs(dps) > _SIM_MAX_DPS:
        if not _clamp_noted:
            _clamp_noted.append(True)
            print('Note: sim motors top out at 800 deg/s (133 rpm); faster speeds are clamped.')
        dps = _SIM_MAX_DPS if dps > 0 else -_SIM_MAX_DPS
    return dps


def _from_dps(dps, units):
    if units == PERCENT:
        return dps / _SIM_MAX_DPS * 100.0
    if units == RPM:
        return dps / 6.0
    if units == VelocityUnits.DPS:
        return dps
    raise ValueError('Velocity units must be PERCENT, RPM or VelocityUnits.DPS, not %r.' % (units,))


_STOP_ACTIONS = {'BRAKE': 'brake', 'COAST': 'coast', 'HOLD': 'hold'}


def _stop_action(mode):
    if not isinstance(mode, BrakeType) or mode.name not in _STOP_ACTIONS:
        raise ValueError('Stopping mode must be BRAKE, COAST or HOLD, not %r.' % (mode,))
    return _STOP_ACTIONS[mode.name]


def _dir_sign(direction, a, b):
    if direction is a:
        return 1
    if direction is b:
        return -1
    raise ValueError('Direction must be %s or %s, not %r.' % (a, b, direction))


def wait(time_value, units=MSEC):
    time.sleep(_seconds(time_value, units))


class Timer(object):
    def __init__(self):
        self._t0 = time.time()

    def time(self, units=MSEC):
        _tick()
        s = time.time() - self._t0
        return s if units == SECONDS else s * 1000.0

    def clear(self):
        self._t0 = time.time()

    def reset(self):
        self.clear()

_mark_unsupported(Timer, ['event'], 'brain.timer')


class _Screen(object):
    def print(self, *args, **kwargs):
        sep = kwargs.get('sep', '')
        precision = kwargs.get('precision', 2)
        parts = []
        for a in args:
            if isinstance(a, float):
                parts.append(('%.' + str(int(precision)) + 'f') % a)
            else:
                parts.append(str(a))
        print(sep.join(parts), end='')

    def next_row(self):
        print('')

    def new_line(self):
        self.next_row()

    def clear_screen(self, color=None):
        print('')

_mark_unsupported(_Screen, [
    'set_cursor', 'clear_row', 'row', 'column', 'print_at', 'get_string_width',
    'get_string_height', 'clear_line', 'set_font', 'set_pen_width', 'set_pen_color',
    'set_fill_color', 'set_origin', 'draw_pixel', 'draw_line', 'draw_rectangle',
    'draw_circle', 'render', 'set_clip_region', 'pressing', 'x_position', 'y_position',
    'pressed', 'released'], 'brain.screen')


class _TriPort(object):
    def __init__(self, letter):
        self.letter = letter

    def __repr__(self):
        return 'three_wire_port.' + self.letter


class _ThreeWirePorts(object):
    def __init__(self):
        for letter in 'abcdefgh':
            setattr(self, letter, _TriPort(letter))


class Brain(object):
    def __init__(self):
        self.screen = _Screen()
        self.timer = Timer()
        self.three_wire_port = _ThreeWirePorts()

_mark_unsupported(Brain, ['program_stop'], 'brain')


def _settle(spinners):
    t0 = time.time()
    while time.time() - t0 < _SETTLE_MAX:
        moving = False
        for s in spinners:
            if s._moving():
                moving = True
        if not moving:
            return
        time.sleep(_POLL)


class _Spinner(object):
    def _setup(self):
        self._velocity = (50.0, PERCENT)
        self._stopping = BRAKE
        self._timeout = 0.0

    def _resolve(self, velocity, units):
        if velocity is None:
            velocity, units = self._velocity
        return _to_dps(velocity, units)

    def _await(self):
        t0 = time.time()
        while self._busy():
            if self._timeout and time.time() - t0 > self._timeout:
                self._halt(self._stopping)
                return False
            self._approach()
            time.sleep(_POLL)
        _settle([self])
        self._halt(self._stopping)
        return True

    def spin(self, direction, velocity=None, units=RPM):
        self._run_forever(_dir_sign(direction, FORWARD, REVERSE) * self._resolve(velocity, units))

    def spin_for(self, direction, angle, units=DEGREES, velocity=None, units_v=RPM, wait=True):
        dps = self._resolve(velocity, units_v)
        sign = _dir_sign(direction, FORWARD, REVERSE)
        self._run_relative(sign * _degrees(angle, units), dps)
        if wait:
            return self._await()
        return False

    def spin_to_position(self, rotation, units=DEGREES, velocity=None, units_v=RPM, wait=True):
        delta = _degrees(rotation, units) - self.position(DEGREES)
        return self.spin_for(FORWARD, delta, DEGREES, velocity, units_v, wait)

    def stop(self, mode=None):
        self._halt(self._stopping if mode is None else mode)

    def set_velocity(self, velocity, units=RPM):
        _to_dps(velocity, units)
        self._velocity = (velocity, units)

    def set_stopping(self, mode):
        _stop_action(mode)
        self._stopping = mode

    def set_timeout(self, value, units=MSEC):
        self._timeout = _seconds(value, units)

    def get_timeout(self):
        return self._timeout * 1000.0

    def is_done(self):
        _tick()
        return not self._busy()

    def is_spinning(self):
        return not self.is_done()


class Motor(_Spinner):
    def __init__(self, port, *args):
        gears = GearSetting.RATIO_18_1
        reverse = False
        if len(args) >= 1:
            if isinstance(args[0], bool):
                reverse = args[0]
            else:
                gears = args[0]
                if len(args) >= 2:
                    reverse = bool(args[1])
        if not isinstance(gears, GearSetting):
            raise ValueError('gears must be a GearSetting, not %r.' % (gears,))
        self._port = port
        self._gears = gears
        self._gport = _gears_port(port, 'Motor')
        self._m = _sim_device(simPython.Motor, self._gport, 'motor')
        self._mount = -1 if self._gport in _MIRRORED else 1
        self._reversed = reverse
        self._setup()
        self._offset = 0.0
        self._started = 0.0
        self._target = None
        self._top = 0.0
        self._m.stop_action('brake')
        self._m.command('stop')

    def __repr__(self):
        return 'Motor(%s)' % self._port

    def _sign(self):
        return -self._mount if self._reversed else self._mount

    def _raw_position(self):
        return self._m.position() * self._sign()

    def _busy(self):
        if time.time() - self._started < _START_GRACE:
            return True
        return self._m.state() in ('running', 'ramping')

    def _moving(self):
        return abs(self._m.speed()) > _SETTLE_DPS

    def _run_forever(self, dps):
        self._target = None
        self._m.speed_sp(dps * self._sign())
        self._m.command('run-forever')
        self._started = 0.0

    def _run_relative(self, degrees, dps):
        raw = degrees * self._sign()
        self._target = self._m.position() + raw
        self._top = abs(dps)
        self._m.stop_action('hold')
        self._m.speed_sp(self._top)
        self._m.position_sp(raw)
        self._m.command('run-to-rel-pos')
        self._started = time.time()

    def _approach(self):
        if self._target is None:
            return
        remaining = abs(self._target - self._m.position())
        dps = math.sqrt(2.0 * _APPROACH_DECEL * remaining)
        self._m.speed_sp(min(self._top, max(_APPROACH_MIN_DPS, dps)))

    def _halt(self, mode):
        self._m.stop_action(_stop_action(mode))
        self._m.command('stop')
        self._started = 0.0

    def set_reversed(self, value):
        pos = self.position(DEGREES)
        self._reversed = bool(value)
        self.set_position(pos, DEGREES)

    def set_position(self, position, units=DEGREES):
        self._offset = self._raw_position() - _degrees(position, units)

    def reset_position(self):
        self.set_position(0)

    def position(self, units=DEGREES):
        _tick()
        return _from_degrees(self._raw_position() - self._offset, units)

    def velocity(self, units=RPM):
        _tick()
        return _from_dps(self._m.speed() * self._sign(), units)

_mark_unsupported(Motor, [
    'set_max_torque', 'current', 'power', 'torque', 'efficiency', 'temperature', 'installed'])


class MotorGroup(_Spinner):
    def __init__(self, *motors):
        if not motors:
            raise ValueError('MotorGroup needs at least one Motor.')
        for m in motors:
            if not isinstance(m, Motor):
                raise TypeError('MotorGroup takes Motor objects, not %r.' % (m,))
        self._motors = list(motors)
        self._setup()

    def _busy(self):
        for m in self._motors:
            if m._busy():
                return True
        return False

    def _moving(self):
        for m in self._motors:
            if m._moving():
                return True
        return False

    def _approach(self):
        for m in self._motors:
            m._approach()

    def _run_forever(self, dps):
        for m in self._motors:
            m._run_forever(dps)

    def _run_relative(self, degrees, dps):
        for m in self._motors:
            m._run_relative(degrees, dps)

    def _halt(self, mode):
        for m in self._motors:
            m._halt(mode)

    def set_position(self, position, units=DEGREES):
        for m in self._motors:
            m.set_position(position, units)

    def reset_position(self):
        self.set_position(0)

    def position(self, units=DEGREES):
        return self._motors[0].position(units)

    def velocity(self, units=RPM):
        return self._motors[0].velocity(units)

    def count(self):
        return len(self._motors)

_mark_unsupported(MotorGroup, ['set_max_torque', 'current', 'power', 'torque', 'efficiency', 'temperature'])


class DriveTrain(object):
    def __init__(self, lm, rm, wheelTravel=300, trackWidth=320, wheelBase=320, units=MM, externalGearRatio=1.0):
        for m in (lm, rm):
            if not isinstance(m, (Motor, MotorGroup)):
                raise TypeError('DriveTrain takes a Motor or MotorGroup, not %r.' % (m,))
        self._lm = lm
        self._rm = rm
        self._wheel_travel = _mm(wheelTravel, units)
        self._track_width = _mm(trackWidth, units)
        self._wheel_base = _mm(wheelBase, units)
        self._ratio = float(externalGearRatio)
        self._drive_velocity = (50.0, PERCENT)
        self._turn_velocity = (50.0, PERCENT)
        self._stopping = BRAKE
        self._timeout = 0.0
        self._lm.set_stopping(BRAKE)
        self._rm.set_stopping(BRAKE)

    def _motor_degrees(self, mm):
        return mm / self._wheel_travel * 360.0 * self._ratio

    def _speed(self, velocity, units, default):
        if velocity is None:
            velocity, units = default
        return _to_dps(velocity, units)

    def _busy(self):
        return self._lm._busy() or self._rm._busy()

    def _await(self):
        t0 = time.time()
        while self._busy():
            if self._timeout and time.time() - t0 > self._timeout:
                self.stop()
                return False
            self._lm._approach()
            self._rm._approach()
            time.sleep(_POLL)
        _settle([self._lm, self._rm])
        self.stop()
        return True

    def _move(self, left_deg, right_deg, dps, wait):
        self._lm._run_relative(left_deg, dps)
        self._rm._run_relative(right_deg, dps)
        if wait:
            return self._await()
        return False

    def drive(self, direction, velocity=None, units=RPM):
        dps = _dir_sign(direction, FORWARD, REVERSE) * self._speed(velocity, units, self._drive_velocity)
        self._lm._run_forever(dps)
        self._rm._run_forever(dps)

    def drive_for(self, direction, distance, units=INCHES, velocity=None, units_v=RPM, wait=True):
        dps = self._speed(velocity, units_v, self._drive_velocity)
        sign = _dir_sign(direction, FORWARD, REVERSE)
        deg = sign * self._motor_degrees(_mm(distance, units))
        return self._move(deg, deg, dps, wait)

    def turn(self, direction, velocity=None, units=RPM):
        dps = _dir_sign(direction, RIGHT, LEFT) * self._speed(velocity, units, self._turn_velocity)
        self._lm._run_forever(dps)
        self._rm._run_forever(-dps)

    def turn_for(self, direction, angle, units=DEGREES, velocity=None, units_v=RPM, wait=True):
        dps = self._speed(velocity, units_v, self._turn_velocity)
        sign = _dir_sign(direction, RIGHT, LEFT)
        arc = math.pi * self._track_width * _degrees(angle, units) / 360.0
        deg = sign * self._motor_degrees(arc)
        return self._move(deg, -deg, dps, wait)

    def stop(self, mode=None):
        mode = self._stopping if mode is None else mode
        self._lm._halt(mode)
        self._rm._halt(mode)

    def set_drive_velocity(self, velocity, units=RPM):
        _to_dps(velocity, units)
        self._drive_velocity = (velocity, units)

    def set_turn_velocity(self, velocity, units=RPM):
        _to_dps(velocity, units)
        self._turn_velocity = (velocity, units)

    def set_stopping(self, mode):
        _stop_action(mode)
        self._stopping = mode

    def set_timeout(self, value, units=MSEC):
        self._timeout = _seconds(value, units)

    def get_timeout(self):
        return self._timeout * 1000.0

    def is_done(self):
        _tick()
        return not self._busy()

    def is_moving(self):
        return not self.is_done()

    def velocity(self, units=RPM):
        return (self._lm.velocity(units) + self._rm.velocity(units)) / 2.0

_mark_unsupported(DriveTrain, ['current', 'power', 'torque', 'efficiency', 'temperature'])


class SmartDrive(DriveTrain):
    _SLOW_ZONE = 30.0
    _MIN_DPS = 40.0

    def __init__(self, lm, rm, g, wheelTravel=300, trackWidth=320, wheelBase=320, units=MM, externalGearRatio=1.0):
        if not isinstance(g, Inertial):
            raise SimNotAvailable('SmartDrive in the simulator needs an Inertial sensor.')
        super(SmartDrive, self).__init__(lm, rm, wheelTravel, trackWidth, wheelBase, units, externalGearRatio)
        self._g = g
        self._threshold = 1.0
        self._constant = 1.0
        self._turn_reverse = False

    def _turn_closed(self, target, velocity, units_v, wait):
        if not wait:
            _na('SmartDrive turns with wait=False')
        top = abs(self._speed(velocity, units_v, self._turn_velocity))
        flip = -1 if self._turn_reverse else 1
        t0 = time.time()
        done = True
        while True:
            err = target - self._g.rotation()
            if abs(err) <= self._threshold:
                break
            if self._timeout and time.time() - t0 > self._timeout:
                done = False
                break
            dps = top * min(1.0, abs(err) * self._constant / self._SLOW_ZONE)
            dps = max(dps, min(top, self._MIN_DPS))
            if err < 0:
                dps = -dps
            self._lm._run_forever(flip * dps)
            self._rm._run_forever(-flip * dps)
            time.sleep(_POLL)
        self._lm._halt(HOLD)
        self._rm._halt(HOLD)
        _settle([self._lm, self._rm])
        self.stop()
        return done

    def turn_for(self, direction, angle, units=DEGREES, velocity=None, units_v=RPM, wait=True):
        sign = _dir_sign(direction, RIGHT, LEFT)
        target = self._g.rotation() + sign * _degrees(angle, units)
        return self._turn_closed(target, velocity, units_v, wait)

    def turn_to_rotation(self, angle, units=DEGREES, velocity=None, units_v=RPM, wait=True):
        return self._turn_closed(_degrees(angle, units), velocity, units_v, wait)

    def turn_to_heading(self, angle, units=DEGREES, velocity=None, units_v=RPM, wait=True):
        err = (_degrees(angle, units) - self._g.heading() + 180.0) % 360.0 - 180.0
        return self._turn_closed(self._g.rotation() + err, velocity, units_v, wait)

    def heading(self, units=DEGREES):
        return self._g.heading(units)

    def rotation(self, units=DEGREES):
        return self._g.rotation(units)

    def set_heading(self, heading, units=DEGREES):
        self._g.set_heading(heading, units)

    def set_rotation(self, rotation, units=DEGREES):
        self._g.set_rotation(rotation, units)

    def set_turn_threshold(self, value):
        self._threshold = abs(float(value))

    def set_turn_constant(self, value):
        self._constant = min(4.0, max(0.1, float(value)))

    def set_turn_direction_reverse(self, value):
        self._turn_reverse = bool(value)


class Bumper(object):
    def __init__(self, port):
        self._gport = _gears_port(port, 'Bumper')
        self._s = _sim_device(simPython.TouchSensor, self._gport, 'touch sensor')

    def pressing(self):
        _tick()
        return bool(self._s.isPressed())

_mark_unsupported(Bumper, ['pressed', 'released'])


class Distance(object):
    _MAX_MM = 2000.0
    _NO_OBJECT_MM = 9999.0

    def __init__(self, port):
        self._gport = _gears_port(port, 'Distance')
        self._s = _sim_device(simPython.UltrasonicSensor, self._gport, 'distance sensor')

    def _mm(self):
        _tick()
        mm = self._s.dist() * 10.0
        return mm if mm <= self._MAX_MM else self._NO_OBJECT_MM

    def object_distance(self, units=MM):
        mm = self._mm()
        if units == MM:
            return mm
        if units == INCHES:
            return mm / 25.4
        raise ValueError('Distance units must be MM or INCHES, not %r.' % (units,))

    def is_object_detected(self):
        return self._mm() != self._NO_OBJECT_MM

_mark_unsupported(Distance, ['object_velocity', 'object_size', 'changed', 'installed'])


class Inertial(object):
    def __init__(self, port):
        self._gport = _gears_port(port, 'Inertial')
        self._s = _sim_device(simPython.GyroSensor, self._gport, 'gyro')
        self._heading_zero = self._yaw()
        self._rotation_zero = self._heading_zero

    def _yaw(self):
        _tick()
        return self._s.yawAngleAndRate(True)[0]

    def heading(self, units=DEGREES):
        return _from_degrees((self._yaw() - self._heading_zero) % 360.0, units)

    def rotation(self, units=DEGREES):
        return _from_degrees(self._yaw() - self._rotation_zero, units)

    def set_heading(self, value, units=DEGREES):
        self._heading_zero = self._yaw() - _degrees(value, units)

    def set_rotation(self, value, units=DEGREES):
        self._rotation_zero = self._yaw() - _degrees(value, units)

    def reset_heading(self):
        self.set_heading(0)

    def reset_rotation(self):
        self.set_rotation(0)

    def calibrate(self):
        pass

    def is_calibrating(self):
        return False

_mark_unsupported(Inertial, [
    'gyro_rate', 'orientation', 'changed', 'installed', 'acceleration', 'collision',
    'set_turn_type', 'get_turn_type'])


class _Unsupported(object):
    def __init__(self, *args, **kwargs):
        _na(self.__class__.__name__)


class Controller(_Unsupported):
    pass


class Competition(_Unsupported):
    pass


class Thread(_Unsupported):
    pass


class Event(_Unsupported):
    pass


class Optical(_Unsupported):
    pass


class Gps(_Unsupported):
    pass


class Electromagnet(_Unsupported):
    pass


class Rotation(_Unsupported):
    pass


class Vision(_Unsupported):
    pass


class AiVision(_Unsupported):
    pass


print('vex shim v' + _VERSION)
