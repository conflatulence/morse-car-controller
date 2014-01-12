#! /usr/bin/env morseexec

""" Basic MORSE simulation scene for <TestEnv> environment

Feel free to edit this template as you like!
"""

from morse.builder import *

from math import pi

# http://www.openrobots.org/morse/doc/stable/components_library.html
#
# 'morse add robot <name> TestEnv' can help you to build custom robots.
from TestEnv.builder.robots import Minihummer
robot = Minihummer()

# The list of the main methods to manipulate your components
# is here: http://www.openrobots.org/morse/doc/stable/user/builder_overview.html
robot.translate(-0.0, 0.0, 0.0)
robot.rotate(0,0,1.3)

# Add a pose sensor that exports the current location and orientation
# of the robot in the world frame
# Check here the other available actuators:
# http://www.openrobots.org/morse/doc/stable/components_library.html#sensors
#
# 'morse add sensor <name> TestEnv' can help you with the creation of a custom
# sensor.
#pose = Pose()
#robot.append(pose)

# To ease development and debugging, we add a socket interface to our robot.
#
# Check here: http://www.openrobots.org/morse/doc/stable/user/integration.html 
# the other available interfaces (like ROS, YARP...)
robot.add_default_interface('socket')
robot.motion.add_stream('socket')
robot.odometry.add_stream('socket')
robot.gps.add_stream('socket')
robot.compass.add_stream('socket')
robot.scanner.add_stream('scoket')

# set 'fastmode' to True to switch to wireframe mode
#env = Environment('sandbox', fastmode = False)
#env = Environment('empty', fastmode=False)
#env = Environment('outdoors', fastmode = False)
#env = Environment('plane.blend', fastmode=False)
env = Environment('environments/plane-with-obstacles.blend', fastmode=False)

env.set_camera_rotation([pi/4,0,0])
env.set_camera_location([0, -30, 30])
env.set_camera_speed(10)


