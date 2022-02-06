#!/usr/bin/env python

from picar.SunFounder_PCA9685 import Servo
import time
from picar import filedb
import picar

class Roboarm(object):
        '''Camera movement control class'''
        pan_channel = 6			# Pan servo channel
        forward_channel = 8		# Forward drive arm servo channel
        vertical_channel = 7            # Vertical drive arm servo channel
        clamp_channel = 9               # clamp servo channel

        READY_ANGLE = 90		# Ready position angle
        CLAMP_OPEN_ANGLE = 90
        CLAMP_CLOSE_ANGLE = 0

        DELAY = 0.05

        _DEBUG = False
        _DEBUG_INFO = 'DEBUG "roboarm.py":'

        def __init__(self, debug=False, bus_number=1, db="config"):
            ''' Init the servo channel '''
            self.db = filedb.fileDB(db=db)
            self.pan_offset = int(self.db.get('pan_offset', default_value=0))
            self.forward_offset = int(self.db.get('forward_offset', default_value=0))
            self.vertical_offset = int(self.db.get('vertical_offset', default_value=0))
            self.clamp_offset = int(self.db.get('clamp_offset', default_value=0))

            self.pan_servo = Servo.Servo(self.pan_channel,
                    bus_number=bus_number, offset=self.pan_offset)
            self.forward_servo = Servo.Servo(self.forward_channel,
                    bus_number=bus_number, offset=self.forward_offset)
            self.vertical_servo = Servo.Servo(self.vertical_channel,
                    bus_number=bus_number, offset=self.vertical_offset)
            self.clamp_servo = Servo.Servo(self.clamp_channel,
                    bus_number=bus_number, offset=self.clamp_offset)
            self.debug = debug

            self.current_pan = self.READY_ANGLE
            self.current_forward = self.READY_ANGLE
            self.current_vertical = self.READY_ANGLE
            self.current_clamp = self.READY_ANGLE
            self.ready()

        def safe_value(self, value):
            if value > 180:
                return 180
            if value < 0:
                return 0
            return value

        def smooth_move(self, servo, current_angle, target_angle, delay=DELAY):
            ''' Smoothly move to the position '''
            if self._DEBUG:
                print('smooth move from %d to %d' % (current_angle, target_angle))
            if (current_angle == target_angle):
                return

            max_step = 2 # Max angles for each step
            start_angle = current_angle + 1
            if (target_angle < current_angle):
                start_angle = current_angle - 1
                max_step = -max_step
            angles = list(range(start_angle, target_angle, max_step))
            angles.append(target_angle)
            for angle in angles:
                servo.write(angle)
                time.sleep(delay)

        def pan(self, expect_pan, delay=DELAY, smooth=False):
            target_pan = self.safe_value(expect_pan)
            if smooth:
                self.smooth_move(self.pan_servo, self.current_pan,
                        target_pan, delay)
            else:
                self.pan_servo.write(target_pan)
            self.current_pan = target_pan
            time.sleep(delay)
            return self.current_pan

        def forward(self, expect_forward, delay=DELAY, smooth=False):
            target_forward = self.safe_value(expect_forward)
            if smooth:
                self.smooth_move(self.forward_servo, self.current_forward,
                        target_forward, delay)
            else:
                self.forward_servo.write(target_forward)
            self.current_forward = target_forward
            time.sleep(delay)
            return self.current_forward

        def vertical(self, expect_vertical, delay=DELAY, smooth=False):
            target_vertical = self.safe_value(expect_vertical)
            if smooth:
                self.smooth_move(self.vertical_servo, self.current_vertical,
                        target_vertical, delay)
            else:
                self.vertical_servo.write(self.current_vertical)
            self.current_vertical = target_vertical
            time.sleep(delay)
            return self.current_vertical

        def open_clamp(self):
            self.smooth_move(self.clamp_servo, self.current_clamp, self.CLAMP_OPEN_ANGLE)
            self.current_clamp = self.CLAMP_OPEN_ANGLE

        def close_clamp(self):
            self.smooth_move(self.clamp_servo, self.current_clamp, self.CLAMP_CLOSE_ANGLE)
            self.current_clamp = self.CLAMP_CLOSE_ANGLE

        def to_position(self, expect_pan, expect_forward, expect_vertical, delay=DELAY, smooth=False):
            '''Move the roboarm to a position'''
            self.pan(expect_pan, smooth=smooth)
            self.forward(expect_forward, smooth=smooth)
            self.vertical(expect_vertical, smooth=smooth)
            return (self.current_pan, self.current_forward, self.current_vertical)         

        def ready(self):
            ''' Set the roboarm to ready position '''
            if self._DEBUG:
                print(self._DEBUG_INFO, 'Turn to "Ready" position')
            self.pan_servo.offset = self.pan_offset
            self.forward_servo.offset = self.forward_offset
            self.vertical_servo.offset = self.vertical_offset
            self.clamp_servo.offset = self.clamp_offset

            self.pan(self.READY_ANGLE, smooth=True)
            self.forward(self.READY_ANGLE, smooth=True)
            self.vertical(self.READY_ANGLE, smooth=True)
            self.clamp_servo.write(self.READY_ANGLE)

            self.current_pan = self.READY_ANGLE
            self.current_forward = self.READY_ANGLE
            self.current_vertical = self.READY_ANGLE
            self.current_clamp = self.READY_ANGLE

            return (self.current_pan, self.current_forward, self.current_vertical, self.current_clamp)         

        def calibration(self):
            ''' Save current position to calibration offset '''
            if self._DEBUG:
                print(self._DEBUG_INFO, 'Save "Calibration" position')
                self.pan_offset = self.current_pan - READY_ANGLE
                self.forward_offset = self.current_forward - READY_ANGLE
                self.vertical_offset = self.current_vertical - READY_ANGLE
                self.clamp_offset = self.current_clamp - READY_ANGLE

                self.db.set('pan_offset', self.pan_offset)
                self.db.set('forward_offset', self.forward_offset)
                self.db.set('vertical_offset', self.vertical_offset)
                self.db.set('clamp_offset', self.clamp_offset)

        def pickup(self):
            ''' Pick up the object '''
            self.open_clamp()
            self.to_position(self.current_pan, 120, 30, smooth=True)
            self.to_position(self.current_pan, 160, 0, smooth=True) 
            self.to_position(self.current_pan, 180, 0, smooth=True)
            self.close_clamp()
            self.to_position(self.current_pan, 160, 45, smooth=True)
            self.to_position(self.current_pan, 100, 90, smooth=True)
            self.to_position(self.current_pan, 90, 90, smooth=True)


        @property
        def debug(self):
            return self._DEBUG

        @debug.setter
        def debug(self, debug):
            ''' Set if debug information shows '''
            if debug in (True, False):
                self._DEBUG = debug
            else:
                raise ValueError('debug must be "True" (Set debug on) or "False" (Set debug off), not "{0}"'.format(debug))

            if self._DEBUG:
                print(self._DEBUG_INFO, "Set debug on")
                self.pan_servo.debug = True
                self.forward_servo.debug = True
                self.vertical_servo.debug = True
                self.clamp_servo.debug = True
            else:
                print(self._DEBUG_INFO, "Set debug off")
                self.pan_servo.debug = False
                self.forward_servo.debug = False
                self.vertical_servo.debug = False
                self.clamp_servo.debug = False

if __name__ == '__main__':
    picar.setup()
    roboarm = Roboarm(debug=True,bus_number=1)
    roboarm.ready()
    time.sleep(1)

    angles = [0, 90, 180, 90]

    for i in angles:
        roboarm.pan(i)
        time.sleep(1)

    for i in angles:
        roboarm.forward(i)
        time.sleep(1)

    for i in angles:
        roboarm.vertical(i)
        time.sleep(1)

    roboarm.open_clamp()
    time.sleep(1)
    roboarm.close_clamp()
