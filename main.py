#!/usr/bin/env python3

import logging
from logging import error, warning, info, debug
import json
import re
import asyncore
import signal

from client import Client
from server import Server
from utils import recursive_round
from speed_control import SpeedController
from collision_control import CollisionController
#from waypoint_control import WaypointController

class VehicleControls:
    def __init__(self):
        self.throttle = 0
        self.brake = 0
        self.steer = 0
        
    def status(self):
        d= {}
        d['throttle'] = self.throttle
        d['brake'] = self.brake
        d['steer'] = self.steer
        return d
        
class VehicleState:
    def __init__(self):
        self.roll = 0
        self.pitch = 0
        self.yaw = 0
        
        self.x = 0
        self.y = 0
        self.z = 0
        
        self.speed = 0
        
        self.time = 0
    
    def update_time(self, dt):
        self.time += dt
    
    def update_gps(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
    
    def update_odometry(self, dS, dt):
        self.speed = dS/dt

    def update_gyro(self, roll, pitch, yaw):
        self.roll = roll
        self.pitch = pitch
        self.yaw = yaw

    def status(self):
        d = {}
        d['roll'] = self.roll
        d['pitch'] = self.pitch
        d['yaw'] = self.yaw
        d['x'] = self.x
        d['y'] = self.y
        d['z'] = self.z
        d['speed'] = self.speed
        d['time'] = self.time
        return d

class Main:
    def __init__(self):
        self.sim_host = "localhost"
        self.service_port = 4000
        self.service_client = Client()
        self.service_client.msg_fn = self.on_service_message
        self.service_client.connect_fn = self.on_service_connect
        self.service_client.close_fn = self.on_service_disconnect
        self.service_client.create_connection(self.sim_host, self.service_port)
        
        self.motion_client = None
        self.range_client = None
        self.odometry_client = None

        self.status_server = Server(60212)
        self.status_server.connect_fn = self.on_status_client_connect
        self.status_server.msg_fn = self.on_status_client_msg
        self.status_server.close_fn = self.on_status_client_disconnect

        self.command_server = Server(60213)
        self.command_server.connect_fn = self.on_command_client_connect
        self.command_server.msg_fn = self.on_command_client_msg
        self.command_server.close_fn = self.on_command_client_disconnect

        self.controls = VehicleControls()
        self.state = VehicleState()
       
        self.speed_control = SpeedController(self.state, self.controls)        
        self.collision_control = CollisionController(self.state, self.controls, self.speed_control)
        #self.waypoint_control = WaypointController(self.state, self.collision_control)

    def exit(self):
        raise asyncore.ExitNow("Exiting")
    
    def send_service_message(self, identifier, component, message, data=[]):
        msg = '%s %s %s %s\n' % (identifier, component, message, json.dumps(data))
        self.service_client.send_msg(msg)

    # the steering value is in radians.
    def send_motion_message(self):
        debug('Sending motion message!')
        if self.motion_client is not None:
            # the sign of the throttle is reversed!
            d = {'steer':self.controls.steer, 'force':-self.controls.throttle, 'brake':self.controls.brake}
            line = json.dumps(d) + '\n'
            self.motion_client.send_msg(line)
        else:
            warning('Cannot send motion message without connection to motion controller.')

    def on_service_connect(self):
        info("Connected to morse service.")
        self.send_service_message('motion_port', 'simulation', 'get_stream_port', ['hummer.motion'])
        self.send_service_message('range_port', 'simulation', 'get_stream_port', ['hummer.scanner'])
        self.send_service_message('odometry_port', 'simulation', 'get_stream_port', ['hummer.odometry'])
        self.send_service_message('gps_port', 'simulation', 'get_stream_port', ['hummer.gps'])
        self.send_service_message('gyro_port', 'simulation', 'get_stream_port', ['hummer.gyroscope'])

    def on_service_disconnect(self):
        info("Disconnected from morse service.")
        self.exit()

    def on_service_message(self, line):
        m = re.match('^(?P<id>\w+) (?P<success>\w+) (?P<data>.*)$', line)
        if m is None:
            warning('Invalid service message:' + line)
            return
        
        if m.group('success') != 'SUCCESS':
            warning('Service command failed:' + line)
            return

        identifier = m.group('id')
        data = m.group('data')

        if identifier == 'motion_port':
            self.motion_client = Client()
            self.motion_client.create_connection(self.sim_host, int(data))
            self.motion_client.connect_fn = self.on_motion_connect
            self.motion_client.msg_fn = self.on_motion_message
            self.motion_client.close_fn = self.on_motion_disconnect

        elif identifier == 'range_port':
            self.range_client = Client()
            self.range_client.create_connection(self.sim_host, int(data))
            self.range_client.connect_fn = self.on_range_connect
            self.range_client.msg_fn = self.on_range_message
            self.range_client.close_fn = self.on_range_disconnect

        elif identifier == 'odometry_port':
            self.odometry_client = Client()
            self.odometry_client.create_connection(self.sim_host, int(data))
            self.odometry_client.connect_fn = self.on_odometry_connect
            self.odometry_client.msg_fn = self.on_odometry_message
            self.odometry_client.close_fn = self.on_odometry_disconnect
        
        elif identifier == 'gps_port':
            self.gps_client = Client()
            self.gps_client.create_connection(self.sim_host, int(data))
            self.gps_client.connect_fn = self.on_gps_connect
            self.gps_client.msg_fn = self.on_gps_message
            self.gps_client.close_fn = self.on_gps_disconnect
 
        elif identifier == 'gyro_port':
            self.gyro_client = Client()
            self.gyro_client.create_connection(self.sim_host, int(data))
            self.gyro_client.connect_fn = self.on_gyro_connect
            self.gyro_client.msg_fn = self.on_gyro_message
            self.gyro_client.close_fn = self.on_gyro_disconnect

        else:
            warning("Unhandled identifier:" + identifier)

    def on_motion_connect(self):
        info("Connected to motion port.")
        
    def on_motion_disconnect(self):
        info("Disconnected from motion port.")

    def on_motion_message(self, line):
        warning("Got unhandled motion message:" + line)

    def on_range_connect(self):
        info("Connected to range port.")
        
    def on_range_disconnect(self):
        info("Disconnected from range port.")
 
    def on_range_message(self, line):
        try:
            obj = json.loads(line)
            self.collision_control.update_range(obj['range_list'])
        except ValueError as err:
            error('Invalid range message:' + str(err))
            return

    def on_odometry_connect(self):
        info("Connected to odometry port.")
        
    def on_odometry_disconnect(self):
        info("Disconnected from odometry port.") 

    def on_odometry_message(self, line):
        try:
            obj = json.loads(line)

            dS = obj['dS']
            dt = 0.1
            self.state.update_time(dt)
            self.state.update_odometry(dS, dt)
            self.speed_control.update()
            self.send_motion_message()
            self.send_status()
                
        except ValueError as err:
            warning('Invalid odometry message:' + str(err))

    def on_gps_connect(self):
        info("Connected to gps port.")

    def on_gps_disconnect(self):
        info("Disconnected from gps port.")

    def on_gps_message(self, line):
        try:
            obj = json.loads(line)
            self.state.update_gps(obj['x'], obj['y'], obj['z'])
            # TODO: update the waypoing controller here?
        except ValueError as err:
            warning('Invalid gps message:' + str(err))

    def on_gyro_connect(self):
        info("Connected to gyro port.")

    def on_gyro_disconnect(self):
        info("Disconnected from gyro port.")
    
    def on_gyro_message(self, line):
        try:
            obj = json.loads(line)
            self.state.update_gyro(obj['roll'], obj['pitch'], obj['yaw'])
        except ValueError as err:
            warning("Invalid gyro message:" + str(err)) 
            
    def send_status(self):
        d = {}
        d['state'] = self.state.status()
        d['controls'] = self.controls.status()
        d['speed_control'] = self.speed_control.status()
        d['collision_control'] = self.collision_control.status()
        #d['waypoint_control'] = self.waypoint_control.status()
        
        msg = json.dumps(recursive_round(d,4)) + '\n'
        self.status_server.broadcast(msg)

    def on_status_client_connect(self):
        info("Status client connected.")
        
    def on_status_client_disconnect(self):
        info("Status client disconnected.")

    def on_status_client_msg(self, line):
        warning("Status client received message, but no messages are supported.")
    
    def on_command_client_connect(self):
        info("Command client connected.")
        
    def on_command_client_disconnect(self):
        info("Command client disconnected.")

    def on_command_client_msg(self, line):
        try:
            d = json.loads(line)
        except ValueError as err:
            warning("Client message is not valid JSON:" + str(err))
            return
        
        try:
            action, class_name, field_name, params = d
        except IndexError:
            warning("Invalid message:" + str(d))
            return
    
        if action == 'set':
            try:
                inst = getattr(self, class_name)
                if callable(getattr(inst, field_name)):
                    warning("Invalid message attempted to set a callable object.")
                    return
                setattr(inst, field_name, params)
            except AttributeError as err:
                warning("Invalid message recipient:" + str(err))
                return
            
        elif action == 'call':
            try:
                inst = getattr(self, class_name)
                func = getattr(inst, field_name)
            except AttributeError as err:
                warning("Invalid message recipient:" + str(err))
                return

            if not callable(func):
                warning("Invalid messaged attempted to call a non-callable object.")
                return
            
            if type(params) is list:
                func(*params)
            elif type(params) is dict:
                func(**params)
            else:
                warning("Invalid message params:" + str(params))
                return
        else:
            warning("Unknown action:" + action)
            return

def sigint_handler(signnum, frame):
    raise asyncore.ExitNow("Exiting")
    
if __name__ == '__main__':
    
    logging.basicConfig(level=logging.INFO)

    signal.signal(signal.SIGINT, sigint_handler)

    main = Main()

    try:
        asyncore.loop()
    except asyncore.ExitNow:
        pass
    
