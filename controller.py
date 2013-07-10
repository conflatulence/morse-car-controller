#!/usr/bin/env python3

import logging
from logging import error, warning, info, debug
import json
import re
import asyncore
import signal

from math import pi

from client import Client
from server import Server
from utils import Position
from speed_control import SpeedController
from auto_reverse import AutoReverseController

class Main:
    def __init__(self):
        self.sim_host = "localhost"
        self.service_port = 4000
        self.service_client = Client()
        self.service_client.msg_fn = self.on_service_message
        self.service_client.connect_fn = self.on_service_connect
        self.service_client.create_connection(self.sim_host, self.service_port)
        
        self.motion_client = None
        self.range_client = None
        self.odometry_client = None

        self.server = Server(60212)
        self.server.connect_fn = self.on_client_connect
        self.server.msg_fn = self.on_client_msg
        self.server.close_fn = self.on_client_disconnect
        
        self.throttle = 0
        self.steer = 0
        self.brake = 0

        self.current_speed = 0
        self.dodging = False
        
        self.gps = Position()
        self.mode = 'park'
        self.speed_control = SpeedController(self)        
        self.reverse_controller = AutoReverseController(self, self.speed_control)

    def send_service_message(self, identifier, component, message, data=[]):
        msg = '%s %s %s %s\n' % (identifier, component, message, json.dumps(data))
        self.service_client.send_msg(msg)

    # the steering value is in radians.
    def send_motion_message(self):
        debug('Sending motion message!')
        if self.motion_client is not None:
            # the sign of the throttle is reversed!
            d = {'steer':self.steer, 'force':-self.throttle, 'brake':self.brake}
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

        elif identifier == 'range_port':
            self.range_client = Client()
            self.range_client.create_connection(self.sim_host, int(data))
            self.range_client.connect_fn = self.on_range_connect
            self.range_client.msg_fn = self.on_range_message

        elif identifier == 'odometry_port':
            self.odometry_client = Client()
            self.odometry_client.create_connection(self.sim_host, int(data))
            self.odometry_client.connect_fn = self.on_odometry_connect
            self.odometry_client.msg_fn = self.on_odometry_message
        
        elif identifier == 'gps_port':
            self.gps_client = Client()
            self.gps_client.create_connection(self.sim_host, int(data))
            self.gps_client.connect_fn = self.on_gps_connect
            self.gps_client.msg_fn = self.on_gps_message
        
        else:
            warning("Unhandled identifier:" + identifier)

    def on_motion_connect(self):
        info("Connected to motion port.")

    def on_motion_message(self, line):
        warning("Got unhandled motion message:" + line)

    def on_range_connect(self):
        info("Connected to range port.")
 
    def on_range_message(self, line):
        try:
            obj = json.loads(line)
        except ValueError as err:
            error('Invalid range message:' + str(err))
            return
         
        ranges = obj['range_list']
        N = len(ranges)
        
        if min(ranges) < 0:
            warning('Range message was less than 0 (%d)' % (min(ranges)))

        min_left = min(ranges[0:int(N/3)])
        min_middle = min(ranges[int(N/3):int(2*N/3)])
        min_right = min(ranges[int(2*N/3):N])
        
        self.reverse_controller.update_range(min_left, min_middle, min_right)

    def on_odometry_connect(self):
        info("Connected to odometry port")

    def on_odometry_message(self, line):
        try:
            obj = json.loads(line)
            #print 'Odometry:', obj
            dS = obj['dS']
            dt = 0.1
            self.current_speed = dS/dt
            self.speed_control.update(self.current_speed, dt)
            self.send_motion_message()
            #self.drawing_area.queue_draw()
            self.send_state()
                
        except ValueError as err:
            warning('Invalid odometry message:' + str(err))

    def on_gps_connect(self):
        info("Connected to gps port.")

    def on_gps_message(self, line):
        try:
            obj = json.loads(line)
            self.gps.x = obj['x']
            self.gps.y = obj['y']
            self.gps.z = obj['z']
            
        except ValueError as err:
            warning('Invalid gps message:' + str(err))
            
    def send_state(self):
        d = {}
        d['mode'] = 'drive'
        d['throttle'] = round(self.throttle, 2)
        d['brake'] = round(self.brake, 2)
        d['steer'] = round(self.steer, 2)
        d['current_speed'] = round(self.current_speed, 2)
        d['target_speed'] = round(self.speed_control.target_speed, 2)
        d['current_pos'] = [round(self.gps.x, 2), round(self.gps.y, 2)]

        msg = json.dumps(d) + '\n'
        self.server.broadcast(msg)

    def on_client_connect(self):
        info("Client connected.")
        
    def on_client_disconnect(self):
        info("Client disconnected.")

    def on_client_msg(self, line):
        try:
            d = json.loads(line)
        except ValueError as err:
            warning("Invalid client message:" + str(err))
        
        if 'stop' in d:
            self.speed_control.stop()
        
        if 'adjust_speed' in d:
            self.speed_control.adjust_speed(d['adjust_speed'])
        
        if 'set_speed' in d:
            self.speed_control.set_speed(d['set_speed'])
        
        if 'steer' in d:
            self.steer = d['steer']
        
        if 'throttle' in d:
            self.throttle = d['throttle']
        
        if 'brake' in d:
            self.brake = d['brake']

        if 'mode' in d:
            self.mode = d['mode']

#     def on_key_press(self, w, event):
#         if event.string == 'q' or event.keyval == Gdk.KEY_Escape:
#             Gtk.main_quit()
# 
#         elif event.keyval == Gdk.KEY_Left:
#             #print 'Left pressed'
#             if not self.dodging:
#                 self.steer = pi/4
# 
#         elif event.keyval == Gdk.KEY_Right:
#             #print 'Right pressed'
#             if not self.dodging:
#                 self.steer = -pi/4
# 
#         elif event.keyval == Gdk.KEY_Up:
#             #print 'Up pressed'
#             self.speed_control.adjust_speed(1.0)
# 
#         elif event.keyval == Gdk.KEY_Down:
#             self.speed_control.adjust_speed(-1.0)
# 
#         elif event.keyval == Gdk.KEY_space:
#             #print 'Space pressed'
#             self.speed_control.stop()
#             
#         elif event.keyval == Gdk.KEY_a:
#             self.reverse_controller.start()
#         
#         elif event.keyval == Gdk.KEY_s:
#             self.reverse_controller.stop()
# 
#     def on_key_release(self, w, event):
#         if event.keyval == Gdk.KEY_Left:
#             #print 'Left released'
#             self.steer = 0
# 
#         elif event.keyval == Gdk.KEY_Right:
#             #print 'Right released'
#             self.steer = 0
# 
#         elif event.keyval == Gdk.KEY_Up:
#             #print 'Up released'
#             pass
# 
#         elif event.keyval == Gdk.KEY_Down:
#             #print 'Down released'        
#             pass

def sigint_handler(signnum, frame):
    raise asyncore.ExitNow("Exiting")
    
if __name__ == '__main__':
    
    logging.basicConfig(level=logging.INFO)

    signal.signal(signal.SIGINT, sigint_handler)

    main_window = Main()

    try:
        asyncore.loop()
    except asyncore.ExitNow:
        pass
    
