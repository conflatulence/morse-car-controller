#!/usr/bin/env python

import sys
import json
import logging
from logging import warning, error, info
from math import pi, degrees

from PyQt4 import Qt, QtCore, QtGui

from connection import Connection

arrow_points = (
    Qt.QPoint(-1, -4),
    Qt.QPoint(1, -4),
    Qt.QPoint(1, 4),
    Qt.QPoint(4, 4),
    Qt.QPoint(0, 12),
    Qt.QPoint(-4, 4),
    Qt.QPoint(-1, 4)
    )

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
        self.s = 1.0
        self.offset_x = 400
        self.offset_y = 300

        self.groups = []


    def translate(self, x, y):
        self.offset_x += x
        self.offset_y += y
        self.update()

    def scale(self, s):
        self.s *= s
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
        qp.drawLine(-2, -2, 2, 2)
        qp.drawLine(-2, 2, 2, -2)
        qp.restore()

    def paintGrid(self, qp):
        pass

    def paintEvent(self, e):

        #print self.offset_x, self.offset_y, self.s

        qp = QtGui.QPainter()
        qp.begin(self)

        qp.translate(self.offset_x, self.offset_y)           
        qp.scale(self.s, -self.s)

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
        qp.end()

    def add_plot_group(self, g):
        self.groups.append(g)

    #def update(self):

class MapPlot(XYPlot):
    def __init__(self):
        XYPlot.__init__(self)

        self.current_pos = PlotGroup(color=Qt.Qt.blue, symbol='arrow')
        self.add_plot_group(self.current_pos)

        self.waypoint_group = PlotGroup(color=Qt.Qt.black, symbol='cross')
        self.add_plot_group(self.waypoint_group)
    
    def on_msg(self, msg):
        try:
            #t = msg[u'state'][u'time']
            current = (msg[u'state'][u'x'], msg[u'state'][u'y'], degrees(msg[u'state'][u'yaw']))
            waypoints = msg[u'waypoint_control'][u'points']
        except KeyError:
            logging.error("Invalid message.")
        else:
            self.current_pos.data = [current]
            self.waypoint_group.data = waypoints
            self.update()

class MainWindow(Qt.QWidget):
    def __init__(self):
        Qt.QWidget.__init__(self)

        self.grid = Qt.QGridLayout()
        self.setLayout(self.grid)
        
        self.plot = MapPlot()
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

