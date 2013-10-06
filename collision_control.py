
from random import random
from math import pi
from utils import wrap_radians

class CollisionController:
    def __init__(self, state, controls, speed_control):
        self.vstate = state
        self.controls = controls
        self.speed_control = speed_control

        self.auto_steer = True
        self.target_heading = 0
        self.target_speed = 0

        self.blocked = False
        self.dodging = False
        self.dodge_turn = pi/4

        self.Kp = 1.0

        self.last_steer_error = 0

 
    def range_mins(self, ranges):
        N = len(ranges)
        min_left = min(ranges[0:int(N/3)])
        min_middle = min(ranges[int(N/3):int(2*N/3)])
        min_right = min(ranges[int(2*N/3):N])
        
        return (min_left, min_middle, min_right)
        
    def update_range(self, ranges):
        left, mid, right = self.range_mins(ranges)
        
        if self.auto_steer:
            m = 4
            if mid < m and left < m and right < m:
                self.speed_control.stop()
                self.blocked = True
                self.dodging = False
            else:
                self.blocked = False
                self.dodging = False
                if left < m  and right > m:
                    self.controls.set_steer(self.dodge_turn)
                    self.dodging = True
                elif right < m and left > m:
                    self.controls.set_steer(-self.dodge_turn)
                    self.dodging = True
                elif mid < m and left > m and right > m:
                    self.controls.set_steer(self.dodge_turn if random() > 0.5 else -self.dodge_turn)
                    self.dodging = True

    def set_steer(self, angle):
        self.auto_steer = False
        self.controls.set_steer(angle)
        
    def set_speed(self, speed):
        if speed < 0 or (speed > 0 and not self.blocked):
            self.speed_control.set_speed(speed)
    
    def adjust_speed(self, amount):
        speed = self.target_speed + amount
        self.set_speed(speed)
    
    def stop(self):
        self.speed_control.stop()

    def set_heading(self, heading):
        self.target_heading = heading
        self.auto_steer = True

    def update_heading(self):
        heading = self.vstate.yaw
        if self.auto_steer and not self.dodging:
            self.last_steer_error = wrap_radians(self.target_heading - heading)
            self.controls.set_steer(self.Kp*self.last_steer_error)
    
    def status(self):
        d = {}
        d['blocked'] = self.blocked
        d['dodging'] = self.dodging
        d['auto_steer'] = self.auto_steer
        d['target_heading'] = self.target_heading
        d['steer_error'] = self.last_steer_error
        return d