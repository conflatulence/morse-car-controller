#!/usr/bin/env python3

import sys
import socket
import json
import re
import logging
from logging import warning, error, info
from math import radians

components = ['robot.motion','robot.gps','robot.pose','robot.scanner','robot.odometry']

if __name__ == '__main__':

    steer = radians(float(sys.argv[1]))
    force = float(sys.argv[2])
    brake = float(sys.argv[3])

    sock = socket.create_connection(("localhost", 4000))
    sockf = sock.makefile()

    msg = '%s simulation get_stream_port %s\n' % ('CMD1', json.dumps(['robot.motion']))
    sock.send(msg.encode())
    line = sockf.readline()

    m = re.match('^(?P<id>\w+) (?P<success>\w+) (?P<data>.*)$', line)
    if m is None:
        sys.exit(1)

    identifier = m.group('id')
    data = m.group('data')

    print(line.strip())

    comp_port = int(data)

    comp_sock = socket.create_connection(("localhost", comp_port))
    comp_sock.send((json.dumps({"steer":steer,"force":-force,"brake":brake}) + '\n').encode())

