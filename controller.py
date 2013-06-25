#!/usr/bin/env python

from gi.repository import Gtk
from gi.repository import Gdk

import sys
import logging
from logging import error, warning, info
import json
import re
from math import pi, cos, sin

from client import Client

def clamp(min_val, max_val, val):
    if val < min_val:
        return min_val
    if val > max_val:
        return max_val
    return val

class SpeedController:
    def __init__(self):
        self.target_speed = 0
        self.stopping = False
        self.last_integral = 0
        self.last_error = 0
        self.Kp = 10
        self.Ki = 5
        self.Kd = 0
        
        self.throttle = 0
        self.brake = 0
        
    def stop(self, controls):
        self.stopping = True
        self.target_speed = 0 
        controls.throttle = 0
        controls.brake = 2
        
    def set_speed(self, speed, controls):
        if self.target_speed > 0 and speed < 0 or self.target_speed < 0 and speed > 0:
            self.stop()

        self.target_speed = clamp(-10, 10, speed)
        
    def adjust_speed(self, amount, controls):
        self.set_speed(self.target_speed + amount, controls) 

    def update(self, current_speed, dt, controls):        
        assert(current_speed >= 0)
        
        if self.stopping and abs(current_speed) < 0.1:
            self.stopping = False
                
        if self.stopping:
            integral = 0
            error = 0
            throttle = 0
            brake = 2
        else:
            error = abs(self.target_speed) - current_speed
            integral = self.last_integral + error*dt
            derivative = (error - self.last_error)/dt
            
            throttle = self.Kp*error + self.Ki*integral + self.Kd*derivative
            
            throttle = clamp(0, 40, throttle)
            brake = 0
            
            if self.target_speed < 0:
                throttle = -throttle

        self.last_error = error
        self.last_integral = integral
        
        controls.throttle = throttle
        controls.brake = brake

