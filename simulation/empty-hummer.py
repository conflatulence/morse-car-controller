from morse.builder import *
from math import pi

# Land robot
hummer = Hummer()

pose = Pose()
#pose.translate(z = 0.75)
hummer.append(pose)

motion = SteerForce()
hummer.append(motion)

odometry = Odometry()
odometry.level('raw')
odometry.frequency(10)
hummer.append(odometry)

gps = GPS()
hummer.append(gps)

gyroscope = Gyroscope()
hummer.append(gyroscope)

#scanner = Sick()
scanner = Hokuyo()
scanner.translate(0, 2.5, 0)
scanner.rotate(0, 0, pi/2)
scanner.frequency(10)
scanner.properties(scan_window=180);
scanner.properties(laser_range=5)
scanner.properties(resolution=5)
scanner.properties(Visible_arc=True)
hummer.append(scanner)

# Scene configuration
pose.add_service('socket')
motion.add_service('socket')
motion.add_interface('socket')
odometry.add_interface('socket')
odometry.add_service('socket')
scanner.add_interface("socket")
scanner.add_service("socket")
gps.add_interface("socket")
gps.add_service("socket")
gyroscope.add_interface("socket")
gyroscope.add_service("socket")

#env = Environment('indoors-1/indoor-1')
env = Environment('./environments/empty.blend', fastmode=True)
#env.place_camera([5, -5, 6])
#env.aim_camera([1.0470, 0, 0.7854])
#env = Environment('empty')
env.aim_camera([pi/4,0,0])
env.place_camera([0, -50, 50])
env.set_camera_speed(10)
