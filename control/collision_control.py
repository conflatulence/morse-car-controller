
from random import random
from math import pi
from utils import wrap_radians

class CollisionController:
    def __init__(self, state, speed_control, steering_control):
        self.vstate = state
        self.speed_control = speed_control
        self.steering_control = steering_control

        self.blocked = False
        self.dodging = False
        self.dodge_turn = pi/4
        self.obstacle_range = 4

        self.enabled = True

    def range_mins(self, ranges):
        N = len(ranges)
        min_left = min(ranges[0:int(N/3)])
        min_middle = min(ranges[int(N/3):int(2*N/3)])
        min_right = min(ranges[int(2*N/3):N])
        
        return (min_left, min_middle, min_right)
        
    def update_range(self, ranges):
        left, mid, right = self.range_mins(ranges)
    
        if self.speed_control.target_speed > 0:
            m = self.obstacle_range
            if mid < m and left < m and right < m:
                self.speed_control.stop()
                self.blocked = True
                self.dodging = False
            else:
                if left < m  and right > m:
                    self.steering_control.set_steer(self.dodge_turn)
                    self.blocked = False
                    self.dodging = True
                elif right < m and left > m:
                    self.steering_control.set_steer(-self.dodge_turn)
                    self.blocked = False
                    self.dodging = True
                elif mid < m and left > m and right > m: # maybe should turn harder in this case.
                    self.steering_control.set_steer(self.dodge_turn if random() > 0.5 else -self.dodge_turn)
                    self.blocked = False
                    self.dodging = True
                else:
                    self.blocked = False
                    self.dodging = False
                    self.steering_control.enabled = True

    def set_steer(self, angle):
        # allow manual external steering control in reverse.
        if not self.enabled or self.speed_control.target_speed <= 0:
            self.steering_control.set_steer(angle)

    def set_speed(self, speed):
        if not self.enabled or speed < 0 or (speed > 0 and not self.blocked):
            self.speed_control.set_speed(speed)
    
    def adjust_speed(self, amount):
        speed = self.speed_control.target_speed + amount
        self.set_speed(speed)
    
    def stop(self):
        self.speed_control.stop()

    def set_heading(self, heading):
        # the steering control won't be enabled here, it needs explicit enable=True
        self.steering_control.set_heading(heading)
    
    def status(self):
        d = {}
        d['enabled'] = self.enabled
        d['blocked'] = self.blocked
        d['dodging'] = self.dodging
        return d
