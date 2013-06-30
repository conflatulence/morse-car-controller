
# states of the car
WAITING = 0
WANDERING = 1
DODGING = 2
REVERSING = 3
TRACKING = 4

from math import pi

class AutoReverseController:
    def __init__(self, controls, speed_control):
        self.state = WAITING
        self.controls = controls
        self.speed_control = speed_control
        
        self.reverse_speed = 3
        self.wander_speed = 3
        self.dodge_turn = pi/4
        self.reverse_turn = pi/4
        self.num_reverse_counts = 10
        
        self.reverse_counter = 0
        
    def start(self):
        self.state = WANDERING
        self.speed_control.set_speed(self.wander_speed)
    
    def stop(self):
        self.speed_control.stop()
        self.controls.steer = 0
        self.state = WAITING
        
    def update_range(self, left, mid, right):
        if self.state in (WANDERING, DODGING):
            if mid < 4:
                self.state = REVERSING
                self.speed_control.set_speed(-self.reverse_speed)
                self.controls.steer = self.reverse_turn
                
            elif left < 4:
                self.state = DODGING
                self.controls.steer = self.dodge_turn
                
            elif right < 4:
                self.state = DODGING
                self.controls.steer = -self.dodge_turn
                
            else:
                self.state = WANDERING
                self.controls.steer = 0
                
        elif self.state == REVERSING:
            if mid > 4:
                self.reverse_counter += 1
                if self.reverse_counter > self.num_reverse_counts:
                    self.state = WANDERING
                    self.speed_control.set_speed(self.wander_speed)
                    self.controls.steer = 0
            else:
                self.reverse_counter = 0
                
    def update_position(self, position):
        pass
                