

CLEAR = 0
DODGING = 1
BLOCKED = 2

# steer_modes
# AUTO_STEER means the controller will track some heading, and attempt
# to veer away from the heading when obstacles appear.
# MANUAL_STEER means the controller will simple stop the car if it is
# heading towards and obstacle, and not modify the steering.
# MANUAL_STEER is useful for doing maneuvers like reverse turn.
AUTO_STEER = 0
MANUAL_STEER = 1

from random import random
from math import pi

class CollisionController:
    def __init__(self, state, controls, speed_control):
        self.vehicle_state = state
        self.controls = controls
        self.speed_control = speed_control

        self.auto_steer = True
        self.target_heading = 0
        self.target_speed = 0

        self.state = CLEAR
        self.dodge_turn = pi/4

        self.Kp = 1.0
 
    def range_mins(self, ranges):
        N = len(ranges)
        min_left = min(ranges[0:int(N/3)])
        min_middle = min(ranges[int(N/3):int(2*N/3)])
        min_right = min(ranges[int(2*N/3):N])
        
        return (min_left, min_middle, min_right)
        
    def update_range(self, ranges):
        
        left, mid, right = self.range_mins(ranges)
        
        if self.auto_steer:
            if mid < 4 and left < 4 and right < 4:
                self.speed_control.stop()
                self.state = BLOCKED 
            else:
                if left < 4  and right > 4:
                    self.controls.steer = self.dodge_turn
                    self.state = DODGING
                elif right < 4 and left > 4:
                    self.controls.steer = -self.dodge_turn
                    self.state = DODGING
                elif left > 4 and right > 4:
                    if random() > 0.5:
                        self.controls.steer = -self.dodge_turn
                    else:
                        self.controls.steer = -self.dodge_turn
                    self.state = DODGING
                else:
                    self.state = CLEAR
                    # leave steering alone, the heading update will set it.

    def set_target_heading(self, target_heading):
        self.target_heading = target_heading
                
    def update_heading(self, heading):
        
        if self.auto_steer and self.state == CLEAR:
            self.controls.steer = self.Kp*(heading - self.target_heading)
    
        self.last_heading = heading
    
    def status(self):
        d = {}
        d['state'] = self.state
        d['auto_steer'] = self.auto_steer
        d['target_heading'] = self.target_heading
        return d