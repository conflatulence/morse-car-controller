
from math import atan2, sqrt, degrees

class WaypointController:
    def __init__(self, state, controller):
        self.state = state
        self.controller = controller
        self.remaining = []
        self.next = None
        self.pos = None
        self.distance = -1
        self.direction = 0
        
    def add(self, points):
        self.remaining += points
        if self.next is None:
            self.next = self.remaining.pop(0)
    
    def clear(self):
        self.remaining = []
        self.next = None

    def update(self, pos):
        self.pos = pos
        self.distance = self.get_distance()
        self.direction = self.get_direction()

    def status(self):
        d = {}
        if self.position is not None:
            d['position'] = (self.pos.x, self.pos.y)

        if self.next is not None:
            d['next'] = (self.next.x, self.next.y)
        
        d['distance'] = self.distance,
        d['direction'] = degrees(self.direction) 
        
        return d

    # return the distance to the next waypoint.
    def get_distance(self, pos=None):
        if pos is None:
            pos = self.pos
            
        if self.next is not None:
            return sqrt((self.next.x - pos.x)**2 + (self.next.y - pos.y)**2)
        else:
            return -1

    # return the direction to the next waypoint.
    def get_direction(self, pos=None):
        if pos is None:
            pos = self.pos
            
        if self.next is not None:
            return atan2(self.next.y - pos.y, self.next.x - pos.x)
        else:
            return -1
        