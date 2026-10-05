"""Simulator only. Delete this import and all pen calls before running on a real V5.

Mirrors the VEXcode VR pen (api.vex.com/vr/home/python/drawing.html).
"""
import simPython
from vex import SimNotAvailable

_VERSION = '0.2'
_PEN_PORT = 'in8'

__all__ = ['Pen', 'UP', 'DOWN', 'BLACK', 'RED', 'GREEN', 'BLUE',
           'EXTRA_THIN', 'THIN', 'MEDIUM', 'WIDE', 'EXTRA_WIDE']


class _Option(object):
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def __repr__(self):
        return self.name

UP = _Option('UP', False)
DOWN = _Option('DOWN', True)
BLACK = _Option('BLACK', (0, 0, 0))
RED = _Option('RED', (255, 0, 0))
GREEN = _Option('GREEN', (0, 255, 0))
BLUE = _Option('BLUE', (0, 0, 255))
# Trace width in cm; VR publishes no sizes.
EXTRA_THIN = _Option('EXTRA_THIN', 0.25)
THIN = _Option('THIN', 0.5)
MEDIUM = _Option('MEDIUM', 1.0)
WIDE = _Option('WIDE', 2.0)
EXTRA_WIDE = _Option('EXTRA_WIDE', 3.0)


def _na(what):
    raise SimNotAvailable(what + ' is not available in the simulator.')


class Pen(object):
    def __init__(self):
        try:
            self._p = simPython.Pen(_PEN_PORT)
        except Exception:
            raise SimNotAvailable('The loaded robot has no pen on %s. Load the VEX VR robot.' % _PEN_PORT)
        self.set_pen_color(BLACK)
        self.set_pen_width(THIN)

    def move(self, action):
        if action is DOWN:
            self._p.down()
        elif action is UP:
            self._p.up()
        else:
            raise ValueError('pen.move takes UP or DOWN, not %r.' % (action,))

    def set_pen_color(self, color):
        if color not in (BLACK, RED, GREEN, BLUE):
            raise ValueError('Pen color must be BLACK, RED, GREEN or BLUE, not %r.' % (color,))
        r, g, b = color.value
        self._p.setColor(r / 255.0, g / 255.0, b / 255.0)

    def set_pen_color_rgb(self, red, green, blue, opacity):
        if opacity < 100:
            _na('Pen opacity below 100')
        for v in (red, green, blue):
            if v < 0 or v > 255:
                raise ValueError('Pen RGB values must be 0 to 255.')
        self._p.setColor(red / 255.0, green / 255.0, blue / 255.0)

    def set_pen_width(self, width):
        if width not in (EXTRA_THIN, THIN, MEDIUM, WIDE, EXTRA_WIDE):
            raise ValueError('Pen width must be EXTRA_THIN, THIN, MEDIUM, WIDE or EXTRA_WIDE, not %r.' % (width,))
        self._p.setWidth(width.value)

    def fill(self, red, green, blue, opacity):
        _na('Pen.fill()')


print('vexsim v' + _VERSION)
