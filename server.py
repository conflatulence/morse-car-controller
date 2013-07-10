import asyncore
import socket
from logging import error, info, warning

from client import Client

class Server(asyncore.dispatcher):

    def __init__(self, port, host="localhost"):
        asyncore.dispatcher.__init__(self)
        self.create_socket()
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(5)

        self.connect_fn = None
        self.msg_fn = None
        self.close_fn = None

        self.clients = []

    def handle_accepted(self, sock, addr):
        new_client = Client(sock)
        new_client.msg_fn = self.msg_fn
        new_client.close_fn = self.close_fn
        
        self.clients.append(new_client)

        if self.connect_fn is not None:
            self.connect_fn()
        
    def broadcast(self, msg):
        for client in self.clients:
            client.send_msg(msg)
