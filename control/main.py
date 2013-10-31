#!/usr/bin/env python3

import logging
from logging import error, warning, info, debug
import json
import re
import asyncore
import signal

from client import Client
from server import Server
from utils import recursive_round, clamp

from controls import VehicleControls
from state import VehicleState
from speed_control import SpeedController
from steering_control import SteeringController
from collision_control import CollisionController
from waypoint_control import WaypointController

class Main:
    def __init__(self):
        self.sim_host = "localhost"
        self.service_port = 4000
        self.service_client = Client(connect_fn=self.service_connect, msg_fn=self.service_message, close_fn=self.service_disconnect)
        self.service_client.create_connection(self.sim_host, self.service_port)

        self.status_server = Server(60212, self.status_client_connect, self.status_client_msg, self.status_client_disconnect)
        self.command_server = Server(60213, self.command_client_connect, self.command_client_msg, self.command_client_disconnect)

        self.controls = VehicleControls()
        self.state = VehicleState()
        self.speed_control = SpeedController(self.state, self.controls)
        self.steering_control = SteeringController(self.state, self.controls)
        self.collision_control = CollisionController(self.state, self.speed_control, self.steering_control)
        self.waypoint_control = WaypointController(self.state, self.collision_control)

    def exit(self):
        raise asyncore.ExitNow("Exiting")
    
    def send_service_message(self, identifier, component, message, data=[]):
        msg = '%s %s %s %s\n' % (identifier, component, message, json.dumps(data))
        self.service_client.send_msg(msg)

    # morse convention is +steer to the left and +force is backwards.
    # The controls class is switched so +steer is to the right and +force is forwards.
    def send_motion_message(self):
        debug('Sending motion message!')
        if self.motion_client is not None:
            # the sign of the throttle is reversed!
            d = {'steer':-self.controls.steer, 'force':-self.controls.throttle, 'brake':self.controls.brake}
            line = json.dumps(d) + '\n'
            self.motion_client.send_msg(line)
        else:
            warning('Cannot send motion message without connection to motion controller.')

    def service_connect(self, client):
        info("Connected to morse service.")
        self.send_service_message('motion_port', 'simulation', 'get_stream_port', ['hummer.motion'])
        self.send_service_message('range_port', 'simulation', 'get_stream_port', ['hummer.scanner'])
        self.send_service_message('odometry_port', 'simulation', 'get_stream_port', ['hummer.odometry'])
        self.send_service_message('gps_port', 'simulation', 'get_stream_port', ['hummer.gps'])
        self.send_service_message('compass_port', 'simulation', 'get_stream_port', ['hummer.compass'])

    def service_disconnect(self, client):
        info("Disconnected from morse service.")
        self.exit()

    def service_message(self, client, line):
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
            self.motion_client = Client(connect_fn=self.motion_connect, msg_fn=self.motion_message, close_fn=self.motion_disconnect)
            self.motion_client.create_connection(self.sim_host, int(data))

        elif identifier == 'range_port':
            self.range_client = Client(connect_fn=self.range_connect, msg_fn = self.range_message, close_fn=self.range_disconnect)
            self.range_client.create_connection(self.sim_host, int(data))

        elif identifier == 'odometry_port':
            self.odometry_client = Client(connect_fn=self.odometry_connect, msg_fn=self.odometry_message, close_fn=self.odometry_disconnect)
            self.odometry_client.create_connection(self.sim_host, int(data))

        elif identifier == 'gps_port':
            self.gps_client = Client(connect_fn=self.gps_connect, msg_fn=self.gps_message, close_fn=self.gps_disconnect)
            self.gps_client.create_connection(self.sim_host, int(data))

        elif identifier == 'compass_port':
            self.compass_client = Client(connect_fn=self.compass_connect, msg_fn=self.compass_message, close_fn=self.compass_disconnect)
            self.compass_client.create_connection(self.sim_host, int(data))

        else:
            warning("Unhandled identifier:" + identifier)

    def motion_connect(self, client):
        info("Connected to motion port.")
        
    def motion_disconnect(self, client):
        info("Disconnected from motion port.")

    def motion_message(self, client, line):
        warning("Got unhandled motion message:" + line)

    def range_connect(self, client):
        info("Connected to range port.")
        
    def range_disconnect(self, client):
        info("Disconnected from range port.")
 
    def range_message(self, client, line):
        try:
            obj = json.loads(line)
            self.collision_control.update_range(obj['range_list'])
        except ValueError as err:
            error('Invalid range message:' + str(err))
            return

    def odometry_connect(self, client):
        info("Connected to odometry port.")
        
    def odometry_disconnect(self, client):
        info("Disconnected from odometry port.") 

    def odometry_message(self, client, line):
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

    def gps_connect(self, client):
        info("Connected to gps port.")

    def gps_disconnect(self, client):
        info("Disconnected from gps port.")

    def gps_message(self, client, line):
        try:
            obj = json.loads(line)
            self.state.update_gps(obj['lat'], obj['lon'], obj['alt'], obj['speed'], obj['heading'])
            self.waypoint_control.update()
        except ValueError as err:
            warning('Invalid gps message:' + str(err))

    def compass_connect(self, client):
        info("Connected to compass port.")

    def compass_disconnect(self, client):
        info("Disconnected from compass port.")
    
    def compass_message(self, client, line):
        try:
            obj = json.loads(line)
            self.state.update_compass(obj['heading'])
            self.steering_control.update_heading()
        except ValueError as err:
            warning("Invalid compass message:" + str(err)) 
            
    def send_status(self):
        d = {}
        d['state'] = self.state.status()
        d['controls'] = self.controls.status()
        d['speed_control'] = self.speed_control.status()
        d['steering_control'] = self.steering_control.status()
        d['collision_control'] = self.collision_control.status()
        d['waypoint_control'] = self.waypoint_control.status()
        
        msg = json.dumps(recursive_round(d,4)) + '\n'
        self.status_server.broadcast(msg)

    def status_client_connect(self, client):
        info("Status client connected.")
        
    def status_client_disconnect(self, client):
        info("Status client disconnected.")

    def status_client_msg(self, client, line):
        warning("Status client received message, but no messages are supported.")
    
    def command_client_connect(self, client):
        info("Command client connected.")
        
    def command_client_disconnect(self, client):
        info("Command client disconnected.")

    def command_client_msg(self, client, line):
        try:
            d = json.loads(line)
        except ValueError as err:
            client.send_msg("ERROR: Client message is not valid JSON:" + str(err))
            return
        
        try:
            action, class_name, field_name, params = d
        except IndexError:
            client.send_msg("ERROR: Invalid message:" + str(d))
            return
    
        if action == 'set':
            try:
                inst = getattr(self, class_name)
                if callable(getattr(inst, field_name)):
                    client.send_msg("ERROR: Invalid message attempted to set a callable object.")
                    return
                setattr(inst, field_name, params)
            except AttributeError as err:
                client.send_msg("ERROR: Invalid message recipient:" + str(err))
                return
            
        elif action == 'call':
            try:
                inst = getattr(self, class_name)
                func = getattr(inst, field_name)
            except AttributeError as err:
                client.send_msg("ERROR: Invalid message recipient:" + str(err))
                return

            if not callable(func):
                warning("ERROR: Invalid messaged attempted to call a non-callable object.")
                return
            
            try:
                if type(params) is list:
                    func(*params)
                elif type(params) is dict:
                    func(**params)
                else:
                    client.send_msg("ERROR: Invalid message params:" + str(params))
                    return
            except Exception as err:
                client.send_msg("ERROR: Call message caused an exception:" + err)
        else:
            client.send_msg("ERROR: Unknown action:" + action)
            return
        
        client.send_msg("OK")

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
    
