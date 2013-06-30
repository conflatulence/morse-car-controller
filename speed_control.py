
from utils import clamp

class SpeedController:
    def __init__(self, controls):
        self.controls = controls
        self.target_speed = 0
        self.stopping = False
        self.last_integral = 0
        self.last_error = 0
        self.Kp = 10
        self.Ki = 5
        self.Kd = 0
        
        self.throttle = 0
        self.brake = 0
        
    def stop(self):
        self.stopping = True
        self.target_speed = 0 
        self.controls.throttle = 0
        self.controls.brake = 2
        
    def set_speed(self, speed):
        if self.target_speed > 0 and speed <= 0 or self.target_speed < 0 and speed >= 0:
            self.stop()
        
        self.target_speed = clamp(-10, 10, speed)
        
    def adjust_speed(self, amount):
        self.set_speed(self.target_speed + amount) 

    def update(self, current_speed, dt):        
        assert(current_speed >= 0)
        
        if self.stopping and abs(current_speed) < 0.1:
            self.stopping = False
                
        if self.stopping:
            integral = 0
            error = 0
            throttle = 0
            brake = 2
        else:
            error = abs(self.target_speed) - current_speed
            integral = self.last_integral + error*dt
            derivative = (error - self.last_error)/dt
            
            throttle = self.Kp*error + self.Ki*integral + self.Kd*derivative
            
            throttle = clamp(0, 40, throttle)
            brake = 0
            
            if self.target_speed < 0:
                throttle = -throttle

        self.last_error = error
        self.last_integral = integral
        
        self.controls.throttle = throttle
        self.controls.brake = brake
    