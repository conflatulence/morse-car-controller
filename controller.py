#!/usr/bin/env python

from gi.repository import Gtk
from gi.repository import Gdk

#import cairo
from math import pi, cos, sin
import json
import re

from client import Client
        
class MainWindow:
    def __init__(self):
        w = Gtk.Window()
        w.set_default_size(200, 200)
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
        
        self.accel = 0
        self.steer = 0
        self.brake = 0
        
        self.disable_forwards = False
        self.dodging = False

    def send_service_message(self, identifier, component, message, data=[]):
        msg = '%s %s %s %s' % (identifier, component, message, json.dumps(data))
        self.service_client.send(msg)

    # the steering value is in radians.
    def send_motion_message(self):
        if self.motion_client is not None:
            d = {'steer':self.steer, 'force':self.accel, 'brake':self.brake}
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
            print 'Invalid service message:', line
            return
        
        if m.group('success') != 'SUCCESS':
            print 'Service command failed:', line
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
            print 'Invalid motion message:', e

#     # function not tested, probably wrong.
#     def range_to_xy(self, r, n):
#         a = self.range_angles[n]
#         x = r*sin(a)
#         y = r*cos(a)
#         return (x,y)

    def on_range_message(self, client, line):
        try:
            obj = json.loads(line)
            ranges = obj['range_list']
            N = len(ranges)
            #if self.range_angles is None:
            #    self.range_angles = [-pi/2 + (pi/2)*a/(len(ranges)-1) for a in range(N)]
                
            print ranges
            
            for r in ranges[int(N/3):int(2*N/3)]:
                if r < 4:
                    if not self.disable_forwards:
                        self.disable_forwards = True
                        self.accel = 0
                        self.brake = 2
                        self.send_motion_message()
                    break
            else:
                self.disable_forwards = False
                
            for r in ranges[0:int(N/3)]:
                if r < 4 and self.accel < 0:
                    self.dodging = True
                    self.steer = pi/4
                    self.send_motion_message()
                    break
            else:
                if self.dodging is True:
                    self.dodging = False
                    self.steer = 0
                    self.send_motion_message()
                
            for r in ranges[int(2*N/3):N]:
                if r < 4 and self.accel < 0:
                    self.dodging = True
                    self.steer = -pi/4
                    self.send_motion_message()
                    break
            else:
                if self.dodging is True:
                    self.dodging = False
                    self.steer = 0
                    self.send_motion_message()

        except ValueError, e:
            print 'Invalid range message:', e

    def on_odometry_message(self, client, line):
        try:
            obj = json.loads(line)
            #print 'Odometry:', obj
        except ValueError, e:
            print 'Invalid odometry message:', e

    def on_stream_message(self, client, line):
        try:        
            obj = json.loads(line)
            print obj
        except ValueError, e:
            print "Stream message was not valid json", e
            return

    def draw_ranges(self):
        pass

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
        cr.move_to(20, 20)
        cr.set_font_size(20)
        #cr.show_text("Recieved:" + str(self.last_data))
        cr.fill()            

    def on_key_press(self, w, event):
        if event.string == 'q' or event.keyval == Gdk.KEY_Escape:
            Gtk.main_quit()

        elif event.keyval == Gdk.KEY_Left:
            #print 'Left pressed'
            if not self.dodging:
                self.steer = pi/4
                self.send_motion_message()

        elif event.keyval == Gdk.KEY_Right:
            #print 'Right pressed'
            if not self.dodging:
                self.steer = -pi/4
                self.send_motion_message()

        elif event.keyval == Gdk.KEY_Up:
            #print 'Up pressed'
            if self.disable_forwards:
                self.brake = 2
                self.accel = 0
            else:
                self.brake = 0
                self.accel -= 1
            self.send_motion_message()

        elif event.keyval == Gdk.KEY_Down:
            #print 'Down pressed'
            self.brake = 0
            self.accel += 1
            self.send_motion_message()

        elif event.keyval == Gdk.KEY_space:
            #print 'Space pressed'
            self.accel = 0
            self.brake = 2
            self.send_motion_message()

    def on_key_release(self, w, event):
        if event.keyval == Gdk.KEY_Left:
            #print 'Left released'
            self.steer = 0
            self.send_motion_message()

        elif event.keyval == Gdk.KEY_Right:
            #print 'Right released'
            self.steer = 0
            self.send_motion_message()

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

    main_window = MainWindow()

    Gtk.main()
