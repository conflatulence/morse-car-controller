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
        self._scale = 1.0
        self.symbol_size = 5.0
        self._symbol_scale = self.symbol_size/self._scale 
        self._offset_x = 400
        self._offset_y = 300
        
        self.messages = []

        self.groups = []

    def translate(self, x, y):
        self._offset_x += x
        self._offset_y += y
        self.update()

    def scale(self, s):
        self._scale *= s
        self._symbol_scale = self.symbol_size/self._scale
        self.update()    

    def drawArrow(self, qp, x, y, angle):
        qp.save()
        qp.translate(x, y)
        qp.rotate(angle)
        qp.scale(self._symbol_scale*0.5, self._symbol_scale*0.5)
        qp.drawPolygon(*arrow_points)
        qp.restore()

    def drawCross(self, qp, x, y):
        qp.save()
        qp.translate(x, y)
        qp.scale(self._symbol_scale, self._symbol_scale)
        qp.drawLine(-1, -1, 1, 1)
        qp.drawLine(-1, 1, 1, -1)
        qp.restore()

    def drawPlus(self, qp, x, y):
        qp.save()
        qp.translate(x, y)
        qp.scale(self._symbol_scale, self._symbol_scale)
        qp.drawLine(-1, 0, 1, 0)
        qp.drawLine(0, -1, 0, 1)
        qp.restore()

    def drawModel(self, qp, x, y, angle, steer):
        
        # all the units are x10 because there is some rounding(?)
        # issue where lines don't joint correctly when using
        # the meter units directly.
        # there is a scale(0.1,0.1) further down to put things
        # back to the correct size.

        Lf = 16 # length of chass from middle to front axle
        Lb = 23 # length of chassis from middle to back axle
        Wa = 13 # half axle length
        Lw = 10 # wheel length

        qp.save()
        
        qp.translate(x,y)
        qp.rotate(angle)
        #qp.scale(self._symbol_scale, self._symbol_scale)
        qp.scale(0.1, 0.1)
        qp.drawLine(0, -Lb, 0, Lf) # main body
        
        qp.save() # begin rear end
        qp.translate(0.0, -Lb)
        qp.drawLine(-Wa, 0.0, Wa, 0.0) # rear axle
        qp.drawLine(-Wa,-Lw, -Wa, Lw) #left wheel
        qp.drawLine(Wa, -Lw, Wa, Lw) # right wheel
        qp.restore()
        
        qp.translate(0.0, Lf) # begin front end
        qp.drawLine(-Wa, 0.0, Wa, 0.0) # front axle
        
        qp.save() # begin left wheel
        qp.translate(-Wa, 0.0)
        qp.rotate(-steer)
        qp.drawLine(0.0, -Lw, 0.0, Lw)
        qp.restore()
        
        qp.save() # begine right wheel
        qp.translate(Wa, 0.0)
        qp.rotate(-steer)
        qp.drawLine(0.0, -Lw, 0.0, Lw)
        qp.restore()
        
        qp.restore()

    def paintGrid(self, qp):
        pass

    def paintEvent(self, e):

        #print self.offset_x, self.offset_y, self.s

        qp = QtGui.QPainter()
        qp.begin(self)
        qp.setRenderHint(QtGui.QPainter.Antialiasing, True)

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
            elif group.symbol == 'model':
                pen = Qt.QPen()
                pen.setWidth(self._symbol_scale)
                pen.setColor(group.color)
                qp.setBrush(group.color)
                qp.setPen(pen)

                for v in group.data:
                    #print("Draw model %0.2f %0.2f %0.2f %0.2f" % (v[0:4]))
                    self.drawModel(qp, v[0], v[1], v[2], v[3])

        qp.end()

    def add_plot_group(self, g):
        self.groups.append(g)

    #def update(self):

class MapPlot(XYPlot):
    def __init__(self):
        XYPlot.__init__(self)

        self.current_pos = PlotGroup(color=Qt.Qt.blue, symbol='model')
        self.add_plot_group(self.current_pos)

        self.waypoint_group = PlotGroup(color=Qt.Qt.black, symbol='cross')
        self.add_plot_group(self.waypoint_group)

        self.scale(12)
    
    def on_msg(self, msg):
        try:
            #t = msg[u'state'][u'time']
            current = (msg[u'state'][u'x'],
                       msg[u'state'][u'y'],
                       degrees(msg[u'state'][u'yaw']),
                       degrees(msg[u'controls'][u'steer']))
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

