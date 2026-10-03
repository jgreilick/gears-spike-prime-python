# Pen (in8): draw a short red line. The visible proof is the trace on screen
# (from JS: robot.getComponentByPort('in8').traceMeshes).
import simPython, time

L = simPython.Motor('outA')
R = simPython.Motor('outB')
pen = simPython.Pen('in8')

def check(name, ok, detail):
    print(('PASS ' if ok else 'FAIL ') + name + ': ' + detail)

check('up at start', not pen.isDown(), 'isDown=%s' % pen.isDown())
pen.setColor(1, 0, 0)
pen.setWidth(1)
pen.down()
check('down', pen.isDown(), 'isDown=%s' % pen.isDown())
L.speed_sp(300); R.speed_sp(300)
L.command('run-forever'); R.command('run-forever')
time.sleep(0.8)
L.command('stop'); R.command('stop')
pen.up()
check('up again', not pen.isDown(), 'isDown=%s' % pen.isDown())
