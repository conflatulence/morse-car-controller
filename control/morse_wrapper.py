from math import sqrt,atan2
from geomath import GeoPoint, point_from_xy

class MorseWrapper:
    def __init__(self):
        self.origin = GeoPoint(-33.80784, 151.176614)
        self.last_x = None
        self.last_y = None
        self.last_t = None

    def pose_message(self, msg):
        x = msg['x']
        y = msg['y']
        t = msg['timestamp']/1000.0 # change to seconds.

        if self.last_t != None:
            dx = x - self.last_x
            dy = y - self.last_y
            dt = t - self.last_t
            speed = sqrt(dx**2 + dy**2)*dt
            heading = atan2(dx, dy)
        else:
            speed = 0.0
            heading = 0.0

        lat,lon = point_from_xy(self.origin, x, y)
        alt = msg['z']

        gps_msg = {'lat':lat, 'lon':lon, 'alt':alt,
                   'speed':speed,'heading':heading}
        
        compass_msg = {'heading':-msg['yaw']}

        self.last_x = x
        self.last_y = y
        self.last_t = t

        return gps_msg, compass_msg


