import asyncore
import socket
from logging import error, info, warning

from client import Client

class Server(asyncore.dispatcher):

    def __init__(self, port, connect_fn=None, msg_fn=None, close_fn=None):
        asyncore.dispatcher.__init__(self)
        self.create_socket()
        self.set_reuse_addr()
        self.bind(('localhost', port))
        self.listen(5)

        self.client_connect_fn = connect_fn
        self.client_msg_fn = msg_fn
        self.client_close_fn = close_fn

        self.clients = []

    def handle_accepted(self, sock, addr):
        client = Client(sock)
        client.msg_fn = self.client_msg_fn
        client.close_fn = self.client_close
        
        self.clients.append(client)

        if self.client_connect_fn:
            self.client_connect_fn(client)

    def client_close(self, client):
        self.clients.remove(client)

        if self.client_close_fn:
            self.client_close_fn(client)
        
    def broadcast(self, msg):
        for client in self.clients:
            client.send_msg(msg)
