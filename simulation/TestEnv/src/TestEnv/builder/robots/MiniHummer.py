from morse.builder import *

from math import pi

class Minihummer(Robot):
    """
    A template robot model for MiniHummer, with a motion controller and a pose sensor.
    """
    def __init__(self, name = None, debug = True):

        print("############################### THIS LINE WAS EXECUTED ###############################")

        # MiniHummer.blend is located in the data/robots directory
        Robot.__init__(self, 'TestEnv/robots/MiniHummer.blend', name)
        self.properties(classpath = "TestEnv.robots.MiniHummer.Minihummer")

        ###################################
        # Actuators
        ###################################

        self.motion = SteerForce()
        self.append(self.motion)

        ###################################
        # Sensors
        ###################################

        self.odometry = Odometry()
        self.odometry.level('raw')
        self.odometry.frequency(10)
        self.append(self.odometry)

        self.gps = GPS()
        self.gps.frequency(10)
        self.gps.properties(origin_lat=-33.80784, origin_lon=151.176614)
        self.gps.alter('GPSNoise', latlon_stddev=3, alt_stddev=3, speed_stddev=1, heading_stddev=1)
        self.append(self.gps)

        self.compass = Compass()
        self.compass.frequency(10)
        self.compass.alter('CompassNoise', heading_stddev=5, heading_bias=0)
        self.append(self.compass)

        self.scanner = Hokuyo()
        self.scanner.translate(0, 2.5/3, 0)
        self.scanner.rotate(0, 0, pi/2)
        self.scanner.frequency(10)
        self.scanner.properties(scan_window=180);
        self.scanner.properties(laser_range=5)
        self.scanner.properties(resolution=5)
        self.scanner.properties(Visible_arc=True)
        self.append(self.scanner)


