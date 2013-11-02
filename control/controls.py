
from math import pi
from utils import clamp
from logging import error, warning, info, debug
from inspect import stack

class VehicleControls:
    def __init__(self):
        self.throttle = 0
        self.brake = 0
        self.steer = 0

    def set_steer(self, val):
        self.steer = clamp(-pi/4, pi/4, val)
        #info('Controls set_steer %0.2f clamped to %0.2f from %s' % (val, self.steer, stack()[1][3]))

    def status(self):
        d= {}
        d['throttle'] = self.throttle
        d['brake'] = self.brake
        d['steer'] = self.steer
        return d
