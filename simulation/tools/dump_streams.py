#!/usr/bin/env python3

import socket
import json
import re
import select
import logging
from logging import warning, error, info

components = [
'robot.motion',
'robot.gps',
#'robot.pose',
'robot.scanner',
'robot.odometry',
'robot.compass'
]

if __name__ == '__main__':
    sock = socket.create_connection(("localhost", 4000))
    sockf = sock.makefile()

    streams = {}
    out_files = {}

    for comp in components:
        msg = '%s simulation get_stream_port %s\n' % (comp, json.dumps([comp]))
        sock.send(msg.encode())
        line = sockf.readline().strip()
        print(line)
        m = re.match('^(?P<id>\S+) (?P<success>\S+) (?P<data>.*)$', line)
        if m is None:
            warning('Invalid service message:' + line)
        elif m.group('success') != 'SUCCESS':
            warning('Service command failed:' + line)
        else:
            identifier = m.group('id')
            data = m.group('data')

            assert(identifier == comp)

            stream_sockf = socket.create_connection(("localhost", int(data))).makefile()
            fileno = stream_sockf.fileno()
            streams[fileno] = stream_sockf
            out_files[fileno] = open('%s.txt' % (comp), 'w')

    rlist = list(streams.values())

    while True:
        rready, wready, xready = select.select(rlist, [], [])
        for rsockf in rready:
            line = rsockf.readline().strip()
            fileno = rsockf.fileno()
            print(line, file=out_files[fileno])

