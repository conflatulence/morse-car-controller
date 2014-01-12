#!/usr/bin/env python3

import socket
import json

components = [
'motion',
'gps',
#'hummer.pose',
'scanner',
'odometry',
'compass'
]

if __name__ == '__main__':
    sock = socket.create_connection(("localhost", 4000))
    sockf = sock.makefile()

    for comp in components:
        msg = '%s simulation get_stream_port ["robot.%s"]\n' % (comp, comp)
        sock.send(msg.encode())
        print(sockf.readline().strip())

