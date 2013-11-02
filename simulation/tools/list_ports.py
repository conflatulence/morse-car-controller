#!/usr/bin/env python3

import socket
import json

components = [
'hummer.motion',
'hummer.gps',
#'hummer.pose',
'hummer.scanner',
'hummer.odometry',
'hummer.compass'
]

if __name__ == '__main__':
    sock = socket.create_connection(("localhost", 4000))
    sockf = sock.makefile()

    for comp in components:
        msg = '%s simulation get_stream_port %s\n' % (comp, json.dumps([comp]))
        sock.send(msg.encode())
        print(sockf.readline().strip())

