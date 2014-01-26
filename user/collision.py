#!/usr/bin/env python

import sys
import json
import logging
from logging import warning, error, info
from math import pi, degrees

from PyQt4 import Qt, QtCore, QtGui

from connection import Connection

class PlotGroup:
    def __init__(self, color=Qt.Qt.black, symbol='cross'):
        self.color = color
        self.symbol = symbol
        self.data = []

class XYPlot(Qt.QWidget):
    def __init__(self):
        Qt.QWidget.__init__(self)
        
        # little dance to make the background white.
        p = self.palette()
        p.setColor(self.backgroundRole(), Qt.Qt.white)
        self.setPalette(p)
        self.setAutoFillBackground(True)

        # map scale
        self._scale = 1.0
        self._offset_x = 400
        self._offset_y = 300
        self.symbol_size = 1.0

        self.messages = []

        self.groups = []

    def translate(self, x, y):
        self._offset_x += x
        self._offset_y += y
        self.update()

    def scale(self, s):
        self._scale *= s
        self.update()    

    def drawArrow(self, qp, x, y, angle):
        qp.save()
        qp.translate(x, y)
        qp.rotate(angle)
        qp.drawPolygon(*arrow_points)
        qp.restore()

    def drawCross(self, qp, x, y):
        qp.save()
        qp.translate(x, y)
        qp.scale(self.symbol_size, self.symbol_size)
        qp.drawLine(-1, -1, 1, 1)
        qp.drawLine(-1, 1, 1, -1)
        qp.restore()

    def drawPlus(self, qp, x, y):
        qp.save()
        qp.translate(x, y)
        qp.scale(self.symbol_size, self.symbol_size)
        qp.drawLine(-1, 0, 1, 0)
        qp.drawLine(0, -1, 0, 1)
        qp.restore()

    def paintGrid(self, qp):
        pass

    def paintEvent(self, e):

        #print self.offset_x, self.offset_y, self.s

        qp = QtGui.QPainter()
        qp.begin(self)

        line_y = 20
        for line in self.messages:
            qp.drawText(20, line_y, line)
            line_y += 20

        qp.translate(self._offset_x, self._offset_y)           
        qp.scale(self._scale, -self._scale)

        #qp.translate(200, 200)

        qp.setBrush(Qt.Qt.black)
        qp.setPen(Qt.Qt.black)
        self.drawCross(qp, 0, 0)

        for group in self.groups:           
            if group.symbol == 'arrow':
                qp.setBrush(group.color)
                qp.setPen(Qt.Qt.NoPen)
                for v in group.data:
                    self.drawArrow(qp, v[0], v[1], v[2])
            elif group.symbol == 'cross':
                qp.setBrush(Qt.Qt.NoBrush)
                qp.setPen(group.color)
                for v in group.data:
                    self.drawCross(qp, v[0], v[1])
            elif group.symbol == 'plus':
                qp.setBrush(Qt.Qt.NoBrush)
                qp.setPen(group.color)
                for v in group.data:
                    self.drawPlus(qp, v[0], v[1])

        qp.end()

    def add_plot_group(self, g):
        self.groups.append(g)

    #def update(self):

class CollisionPlot(XYPlot):
    def __init__(self):
        XYPlot.__init__(self)

        self.blocked_path_group = PlotGroup(color=Qt.Qt.red, symbol='plus')
        self.add_plot_group(self.blocked_path_group)

        self.path_group = PlotGroup(color=Qt.Qt.green, symbol='plus')
        self.add_plot_group(self.path_group)

        self.obstacle_group = PlotGroup(color=Qt.Qt.blue, symbol='cross')
        self.add_plot_group(self.obstacle_group)

        self.symbol_size = 0.1
        self.scale(50)
    
    def on_msg(self, msg):
        try:
            #t = msg[u'state'][u'time']
            #current = (msg[u'state'][u'x'], msg[u'state'][u'y'], degrees(msg[u'state'][u'yaw']))
            #waypoints = msg[u'waypoint_control'][u'points']
            colmsg = msg[u'collision_control']
            enabled = colmsg[u'enabled']
            blocked = colmsg[u'blocked']
            path = colmsg[u'path']
            blocked_paths = colmsg[u'blocked_paths']
            obstacles = colmsg[u'obstacles']
            requested_steer = degrees(colmsg[u'requested_steer'])
            actual_steer = degrees(msg[u'controls'][u'steer'])
            reversing = msg[u'waypoint_control'][u'reversing']
        except KeyError:
            logging.error("Invalid message.")
        else:
            #print(msg)
            self.messages = []
            self.messages.append('Enabled %s Blocked %s Reversing %s' % (
                enabled, blocked, reversing))
            self.messages.append('Steer req. %0.2f act. %0.2f degrees' % (
                requested_steer, actual_steer))
            self.path_group.data = path
            self.blocked_path_group.data = blocked_paths
            self.obstacle_group.data = obstacles
            self.update()

class MainWindow(Qt.QWidget):
    def __init__(self):
        Qt.QWidget.__init__(self)

        self.grid = Qt.QGridLayout()
        self.setLayout(self.grid)
        
        self.plot = CollisionPlot()
        self.grid.addWidget(self.plot, 0, 0)

        self.connection = Connection('localhost', 60212, self.update)

    def update(self, msg):
        self.plot.on_msg(msg)        

    def keyPressEvent(self, e):
        if e.key() == Qt.Qt.Key_Escape:
            self.close()
        elif e.key() == Qt.Qt.Key_A:
            self.plot.scale(2)
        elif e.key() == Qt.Qt.Key_Z:
            self.plot.scale(0.5)
        elif e.key() == Qt.Qt.Key_Up:            
            self.plot.translate(0, 10)
        elif e.key() == Qt.Qt.Key_Down:
            self.plot.translate(0, -10)
        elif e.key() == Qt.Qt.Key_Left:
            self.plot.translate(10, 0)
        elif e.key() == Qt.Qt.Key_Right:
            self.plot.translate(-10, 0)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app = Qt.QApplication([])
    demo = MainWindow()
    demo.resize(800, 600)
    demo.show()
    sys.exit(app.exec_())

