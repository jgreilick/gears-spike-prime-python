"""Build dist/vex-starter.zip: a Gears project ZIP plus the Castle Crasher world.

Gears' Import ZIP reads meta.json, gearsRobot.json and every *.py file; it ignores
castle-crasher.json, which students extract and load with World -> Load from file.
Run from anywhere: python spike/build_starter.py
"""
import json
import os
import zipfile

SPIKE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SPIKE)
OUT = os.path.join(ROOT, 'dist', 'vex-starter.zip')
FIXED_TIME = (2026, 1, 1, 0, 0, 0)

FILES = [
    ('main.py', os.path.join(SPIKE, 'starter', 'main.py')),
    ('vex.py', os.path.join(SPIKE, 'vex.py')),
    ('vexsim.py', os.path.join(SPIKE, 'vexsim.py')),
    ('gearsRobot.json', os.path.join(SPIKE, 'vr-robot-styled.json')),
    ('castle-crasher.json', os.path.join(SPIKE, 'castle-crasher-world.json')),
]
META = {'name': 'vex-starter', 'pythonModified': True}


def read(path):
    with open(path, 'rb') as f:
        return f.read()


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.loads(read(FILES[3][1]))
    json.loads(read(FILES[4][1]))
    with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr(zipfile.ZipInfo('meta.json', FIXED_TIME), json.dumps(META, indent=2), zipfile.ZIP_DEFLATED)
        for name, path in FILES:
            z.writestr(zipfile.ZipInfo(name, FIXED_TIME), read(path), zipfile.ZIP_DEFLATED)
    with zipfile.ZipFile(OUT) as z:
        for info in z.infolist():
            print('%-22s %7d bytes' % (info.filename, info.file_size))
    print('wrote ' + os.path.relpath(OUT, ROOT))


if __name__ == '__main__':
    main()
