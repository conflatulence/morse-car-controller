#!/usr/bin/env python

# based on Qwt-5.0.0/examples/data_plot
#!/usr/bin/env python

import sys
import json
import logging
import csv

from logging import error,warning, debug,info

from PyQt4 import Qt
import PyQt4.Qwt5 as Qwt
import PyQt4.Qwt5.anynumpy as np

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

class CsvLogger:
    def __init__(self, fname):
        self.writer = csv.writer(open(fname, 'w'))
        self.first = True

    def update(self, msg):
        if self.first:
            self.first = False
            self.cols = []
            for module in msg:
                for var in msg[module]:
                    self.cols.append(module + '.' + var)
            self.writer.writerow(self.cols)

        vals = []
        for name in self.cols:
            module, var = name.split('.')
            vals.append(msg[module][var])

        self.writer.writerow(vals)

class TimePlot:
    def __init__(self, name, lines):
        self.name = name
        self.widget = Qwt.QwtPlot()
        self.widget.setCanvasBackground(Qt.Qt.white)
        #self.widget.setTitle(self.name)
        self.widget.insertLegend(Qwt.QwtLegend(), Qwt.QwtPlot.BottomLegend);     
 
        self.lines = lines
        self.curves = {}
        self.data = {}

        grid = Qwt.QwtPlotGrid()
        grid.attach(self.widget)
        grid.setPen(Qt.QPen(Qt.Qt.black, 0, Qt.Qt.DotLine))

        self.t = np.zeros(0)
        
        for var, color in self.lines:
            self.data[var] = np.zeros(0)
            c = Qwt.QwtPlotCurve(var)
            c.setPen(Qt.QPen(color))
            c.attach(self.widget)
            self.curves[var] = c

        # in seconds, the amount of time on the x-axis.
        self.window = 120.0
        # the size of the shift (in seconds) when current time reaches the rhs of the graph.
        self.jump = 30.0
        # how close to the rhs before most recent sample must be before a shift occurs.
        self.jump_threshold = 0.1
        # how many samples to extend the arrays by when they run out of entries.
        self.extra_samples = 512
        
        self.first_update = True

    def reset(self):
        self.first_update = True
        self.n = 0

        self.t = np.zeros(0)
        for var in self.data:
            self.data[var] = np.zeros(0)
    
    def update_plot(self, new_t, new_vals):

        if self.first_update:            
            self.first_update = False
            self.n = 0            
            self.tmin = new_t
            self.tmax = self.tmin + self.window
            self.t = np.arange(self.tmin, self.tmax, 0.1)
            for var in self.data:
                self.data[var] = np.zeros(len(self.t))            
            self.widget.setAxisScale(Qwt.QwtPlot.xBottom, self.tmin, self.tmax)        

        self.t[self.n] = new_t

        for var, val in new_vals.iteritems():
            self.data[var][self.n] = val
            self.curves[var].setData(self.t[:self.n], self.data[var][:self.n])
            #self.curves[var].setData(self.t, self.data[var])

        if self.tmax - self.t[self.n] < self.jump_threshold:
            self.tmin += self.jump
            self.tmax += self.jump             
            self.widget.setAxisScale(Qwt.QwtPlot.xBottom, self.tmin, self.tmax)
            # drop old data the will not be displayed.
            # find the index of the largest value in self.t that is less than tmin.
            cut_index = len(np.nonzero(self.t[:self.n] < self.tmin)[0])
            debug("tmin=%f tmax=%f cut=%d n=%d -> %d array_lenth=%d" % (
                self.tmin, self.tmax, cut_index, self.n, self.n - cut_index, len(self.t)))

            self.t = self.t[cut_index:]
            for var in self.data:
                self.data[var] = self.data[var][cut_index:]
            self.n -= cut_index
            assert(self.t[self.n] == new_t)
        
        self.n += 1

        if self.n >= len(self.t):
            debug("Extending arrays by %d samples" % (self.extra_samples))
            self.t = np.concatenate((self.t, np.zeros(self.extra_samples)))
            for var in self.data:
                self.data[var] = np.concatenate((self.data[var], np.zeros(self.extra_samples)))

        #self.widget.setAxisScale(Qwt.QwtPlot.xBottom, t[-1]-10, t[-1])        
        self.widget.replot()

class TestPlot(TimePlot):
    def __init__(self):
        lines = (('x', Qt.Qt.red),('y', Qt.Qt.blue))
        TimePlot.__init__(self, 'Test', lines)
    
    def update(self, msg):
        v = {}
        try:
            t = msg['t']
            v['x'] = msg['x']
            v['y'] = msg['y']
        except KeyError as err:
            error("Invalid message", str(err))
        else:
            self.update_plot(t, v)

