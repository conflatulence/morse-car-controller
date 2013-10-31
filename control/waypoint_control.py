
from math import atan2, sqrt, pi

class WaypointController:
    def __init__(self, state, collision_control):
        self.state = state
        self.collision_control = collision_control
        self.points = []
        self.last_distance = 0
        self.last_direction = 0
        self.enabled = False
        self.forward_speed = 2
        self.reverse_speed = 2
        self.reverse_turn = pi/3
        self.completion_distance = 2
    
    def add_waypoint(self, x, y):
        self.points.append((x,y))
    
    def add_waypoints(self, points):
        self.points += points
    
    def clear_waypoints(self):
        self.points = []

    def update(self):
        if not self.enabled:
            return
        
        if len(self.points) > 0:
            x,y = self.points[0]
            distance = self.calc_distance(x, y)
            direction = self.calc_direction(x, y)
            if distance < self.completion_distance:
                self.points.pop(0)
            elif self.collision_control.blocked:
                self.collision_control.set_steer(-self.reverse_turn)
                self.collision_control.set_speed(-self.reverse_speed)
            else:
                self.collision_control.set_heading(direction)
                self.collision_control.set_speed(self.forward_speed)
            self.last_distance = distance
            self.last_direction = direction
            
        else:
            self.collision_control.stop()

    def status(self):
        d = {}
        d['enabled'] = self.enabled
        d['points'] = self.points
        d['distance'] = self.last_distance
        d['direction'] = self.last_direction
        return d

    # distance to point x,y
    def calc_distance(self, x, y):
        return sqrt((x - self.state.x)**2 + (y - self.state.y)**2)
 
    # direction to point x,y
    def calc_direction(self, x, y):
        return atan2((x - self.state.x), y - self.state.y)
        
