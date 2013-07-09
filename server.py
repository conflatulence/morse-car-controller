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

        self.clients = []

    def handle_accepted(self, sock, addr):
        self.clients.append(Client(sock))
        
    def broadcast(self, msg):
        for client in self.clients:
            client.send_msg(msg)