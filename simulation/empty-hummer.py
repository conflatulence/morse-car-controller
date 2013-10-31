from morse.builder import *
from math import pi

hummer = Hummer()

motion = SteerForce()
hummer.append(motion)

odometry = Odometry()
odometry.level('raw')
odometry.frequency(10)
hummer.append(odometry)

gps = GPS()
gps.frequency(10)
gps.properties(origin_lat=-33.80784, origin_lon=151.176614)
hummer.append(gps)

compass = Compass()
compass.frequency(10)
hummer.append(compass)

scanner = Hokuyo()
scanner.translate(0, 2.5, 0)
scanner.rotate(0, 0, pi/2)
scanner.frequency(10)
scanner.properties(scan_window=180);
scanner.properties(laser_range=5)
scanner.properties(resolution=5)
scanner.properties(Visible_arc=True)
hummer.append(scanner)

motion.add_stream('socket')
odometry.add_stream('socket')
scanner.add_stream("socket")
gps.add_stream("socket")
compass.add_stream("socket")

#env = Environment('environments/empty.blend', fastmode=True)
env = Environment('./environments/empty.blend', fastmode=True)
#env = Environment('empty')
env.set_camera_rotation([pi/4,0,0])
env.set_camera_location([0, -50, 50])
env.set_camera_speed(10)
