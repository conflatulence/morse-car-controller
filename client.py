
import asynchat
import socket
from logging import error, info, warning

class Client(asynchat.async_chat):
    def __init__(self, socket=None, connect_fn=None, msg_fn=None, close_fn=None):
        asynchat.async_chat.__init__(self, socket)
        
        self.received_data = bytearray()
        self.set_terminator(b'\n')
        self.host = None
        self.port = None

        self.connect_fn = connect_fn
        self.msg_fn = msg_fn
        self.close_fn = close_fn

    def create_connection(self, host, port):
        self.host = host
        self.port = port
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.connect((self.host, self.port))
        except ConnectionRefusedError:
            error("Client failed to connect.")

    def handle_connect(self):
        if self.connect_fn is not None:
            self.connect_fn()
        else:
            info("Unhandled connect.")
    
    def collect_incoming_data(self, data):
        self.received_data.extend(data)

    def found_terminator(self):
        msg = self.received_data.decode()
        if self.msg_fn is not None:        
            self.msg_fn(msg)
        else:
            info("Unhandled message.")
        self.received_data.clear()

    def handle_close(self):
        self.close()
        if self.close_fn is not None:
            self.close_fn()
        else:
            info("Unhandled close.")

    def send_msg(self, msg):
        if not msg.endswith('\n'):
            msg += '\n'
        data = msg.encode()
        self.push(data)

