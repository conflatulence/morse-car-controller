
from math import pi
from utils import clamp

class VehicleControls:
    def __init__(self):
        self.throttle = 0
        self.brake = 0
        self.steer = 0

    def set_steer(self, val):
        self.steer = clamp(-pi/4, pi/4, val)
        
    def status(self):
        d= {}
        d['throttle'] = self.throttle
        d['brake'] = self.brake
        d['steer'] = self.steer
        return d
