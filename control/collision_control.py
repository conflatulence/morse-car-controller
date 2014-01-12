
from random import random
from math import pi, cos, sin, tan, radians, ceil
from utils import wrap_radians, clamp
from logging import error, warning, info, debug

from collections import namedtuple
Point = namedtuple('Point',['x','y'])

def make_path(steer_radians, step, path_length, vehicle_length):
    ds = step
    a = 0
    points = [Point(0,0)]
    if abs(steer_radians) > 0.1:
        L = vehicle_length #1.267
        R = L/tan(steer_radians)
        dt = ds/R
        a = 0
        t = dt
        while a < path_length:
            x = R*(1-cos(t))
            y = R*sin(t)
            points.append(Point(x,y))
            a += ds
            t += dt
    else:
        while a < path_length:
            a += ds
            x = 0
            y = a
            points.append(Point(x,y))
    return points

def reduce_scan_points(ranges, group_size):
    result = []
    count = 0
    for ray in ranges:
        if count == 0:
            result.append(ray)
        else:
            if result[-1] > ray:
                result[-1] = ray

        count += 1
        if count == group_size:
            count = 0

    return result

def scan_to_points(ranges, start_angle, angle_inc_degrees, non_range_val=-1, threshold=5):
    angle_degrees = start_angle
    points = []
    for r in ranges:
        if r != non_range_val and r < threshold:
            while r < 5:
                x = r*sin(radians(angle_degrees)) # distance to the right of the vehicle
                y = r*cos(radians(angle_degrees)) # distance ahead of the vehicle
                points.append(Point(x,y))
                r += 1
        angle_degrees += angle_inc_degrees
    return points

def path_near_points(path, points, threshold):
    D = threshold**2
    for a in path:
        for b in points:
            d = (a.x - b.x)**2 + (a.y - b.y)**2
            if d < D:
                return True
    return False

class CollisionController:
    def __init__(self, state, speed_control, basic_controls):
        self.vstate = state
        self.speed_control = speed_control
        self.basic_controls = basic_controls
        
        self.blocked = False
        self.enabled = True

        self.degrees_per_ray = 5
        self.left_most_ray_degrees = -90
        self.right_most_ray_degrees = 90
        self.vehicle_length = 0.75 #1.267
        self.non_range_val = 5 # indicates the scanner didn't pick up anything.

        self.requested_steer = 0
        self.requested_speed = 0
        self.actual_steer = 0
        self.requested_distance = 0

        self.last_obstacles = [] 
        self.last_path = []

    def update_range(self, ranges):

        if not self.enabled:
            return

        scan_points = scan_to_points(ranges, self.right_most_ray_degrees, -self.degrees_per_ray)
        self.last_obstacles = scan_points

        if len(scan_points) == 0:
            if self.requested_speed > 0:
                self.blocked = False
                self.actual_steer = self.requested_steer
                self.basic_controls.set_steer(self.actual_steer)
                self.speed_control.set_speed(self.requested_speed)
                self.last_path = []
        else:
            for dev in [0,-2,2,-4,4,-6,6,-8,8]:
                steer = self.requested_steer + dev*pi/16.0
                if abs(steer) > pi/4:
                    continue	
                
                path_length = min(self.requested_distance, 5)

                path_points = make_path(steer, 0.25, path_length, self.vehicle_length)

                if not path_near_points(path_points, scan_points, 1.5):
                    self.actual_steer = steer
                    if self.requested_speed > 0:
                        self.basic_controls.set_steer(self.actual_steer)
                        self.speed_control.set_speed(self.requested_speed)
                    self.blocked = False
                    self.last_path = path_points
                    break
            else:
                # no path found
                self.blocked = True
                if self.requested_speed > 0:
                    self.speed_control.stop()

    def set_steer(self, angle):
        angle = clamp(-pi/4, pi/4, angle)
        # allow manual external steering control in reverse.
        if not self.enabled or self.requested_speed < 0:
            self.basic_controls.set_steer(angle)
            self.requested_steer = angle
            self.actual_steer = angle
        else:
            self.requested_steer = angle

    def set_speed(self, speed):
        self.requested_speed = speed
        if not self.enabled or speed < 0:
            self.basic_controls.set_steer(self.requested_steer)
            self.speed_control.set_speed(speed)

    def set_distance(self, distance):
        self.requested_distance = distance
    
    def adjust_speed(self, amount):
        speed = self.requested_speed + amount
    
    def stop(self):
        self.speed_control.stop()
        self.requested_speed = 0
    
    def status(self):
        d = {}
        d['enabled'] = self.enabled
        d['blocked'] = self.blocked
        d['path'] = self.last_path
        d['obstacles'] = self.last_obstacles
        d['requested_steer'] = self.requested_steer
        return d

