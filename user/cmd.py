#!/usr/bin/env python3

import sys
import os
import socket
import json



if __name__ == '__main__':
    if len(sys.argv) > 1:
        f = open(sys.argv[1], 'r')
    else:
        f = sys.stdin

    sock = socket.create_connection(("localhost", 60213))
    sockf = sock.makefile()    

    for line in f:
        line = line.strip()
        if line.startswith('#') or len(line) == 0:
            continue
        
        try:
            action, sep, rem = line.partition(' ')
            component, sep, rem = rem.partition(' ')
            field, sep, rem = rem.partition(' ')
            rem = rem.strip()

            if len(action) == 0 or len(component) == 0 or len(field) == 0:
                raise ValueError("Invalid command:"+line)

            if action == 'set':
                if len(rem) == 0:
                    raise ValueError("Set command must have an argument:"+line)
                if rem[0] in '[{': # it is a container argument.
                    args = json.loads(rem)
                else: # single value, not container.
                    args = json.loads('[' + rem + ']')[0]

            elif action == 'call':
                if len(rem) > 0:
                    args = json.loads(rem)
                else:
                    args = []
            elif action == 'get':
                raise ValueError("get command not supported yet.")
            else:
                raise ValueError("Invalid command type:" + line)
                
            msg = json.dumps([action, component, field, args]) + '\n'
            print('Sending: '+ msg.strip())
            sock.send(msg.encode())
            print('Received: ' + sockf.readline())
        except IndexError as err:
            print(err)
        except ValueError as err:
            print(err)
