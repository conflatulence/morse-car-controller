#!/usr/bin/env python3

import sys
import os
import socket
import json

def set_type(s):

    s = s.strip()
    if len(s) == 0:
        return []

    try:
        v = float(s)
        return v
    except ValueError:
        pass
    
    if s.lower() == 'true':
        return True
    elif s.lower() == 'false':
        return False
    
    return s

def argparse(s):
    if '=' in s:
        d = {}
        for p in s.split(','):
            name, sep, val = p.partition('=')
            name = name.strip()
            val = val.strip()
            if len(name) == 0 or sep != '=' or len(val) == 0:
                raise ValueError('Invalid named arg string.')
            d[name] = set_type(val)
        return d
    elif ',' in s:
        return [set_type(v) for v in s.split(',')]
    else:
        return set_type(s)

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

            if len(action) == 0 or len(component) == 0 or len(field) == 0:
                raise ValueError("Invalid command:"+line)

            args = argparse(rem)
            msg = json.dumps([action, component, field, args]) + '\n'
            print('Sending: '+ msg.strip())
            sock.send(msg.encode())
            print('Received: ' + sockf.readline())
        except IndexError as err:
            print(err)
        except ValueError as err:
            print(err)
