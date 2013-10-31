

from geo import *

class VehicleState:
    def __init__(self):
        self.roll = 0
        self.pitch = 0
        self.yaw = 0
        
        self.heading = 0

        self.x = 0
        self.y = 0
        self.z = 0
        
        self.speed = 0
        
        self.time = 0

        self.origin = (-33.80784, 151.176614)
    
    def update_time(self, dt):
        self.time += dt
    
    def update_gps(self, lat, lon, alt, speed, heading):
        self.x, self.y = distance_in_xy(self.origin, (lat, lon))
        self.z = alt

    def update_odometry(self, dS, dt):
        self.speed = dS/dt

    def update_compass(self, heading):
        self.heading = radians(heading)
        self.yaw = -self.heading

    def status(self):
        d = {}
        d['roll'] = self.roll
        d['pitch'] = self.pitch
        d['yaw'] = self.yaw
        d['x'] = self.x
        d['y'] = self.y
        d['z'] = self.z
        d['speed'] = self.speed
        d['time'] = self.time
        d['heading'] = self.heading
        return d

