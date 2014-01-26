
from random import random
from math import pi, cos, sin, tan, radians, ceil, sqrt
from utils import wrap_radians, clamp
from logging import error, warning, info, debug

from collections import namedtuple
Point = namedtuple('Point',['x','y'])

def make_path(steer_radians, step, path_length):
    ds = step
    a = 0
    points = [Point(0,0)]
    if abs(steer_radians) > 0.1:
        sign = 1 if steer_radians > 0 else -1
        L = (1.6 + 2.3)/3.0 # vehicle length
        Lm = 2.3/3.0 # distance from vehicle's 'center' to the back axle
        R = L/tan(abs(steer_radians))
        Rm = sqrt(Lm**2 + R**2) # radius to vehicle mid-point
        Rm*=1.0 # hack to mess with the turning circle.
        dt = ds/Rm # angle increment
        a = 0
        t = dt
        while a < path_length:
            x = sign*Rm*(1-cos(t))
            y = Rm*sin(t)
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
    ''' Return the index of the first point in the path that is
    less than threshold distance to one of the points. Otherwise
    return None.'''

    D = threshold**2
    num = 0

    for a in path:
        for b in points:
            d = (a.x - b.x)**2 + (a.y - b.y)**2
            if d < D:
                return num
        num += 1
    return None

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
        self.non_range_val = 5 # indicates the scanner didn't pick up anything.

        self.requested_steer = 0
        self.requested_speed = 0
        self.actual_steer = 0
        self.requested_distance = 0

        self.last_obstacles = [] 
        self.last_path = []
        self.blocked_paths = []
        self.max_steer = pi/4
        self.max_req_steer = pi/12

    def update_range(self, ranges):

        if not self.enabled:
            return

        scan_points = scan_to_points(
            ranges, self.right_most_ray_degrees, -self.degrees_per_ray)
        self.last_obstacles = scan_points

        # if there are no obstacles.
        if len(scan_points) == 0:
            if self.requested_speed > 0:
                self.blocked = False
                self.actual_steer = clamp(-pi/9, pi/9, self.requested_steer)
                self.basic_controls.set_steer(self.actual_steer)
                self.speed_control.set_speed(self.requested_speed)
                self.last_path = []
        else: # there are obstacles.
            self.blocked_paths = []
            for dev in [0,-1,1,-2,2,-3,3,-4,4,-6,6,-8,8]:
                # when there's obstacles around, don't allow the
                # heading control to turn sharply.
                req_steer = clamp(-pi/12, pi/12, self.requested_steer)
                steer = req_steer + dev*pi/9.0

                if abs(steer) > self.max_steer:
                    continue

                path_length = min(self.requested_distance, 5)

                path_points = make_path(steer, 0.25, path_length)

                left_path = [Point(x-1.0, y) for x,y in path_points]
                right_path = [Point(x+1.0, y) for x,y in path_points]

                left_index = path_near_points(left_path, scan_points, 0.5)
                right_index = path_near_points(right_path, scan_points, 0.5)

                if left_index or right_index:
                    self.blocked_paths += path_points
                else: # path is clear
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
                self.last_path = []
                if self.requested_speed > 0:
                    self.speed_control.stop()

    def set_steer(self, angle):
        angle = clamp(-self.max_steer, self.max_steer, angle)
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
        d['blocked_paths'] = self.blocked_paths
        d['obstacles'] = self.last_obstacles
        d['requested_steer'] = self.requested_steer
        return d

