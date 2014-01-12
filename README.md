Introduction
============

The goal has been to develop a car-driving program that can avoid collision and drive to waypoints in the MORSE simulator. The car is a hobby R/C-sized car with a 5-meter range LIDAR on the front along with GPS and compass.

Dependencies
============

MORSE installation instructions are here:
http://www.openrobots.org/morse/doc/latest/user/installation.html

There are some changes to MORSE (add lat/lon to GPS sensor and add compass sensor) used by this project, a fork of morse with these changes is here: https://github.com/conflatulence/morse.

This project is using the MORSE socket interface so you don't need ROS or YARP.

The graphical programs are using PyQt4 and PyQWT. Unfortunately they are python2 only.

On Fedora 19 for example, install all the dependencies except for MORSE using yum:
yum install blender python3 PyQWT

Directory Layout
================

simulation
----------

Contains files used by MORSE. These files describe the robot platform, actuators, sensors and environment.

The robot is currently a car with a LIDAR on the front for collision detection and a few other sensors like position and orientation.

The important files are in simulation/TestEnv.

simulation/TestEnv/default.py puts the robot in the environment. This is the script to edit if you want to change the environment or the car's starting position.

simulation/TestEnv/src/TestEnv/robots/MiniHummer.py is the mechanical description of the car. It is copied from MORSE's hummer robot, but scaled down.

simulation/TestEnv/src/TestEnv/builder/robots/MiniHummer.py adds the sensors and actuators (LIDARcompass, GPS, steer, throttle, brake) to the car.

control 
-------

Code which reacts to senors and user input and sets actuator values accordingly. This is intended to run on the car's on-board computer.

The most important files here are:
main.py: this is the entry point to the controller. It connects with the simulated sensors and actuators. It also provides two servers. One is a status server which is a great spew of information about sensor values and other important stuff inside the controller program. The other server is for users to send commands to the car to do stuff and change various parameters of the controller.

user
----

Code that is useful for telling the car what to do and looking at status/debugging information. 

The important files here are:
cmd.py: this is a command line program for sending commands to the car. When run, it will connect to the car's command server and then send each command listed in the supplied text file. Example command files are given in the cmd subdirectory.
monitor.py: this is a GUI program that reads the controller's status server and displays most of the interesting data big numbers.
graph.py: another GUI like monitory.py but shows the variables graphed over time. This is more useful for determining wtf just happend.
map.py: another GUI, this shows the bird's eye view of the car in it's environment. It shows things like the position, heading and waypoints.
collision.py: another GUI, shows the scans and predicted paths from the collision controller.

Usage
=====

I like to do this in 3 separate terminals. For each term, cd to the morse-car-controller checkout.

In Term 1, start morse

	cd simulator
	export MORSE_RESOURCE_PATH=$PWD
	morse run TestEnv

The morse window should appear with the car in the middle of the window.

In Term 2, start the controller

	cd controller
	./main.py

The controller should display a few messages saying it has connected with various sensors in morse.

In Term 3, tell the car to do something, drive to a waypoint for example. There are example command files in user/cmds. example-go.cmd changes some paremeters of the speed controller, sets some waypoints and then enables the waypoint controller, causing the car to start driving to the first waypoint.

	cd user
	./sendcmd.py cmds/example-go.cmd

That should be enough to see the car do something.

The various monitor programs can be run from a 4th terminal. They don't require any arguments. e.g.

	cd user
	./monitor.py &
	./map.py &


