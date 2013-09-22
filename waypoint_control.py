
from math import atan2, sqrt, pi

class WaypointController:
    def __init__(self, state, controller):
        self.state = state
        self.controller = controller
        self.points = []
        self.dist = 0
        self.dir = 0
        self.enabled = False
        
    def add_points(self, points):
        self.points += points
    
    def clear_points(self):
        self.points = []

    def update(self):
        if not self.enabled:
            return
        
        if len(self.points) > 0:
            x,y = self.points[0]
            self.dist = self.distance(x, y)
            self.dir = self.direction(x, y)
            if self.distance < 2:
                self.points.pop(0)
            elif self.controller.blocked:
                self.controller.set_steer(-pi/3)
                self.controller.set_speed(-3)
            else:
                self.controller.set_heading(self.dir)
                self.controller.set_speed(3)
        else:
            self.controller.stop()

    def status(self):
        d = {}
        d['enabled'] = self.enabled
        d['points'] = self.points
        d['distance'] = self.distance
        d['direction'] = self.direction
        return d

    # distance to point x,y
    def distance(self, x, y):
        return sqrt((x - self.state.x)**2 + (y - self.state.y)**2)
 
    # direction to point x,y
    def direction(self, x, y):
        return atan2(y - self.state.y, x - self.state.x)
        