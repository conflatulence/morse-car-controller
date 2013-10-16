#!/usr/bin/env python

import sys
import json
import logging
import csv
from math import degrees

from logging import error,warning, debug,info

from PyQt4 import Qt

class Connection:
    def __init__(self, host, port, update_fn):
        self.host = host
        self.port = port
        self.update_fn = update_fn

        self.sock = Qt.QTcpSocket()
        self.sock.connected.connect(self.connected)
        self.sock.disconnected.connect(self.disconnected)
        self.sock.error.connect(self.socket_error)
        self.sock.readyRead.connect(self.data_ready)
        self.retry_delay_ms = 2000
        self.connect()

    def connect(self):
        info("Attempting to connect.")
        self.sock.connectToHost(self.host, self.port)

    def connected(self):
        info('Connected to host!')

    def disconnected(self):
        info("Disconnected from host!")
        Qt.QTimer.singleShot(self.retry_delay_ms, self.connect)

    def socket_error(self):
        warning("Socket error")
        Qt.QTimer.singleShot(self.retry_delay_ms, self.connect)

    def data_ready(self):
        if self.sock.canReadLine():
            line = str(self.sock.readLine())
            
            try:
                obj = json.loads(line)
            except ValueError as err:
                warning("Received invalid json: %s" % str(err))
                return

            self.update_fn(obj)



class Display(Qt.QWidget):
    def __init__(self, name):
        Qt.QWidget.__init__(self)
        self.name = name
        
        vbox = Qt.QVBoxLayout()
        self.setLayout(vbox)
        
        p = self.palette()
        p.setColor(self.backgroundRole(), Qt.Qt.white)
        self.setPalette(p)
        self.setAutoFillBackground(True)
        
        self.name_label = Qt.QLabel(text=name)
        self.data_label = Qt.QLabel(text="--")
        
        self.name_label.setSizePolicy(Qt.QSizePolicy(Qt.QSizePolicy.Minimum, Qt.QSizePolicy.Minimum))
        self.data_label.setSizePolicy(Qt.QSizePolicy(Qt.QSizePolicy.Minimum, Qt.QSizePolicy.Minimum))
        self.setSizePolicy(Qt.QSizePolicy(Qt.QSizePolicy.Minimum, Qt.QSizePolicy.Minimum))
        
        font = self.font()
        
        font.setPointSize(12)
        self.name_label.setFont(font)
        
        font.setPointSize(20)
        self.data_label.setFont(font)
        
        vbox.addWidget(self.name_label)
        vbox.addWidget(self.data_label)

    def update_display(self, new_str):
        self.data_label.setText(new_str)

class OrientationDisplay(Display):
    def __init__(self):
        Display.__init__(self, 'State Roll/Pitch/Yaw (degrees)')

    def update_msg(self, msg):
        try:
            roll = msg[u'state'][u'roll']
            pitch = msg[u'state'][u'pitch']
            yaw = msg[u'state'][u'yaw']
        except KeyError as err:
            error("Invalid message %s", err)
        else:
            self.update_display("%6.2f %6.2f %6.2f" % (degrees(roll), degrees(pitch), degrees(yaw)))     

class PositionDisplay(Display):
    def __init__(self):
        Display.__init__(self, 'State X/Y/Z')

    def update_msg(self, msg):
        try:
            x = msg[u'state'][u'x']
            y = msg[u'state'][u'y']
            z = msg[u'state'][u'z']
        except KeyError as err:
            error("Invalid message %s", err)
        else:
            self.update_display("%6.2f %6.2f %6.2f" % (x, y, z))

class ControlsDisplay(Display):
    def __init__(self):
        Display.__init__(self, 'Controls Throttle/Brake/Steering (Steering in degrees)')

    def update_msg(self, msg):
        try:
            throttle = msg[u'controls'][u'throttle']
            brake = msg[u'controls'][u'brake']
            steer = msg[u'controls'][u'steer']
        except KeyError as err:
            error("Invalid message %s", err)
        else:
            self.update_display("%6.2f %6.2f %6.2f" % (throttle, brake, degrees(steer)))

class SpeedControlDisplay(Display):
    def __init__(self):
        Display.__init__(self, 'Speed Control Target/Error/Integral')

    def update_msg(self, msg):
        try:
            target = msg[u'speed_control'][u'target']
            error = msg[u'speed_control'][u'error']
            integral = msg[u'speed_control'][u'integral']
        except KeyError as err:
            error("Invalid message %s", err)
        else:
            self.update_display("%6.2f %6.2f %6.2f" % (target, error, integral))

class CollisionControlDisplay(Display):
    def __init__(self):
        Display.__init__(self, 'Collision Control Blocked/Dodging/Enabled')

    def update_msg(self, msg):
        try:
            blocked = msg[u'collision_control'][u'blocked']
            dodging = msg[u'collision_control'][u'dodging']
            enabled = msg[u'collision_control'][u'enabled']
        except KeyError as err:
            error("Invalid message %s", err)
        else:
            self.update_display("%s %s %s" % (blocked, dodging, enabled))

class SteeringControlDisplay(Display):
    def __init__(self):
        Display.__init__(self, 'Steering Control TargetHeading/HeadingError')

    def update_msg(self, msg):
        try:
            target_heading = msg[u'steering_control'][u'target_heading']
            steer_error = msg[u'steering_control'][u'heading_error']
        except KeyError as err:
            error("Invalid message %s", err)
        else:
            self.update_display("%6.2f %6.2f" % (degrees(target_heading), degrees(steer_error)))

class WaypointDisplay(Display):
    def __init__(self):
        Display.__init__(self, 'Waypoint Control Distance/Direction')

    def update_msg(self, msg):
        try:
            distance = msg[u'waypoint_control'][u'distance']
            direction = msg[u'waypoint_control'][u'direction']
        except KeyError as err:
            error("Invalid message %s", err)
        else:
            self.update_display("%6.2f %6.2f" % (distance, degrees(direction)))

class MainWindow(Qt.QWidget):
    def __init__(self):
        Qt.QWidget.__init__(self)
        
        self.grid = Qt.QGridLayout()
        self.setLayout(self.grid)
        self.displays = []

        self.add_display(OrientationDisplay(), 0, 0)
        self.add_display(PositionDisplay(), 1, 0)
        self.add_display(ControlsDisplay(), 2, 0)
        self.add_display(SpeedControlDisplay(), 3, 0)
        self.add_display(CollisionControlDisplay(), 4, 0)
        self.add_display(SteeringControlDisplay(), 5, 0)
        self.add_display(WaypointDisplay(), 6, 0)

        self.paused = False

        self.msglog = open('msglog.txt', 'w')
    
        self.connection = Connection('localhost', 60212, self.update)

    def add_display(self, p, row, col):
        self.displays.append(p)
        self.grid.addWidget(p, row, col)

    def update(self, msg):
        print >>self.msglog, msg
        if self.paused:
            return
        
        for display in self.displays:
            display.update_msg(msg)

    def keyPressEvent(self, e):
        if e.key() == Qt.Qt.Key_Escape:
            self.close()
        elif e.key() == Qt.Qt.Key_P:
            if self.paused:
                self.paused = False
            else:
                self.paused = True
        elif e.key() == Qt.Qt.Key_C:
            self.clear()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app = Qt.QApplication([])
    demo = MainWindow()
    #demo.resize(800, 600)
    demo.show()
    sys.exit(app.exec_())