class MainWindow:
    def __init__(self):
        w = Gtk.Window()
        w.set_default_size(300, 300)
        self.drawing_area = Gtk.DrawingArea()
        w.add(self.drawing_area)

        w.connect('destroy', Gtk.main_quit)

        self.drawing_area.connect('draw', self.on_draw)
        self.drawing_area.set_can_focus(True)
        self.drawing_area.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.drawing_area.add_events(Gdk.EventMask.KEY_PRESS_MASK)
        self.drawing_area.connect('key-press-event', self.on_key_press)
        self.drawing_area.connect('key-release-event', self.on_key_release)
        #a.connect('button-press-event', self.OnButtonPress)

        w.show_all()

        self.sim_host = "localhost"
        self.service_port = 4000
        self.service_client = Client(self.sim_host, self.service_port)
        self.service_client.connect('message', self.on_service_message)
        self.service_client.connect('connected', self.on_service_connect)
        
        self.motion_client = None
        self.range_client = None
        self.odometry_client = None
        
        self.throttle = 0
        self.steer = 0
        self.brake = 0
        
        self.speed_control = SpeedController()
        
        self.current_speed = 0
        self.dodging = False

    def send_service_message(self, identifier, component, message, data=[]):
        msg = '%s %s %s %s' % (identifier, component, message, json.dumps(data))
        self.service_client.send(msg)

    # the steering value is in radians.
    def send_motion_message(self):
        logging.info('Sending motion message!')
        if self.motion_client is not None:
            # the sign of the throttle is reversed!
            d = {'steer':self.steer, 'force':-self.throttle, 'brake':self.brake}
            line = json.dumps(d) + '\n'
            self.motion_client.send(line)
        else:
            print 'Cannot send motion message without connection to motion controller.'

    def on_service_connect(self, client):
        self.send_service_message('motion_port', 'simulation', 'get_stream_port', ['hummer.motion'])
        self.send_service_message('range_port', 'simulation', 'get_stream_port', ['hummer.scanner'])
        self.send_service_message('odometry_port', 'simulation', 'get_stream_port', ['hummer.odometry'])

    def on_service_message(self, client, line):
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
            self.motion_client = Client(self.sim_host, int(data))
            self.motion_client.connect("message", self.on_motion_message)

        elif identifier == 'range_port':
            self.range_client = Client(self.sim_host, int(data))
            self.range_client.connect("message", self.on_range_message)

        elif identifier == 'odometry_port':
            self.odometry_client = Client(self.sim_host, int(data))
            self.odometry_client.connect("message", self.on_odometry_message)

    def on_motion_message(self, client, line):
        try:
            obj = json.loads(line)
            print 'Motion:', obj
        except ValueError, e:
            warning('Invalid motion message:' + e)
        
    def on_range_message(self, client, line):
        try:
            obj = json.loads(line)
        except ValueError, e:
            error('Invalid range message:' + e)
            return
         
        ranges = obj['range_list']
        N = len(ranges)
        
        if min(ranges) < 0:
            warning('Range message was less than 0 (%d)' % (min(ranges)))

        min_left = min(ranges[0:int(N/3)])
        min_middle = min(ranges[int(N/3):int(2*N/3)])
        min_right = min(ranges[int(2*N/3):N])
        
        if min_middle < 4 or (min_left < 4 and min_right < 4):
            if self.speed_control.target_speed > 0:
                self.speed_control.stop(self)
        elif self.speed_control.target_speed > 0:
            if min_left < 4:
                self.dodging = True
                self.steer = pi/4
            elif min_right < 4:
                self.dodging = True
                self.steer = -pi/4
            elif self.dodging:
                self.dodging = False
                self.steer = 0

    def on_odometry_message(self, client, line):
        try:
            obj = json.loads(line)
            #print 'Odometry:', obj
            dS = obj['dS']
            dt = 0.1
            self.current_speed = dS/dt
            self.speed_control.update(self.current_speed, dt, self)
            self.send_motion_message()
            self.drawing_area.queue_draw()
                
        except ValueError, e:
            print 'Invalid odometry message:', e

    def on_stream_message(self, client, line):
        try:        
            obj = json.loads(line)
            print obj
        except ValueError, e:
            error("Stream message was not valid json" + e)
            return

    def draw_ranges(self):
        pass

    def draw_text_line(self, cr, line_number, text):
        cr.save()
        line_height = cr.font_extents()[2] + 2
        #cr.move_to(10, line_height)
        cr.translate(0, (line_number+1)*line_height)
        cr.show_text(text)
        cr.fill()
        cr.restore()
        
    # cr is the cairo context
    def on_draw(self, widget, cr):
        #print dir(cr)
        #x1, y1, x2, y2 = cr.clip_extents()
        #width = x2 - x1
        #height = y2 - y1
        #print 'Drawing area size:', width, height
 
        cr.set_source_rgb(1,1,1)
        cr.paint()
    
        cr.set_source_rgb(0,0,0)
        cr.set_font_size(16)
        
        self.draw_text_line(cr, 0, "Speed: %0.2f" % (self.current_speed))
        self.draw_text_line(cr, 1, "Steer: %0.2f Throttle: %0.2f Brake: %0.2f" % (self.steer, self.throttle, self.brake))
        self.draw_text_line(cr, 2, "Target Speed: %0.2f" % (self.speed_control.target_speed))
        #self.draw_text_line(cr, 3, "Disable forwards: %s Dodging: %s" % (self.disable_forwards, self.dodging))
        #cr.move_to(20, 20)
        #cr.show_text("Speed:" + str(self.last_speed))
        #cr.move_to(20, 30)
        
    def on_key_press(self, w, event):
        if event.string == 'q' or event.keyval == Gdk.KEY_Escape:
            Gtk.main_quit()

        elif event.keyval == Gdk.KEY_Left:
            #print 'Left pressed'
            if not self.dodging:
                self.steer = pi/4

        elif event.keyval == Gdk.KEY_Right:
            #print 'Right pressed'
            if not self.dodging:
                self.steer = -pi/4

        elif event.keyval == Gdk.KEY_Up:
            #print 'Up pressed'
            self.speed_control.adjust_speed(1.0, self)

        elif event.keyval == Gdk.KEY_Down:
            self.speed_control.adjust_speed(-1.0, self)

        elif event.keyval == Gdk.KEY_space:
            #print 'Space pressed'
            self.speed_control.stop(self)

    def on_key_release(self, w, event):
        if event.keyval == Gdk.KEY_Left:
            #print 'Left released'
            self.steer = 0

        elif event.keyval == Gdk.KEY_Right:
            #print 'Right released'
            self.steer = 0

        elif event.keyval == Gdk.KEY_Up:
            #print 'Up released'
            pass

        elif event.keyval == Gdk.KEY_Down:
            #print 'Down released'        
            pass

    def OnButtonPress(self, w, event):
        print 'Button press event'
        #print dir(event)
        print 'event type = %d, x = %d y = %d' % (event.type, event.x, event.y)

if __name__ == '__main__':
    
    logging.basicConfig(level=logging.WARNING)

    main_window = MainWindow()

    Gtk.main()
