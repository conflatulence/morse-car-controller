
from gi.repository import GLib
from gi.repository import Gio
from gi.repository import GObject

from logging import error, warning, info

class Client(GObject.GObject):

    # as explained in https://developer.gnome.org/pygobject/stable/class-gobject.html#method-gobject--connect
    # the handler must take an object (in this case Client)
    # as the first arg, so to handle the message signal the handler should be
    # def handler(client, line) or
    # def handler(self, client, line) if the handler is an object method.

    __gsignals__ = {
        'message':(GObject.SIGNAL_RUN_FIRST, None, (str,)),
        'connected':(GObject.SIGNAL_RUN_FIRST, None, ()),
        'disconnected':(GObject.SIGNAL_RUN_FIRST, None, ())
    }

#    def do_message(self, line):
#        print 'Message signal:', line.strip()

    def do_connected(self):
        info("Client connected")

    def do_disconnected(self):
        info("Client disconnected")

    def __init__(self, host, port):
        GObject.GObject.__init__(self)
        self.host = host
        self.port = port
        self.connected = False
        self.reconnect_period = 5
        self.socket_client = Gio.SocketClient()
        self.attempt_connection()
        self.auto_reconnect = True

    def connection_ready(self, source, result, arg):
        try:
            self.connection = self.socket_client.connect_to_host_finish(result)
        except GLib.GError, e:
            error('Problem connecting to host:' + e.message)
            if self.auto_reconnect:
                GLib.timeout_add_seconds(self.reconnect_period, self.reconnect_timeout)
            return

        self.connected = True
        self.channel = GLib.IOChannel(self.connection.get_socket().get_fd())
        conditions = GLib.IOCondition.IN | GLib.IOCondition.ERR | GLib.IOCondition.HUP | GLib.IOCondition.NVAL
        self.channel.add_watch(conditions, self.data_ready, None)
        self.emit("connected")

    def attempt_connection(self):
        cancellable = Gio.Cancellable()
        self.connection = self.socket_client.connect_to_host_async(
            self.host, self.port, cancellable, self.connection_ready, None)

    def reconnect_timeout(self):
        self.attempt_connection()
        return False

    def handle_disconnect(self):
        self.connected = False
        self.emit("disconnected")
        if self.auto_reconnect:
            self.attempt_connection()

    def data_ready(self, source, condition, arg):
        if condition == GLib.IOCondition.IN:
            line = source.readline()
            if line is None or len(line) == 0:
                warning("Client condition IN but not data read.")
                self.handle_disconnect()
                return False
            else:
                self.emit("message", line)

        elif condition == GLib.IOCondition.HUP:
            info("Client received HUP")
            self.handle_disconnect()
            return False

        elif condition == GLib.IOCondition.NVAL:
            info("Client received NVAL")
            self.handle_disconnect()
            return False

        else:
            warning("Client received unknown condition")
            return False
    
        return True

    def send(self, line):
        if not line.endswith('\n'):
            line = line + '\n'

        try:
            self.channel.write(line)
            self.channel.flush()
        except GLib.GError, e:
            error('Client send exception:' + e.message)