class OrientationPlot(TimePlot):
    def __init__(self):
        lines = (('roll', Qt.Qt.red), ('pitch', Qt.Qt.green), ('yaw',Qt.Qt.blue))
        TimePlot.__init__(self, 'Orientation', lines)

    def update(self, msg):
        v = {}
        try:
            t = msg[u'state'][u'time']
            v['roll'] = msg[u'state'][u'roll']
            v['pitch'] = msg[u'state'][u'pitch']
            v['yaw'] = msg[u'state'][u'yaw']
        except KeyError as err:
            error("Invalid message %s", err)
        else:
            self.update_plot(t, v)       

class ThrottlePlot(TimePlot):
    def __init__(self):
        lines = (('throttle', Qt.Qt.red),('brake', Qt.Qt.blue))
        TimePlot.__init__(self, 'Throttle', lines)

    def update(self, msg):
        v = {}
        try:
            t = msg[u'state'][u'time']
            v['throttle'] = msg[u'controls'][u'throttle']
            v['brake'] = msg[u'controls'][u'brake']
        except KeyError as err:
            error("Invalid message %s", err)
        else:
            self.update_plot(t, v)

class SpeedPlot(TimePlot):
    def __init__(self):
        lines = (
                 ('speed', Qt.Qt.red),
                 ('target_speed', Qt.Qt.green),
                 ('error', Qt.Qt.blue)
                 #('integral', Qt.Qt.magenta)
                 )
        TimePlot.__init__(self, 'Speed', lines)
    
    def update(self, msg):
        v = {}
        try:
            t = msg[u'state'][u'time']
            v['speed'] = msg[u'state'][u'speed']
            v['target_speed'] = msg[u'speed_control'][u'target']
            #v['integral'] = msg[u'speed_control'][u'integral']
            v['error'] = msg[u'speed_control'][u'error']
        except KeyError as err:
            error("Invalid message %s", err)
        else:
            self.update_plot(t, v)

class SteerPlot(TimePlot):
    def __init__(self):
        lines = (
                 ('steer', Qt.Qt.red),
                 ('heading', Qt.Qt.blue),
                 ('target_heading', Qt.Qt.green),
                 ('steer_error', Qt.Qt.magenta)
                 )
        TimePlot.__init__(self, 'Steering', lines)

    def update(self, msg):
        v = {}
        try:
            t = msg[u'state'][u'time']
            v['steer'] = msg[u'controls'][u'steer']
            v['heading'] = msg[u'state'][u'yaw']
            v['target_heading'] = msg[u'collision_control'][u'target_heading']
            v['steer_error'] = msg[u'collision_control'][u'steer_error']
        except KeyError as err:
            error("Invalid message %s", err)                
        else:
            self.update_plot(t, v)

class CollisionPlot(TimePlot):
    def __init__(self):
        lines = (('blocked', Qt.Qt.red), ('dodging', Qt.Qt.blue), ('auto_steer', Qt.Qt.green))
        TimePlot.__init__(self, 'Collision', lines)

    def update(self, msg):
        v = {}
        try:
            t = msg[u'state'][u'time']
            v['blocked'] = msg[u'collision_control'][u'blocked']
            v['dodging'] = msg[u'collision_control'][u'dodging']
            v['auto_steer'] = msg[u'collision_control'][u'auto_steer']
        except KeyError as err:
            error("Invalid message %s", err)                
        else:
            self.update_plot(t,v)


class MainWindow(Qt.QWidget):
    def __init__(self):
        Qt.QWidget.__init__(self)
        
        self.grid = Qt.QGridLayout()
        self.setLayout(self.grid)
        self.plots = []

        if False:
            self.add_plot(TestPlot(), 0, 0)
        else:
            self.add_plot(ThrottlePlot(), 0, 0)
            self.add_plot(SpeedPlot(), 1, 0)
            self.add_plot(OrientationPlot(), 2, 0)
            self.add_plot(SteerPlot(), 3, 0)
            self.add_plot(CollisionPlot(), 4, 0)

        self.paused = False

        #self.csv = CsvLogger('log.csv')
        self.msglog = open('msglog.txt', 'w')
    
        self.connection = Connection('localhost', 60212, self.update)

    def add_plot(self, p, row, col):
        self.plots.append(p)
        self.grid.addWidget(p.widget, row, col)

    def update(self, msg):
        #print msg,
        print >>self.msglog, msg
        if self.paused:
            # just discard the messages ... do something smarter in the future?
            return
        
        for plot in self.plots:
            plot.update(msg)
        #self.csv.update(msg)

    def clear(self):
        for p in self.plots:
            p.reset()

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
    demo.resize(800, 600)
    demo.show()
    sys.exit(app.exec_())

