#!/usr/bin/env python

import sys
import json
import logging
import csv

from logging import error,warning, debug,info

from PyQt4 import Qt

from connection import Connection

class MainWindow(Qt.QWidget):
    def __init__(self, input_fname):
        Qt.QWidget.__init__(self)

        self.msgs = open(input_fname, 'r').readlines()
        self.next_msg_index = 0
     
        self.paused = True

        self.timer = Qt.QTimer()
        #self.timer.start(1000);
        self.timer.timeout.connect(self.timeout)

        self.server = Qt.QTcpServer()
        self.server.newConnection.connect(self.client_connect)
        self.server.listen(port=60212)

        self.clients = []

    def client_connect(self):
        while self.server.hasPendingConnections():
            print("Client connect")
            client = self.server.nextPendingConnection()
            client.disconnected.connect(self.client_disconnect)
            self.clients.append(client)

    def client_disconnect(self):
        self.clients = [c for c in self.clients
                        if c.state() != Qt.QAbstractSocket.UnconnectedState]
        print('Client disconnect, remaining clients = %d' % len(self.clients))

    def send_next_msg(self):
        try:
            msg = self.msgs[self.next_msg_index]
        except IndexError as e:
            print >>sys.stderr, "No more messages to send."
            return
        
        if len(msg) == 0:
            print >>sys.stderr, "Empty message line in replay, skipping..."
            return

        print(msg)

        for client in self.clients:
            try:
                client.write(msg)
            except Exception as e:
                print(e)
        
        self.next_msg_index += 1

    def send_prev_msg(self):
        self.next_msg_index = max(self.next_msg_index-2, 0)
        self.send_next_msg()

    def timeout(self):
        self.send_next_msg()

    def keyPressEvent(self, e):
        if e.key() == Qt.Qt.Key_Escape:
            self.close()
        elif e.key() == Qt.Qt.Key_P:
            if self.paused:
                self.paused = False
                self.timer.start()
            else:
                self.paused = True
                self.timer.stop()

        elif e.key() == Qt.Qt.Key_Space and self.paused:
            self.send_next_msg()
        elif e.key() == Qt.Qt.Key_B and self.paused:
            self.send_prev_msg()
        elif e.key() == Qt.Qt.Key_R:
            self.next_msg_index = 0 

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app = Qt.QApplication([])
    main_window = MainWindow(sys.argv[1])
    main_window.resize(200, 200)
    main_window.show()
    sys.exit(app.exec_())

