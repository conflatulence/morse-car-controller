#!/usr/bin/env python3

import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from tkinter.messagebox import showwarning
import socket
import json

import logging
from logging import info, debug, warning, error

from math import pi

from utils import Position, clamp

MODE_PARK=0
MODE_DRIVE=1
MODE_AUTO=2

class CarInterface:
	def __init__(self, parent):
		self.parent = parent		

		self.target_pos = Position()
		self.current_pos = Position()

		self.target_speed = 0
		self.current_speed = 0

		self.mode = MODE_PARK

		self.throttle = 0
		self.brake = 0
		self.steer = 0

	def handle_msg(self, msg):
		try:
			d = json.loads(msg)
		except ValueError as err:
			print(dir(err))
			warning("Invalid message received:" + str(err))
			warning(msg)
			return

		if 'current_speed' in d:
			self.current_speed = d['current_speed']
			self.parent.current_speed.update(self.current_speed)
		
		if 'target_speed' in d:
			self.target_speed = d['target_speed']
			self.parent.target_speed.update(self.target_speed)

		if 'target_pos' in d:
			self.target_pos.x, self.target_pos_y = d['target_pos']
			self.parent.target_pos.update((self.target_pos.x, self.target_pos.y))

		if 'current_pos' in d:
			self.current_pos.x, self.current_pos.y = d['current_pos']
			self.parent.current_pos.update((self.current_pos.x, self.current_pos.y))
		
		if 'mode' in d:
			self.mode = d['mode']
			self.parent.mode.update(self.mode)

		if 'steer' in d:
			self.steer = d['steer']
			self.parent.steer.update(self.steer)
	
		if 'throttle' in d:
			self.throttle = d['throttle']
			self.parent.throttle.update(self.throttle)

		if 'brake' in d:
			self.brake = d['brake']
			self.parent.brake.update(self.brake)

	def stop(self):
		s = json.dumps({'cmd':'stop'})
		self.parent.send(s)
	
	def set_speed(self, speed):
		if self.mode == MODE_DRIVE:
			s = json.dumps({'cmd':'set_speed', 'speed':round(speed, 2)})
			self.parent.send(s)
		else:
			warning("Not in drive mode.")

	def adjust_speed(self, amount):
		if self.mode == MODE_DRIVE:
			s = json.dumps({'cmd':'adjust_speed', 'amount':round(amount, 2)})
			self.parent.send(s)
		else:
			warning("Not in drive mode.")
	
	def turn(self, angle):
		if self.mode == MODE_DRIVE:		
			s = json.dumps({'cmd':'turn', 'angle':round(angle, 2)})
			self.parent.send(s)
		else:
			warning("Not in drive mode.")

	def set_target_pos(self, x, y):
		s = json.dumps({'cmd':'target_pos', 'x':round(x,2), 'y':round(y,2)})
		self.parent.send(s)

	def set_auto_speed(self, speed):
		s = json.dumps({'cmd':'config', 'auto_speed':round(speed,2)})
		self.parent.send(s)

	def set_mode(self, mode):
		if mode == MODE_PARK:
			mode_str = 'park'
		elif mode == MODE_DRIVE:
			mode_str = 'drive'
		elif mode == MODE_AUTO:
			mode_str = 'auto'
		else:
			warning("Unknown mode requested.")
			return

		s = json.dumps({'cmd':'mode', 'mode':mode_str})
		self.parent.send(s)

class LabelVar(tk.Frame):
	def __init__(self, master, text, fmt, initial_value):
		tk.Frame.__init__(self, master)
		self.fmt = fmt
		self.string_var = tk.StringVar()
		self.description_label = tk.Label(self, text=text)
		self.value_label = tk.Label(self, textvariable=self.string_var)
		self.description_label.pack(side=tk.LEFT)
		self.value_label.pack(side=tk.LEFT)
		self.update(initial_value)

	def update(self, val):
		self.string_var.set(self.fmt % val)

class Application(tk.Frame):
	def __init__(self, root=None):
		tk.Frame.__init__(self, root)

		root.wm_title("GUI")

		self.pack(expand=True, fill=tk.BOTH)
		
		root.bind("<KeyPress>", self.key_pressed)
		root.bind("<KeyRelease>", self.key_released)		
		#root.bind("<Button-1>", self.mouse_click)

		lf = tk.Frame(self)
		lf.pack(expand=False, fill=tk.X)

		# the padding sizes of the labels.
		vpx = 30
		vpy = 0
		gpx = 20

		self.throttle = LabelVar(lf, "Throttle", "%0.2f", 0)
		self.brake = LabelVar(lf, "Brake", "%0.2f", 0)
		self.steer = LabelVar(lf, "Steer", "%0.2f", 0)

		self.current_speed = LabelVar(lf, "Current Speed", "%0.2f", 0)
		self.target_speed = LabelVar(lf, "Target Speed", "%0.2f", 0)

		self.target_pos = LabelVar(lf, "Target Pos", "%0.2f, %0.2f", (0,0))
		self.current_pos = LabelVar(lf, "Current Pos", "%0.2f, %0.2f", (0,0))

		self.mode = LabelVar(lf, "Mode", "%s", "park")

		self.entry_target_x = tk.Entry(lf)
		self.entry_target_y = tk.Entry(lf)
		self.button_target_set = tk.Button(lf, text="Set", command=self.target_set_clicked)

		row = 0
		self.throttle.grid(row=row, column=1, sticky=tk.W)
		self.brake.grid(row=row, column=2, sticky=tk.W)
		self.steer.grid(row=row, column=3, sticky=tk.W)

		#self.throttle_label = tk.Label(lf, text="Throttle 0").grid(row=0,column=1, padx=vpx)
		#self.brake_label = tk.Label(lf, text="Brake 0").grid(row=0,column=2, padx=vpx)
		#self.steer_label = tk.Label(lf, text="Steer 0").grid(row=0,column=3, padx=vpx)
		
		row += 1
		self.target_speed.grid(row=row, column=1, sticky=tk.W)
		self.current_speed.grid(row=row, column=2, sticky=tk.W)

		row += 1
		self.target_pos.grid(row=row, column=1, sticky=tk.W)
		self.current_pos.grid(row=row, column=2, sticky=tk.W)

		row += 1
		tk.Label(lf, text="Set Target Pos").grid(row=row, column=0, sticky=tk.W)
		self.entry_target_x.grid(row=row, column=1, sticky=tk.W)
		self.entry_target_y.grid(row=row, column=2, sticky=tk.W)
		self.button_target_set.grid(row=row, column=3, sticky=tk.W)

		row += 1
		self.mode.grid(row=row, column=0, sticky=tk.W)

		self.mode_var = tk.IntVar()
		self.mode_var.set(MODE_PARK)

		for text,mode in [("Park", MODE_PARK),("Drive", MODE_DRIVE),("Auto", MODE_AUTO)]:
			b = tk.Radiobutton(lf, text=text, variable=self.mode_var,
					value=mode, command=self.control_mode_changed)
			b.grid(row=row, column=mode+1)

		row += 1
		self.scroll_lock = tk.IntVar()
		self.scroll_lock.set(1)
		self.scroll_lock_button = tk.Checkbutton(lf, text='auto-scroll', variable=self.scroll_lock) 
		self.scroll_lock_button.grid(row=row, column=0, sticky=tk.W)

		#canvas = tk.Canvas(self, background="white")
		#self.canvas = canvas
		#canvas.pack(expand=True, fill=tk.BOTH)
		#canvas.create_line(0, 0, 200, 100)
		#canvas.create_line(0, 100, 200, 0, fill="red", dash=(4, 4))

		text = ScrolledText(self)
		text.pack(expand=True, fill=tk.BOTH)
		self.text = text

		self.data = bytearray()
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket.connect(("localhost", 60212))
		self.socket.setblocking(0)

		self.after(100, self.poll_socket)

		self.car = CarInterface(self)

	# no useful socket monitoring in tkinter mainloop, so poll.
	# tkinter.createfilehandle() doesn't work on windows.
	def poll_socket(self):
		self.after(100, self.poll_socket)		

		try:
			new_data = self.socket.recv(4096)
		except BlockingIOError:
			return

		self.data.extend(new_data)	
		msgs = new_data.split(b'\n')
		
		for msg_data in msgs[:-1]:
			msg = msg_data.decode()
			self.add_text('Received:' + msg + '\n')
			self.car.handle_msg(msg)

		self.data = bytearray(msgs[-1])

	def send(self, msg):
		msg += '\n'
		data = msg.encode()
		sent_data = self.socket.send(data)
		if sent_data != len(data):
			warning("Socket send did not send all data.")
		self.add_text('Sent:' + msg)	

	def add_text(self, s):
		self.text.config(state=tk.NORMAL)
		self.text.insert(tk.END, s)
		if self.scroll_lock.get() > 0:		
			self.text.see(tk.END)
		self.text.config(state=tk.DISABLED)

	def target_set_clicked(self):
		try:
			x = float(self.entry_target_x.get())
			y = float(self.entry_target_y.get())
		except ValueError:
			showwarning(title='Warning', message='Invalid target position.')
			return

		self.car.set_target_pos(x,y)

	def control_mode_changed(self):
		control_mode = self.mode_var.get()
		self.add_text("New mode: %d.\n" % control_mode)
		self.car.set_mode(control_mode)

	def key_pressed(self, event):
		if event.keysym in ('q', 'Escape'):
			self.master.quit()

		if self.car.mode == MODE_DRIVE:
			if event.keysym == 'Up':
				self.car.adjust_speed(1)
			elif event.keysym == 'Down':
				self.car-adjust_speed(-1)
			elif event.keysym == 'Left':
				self.car.turn(pi/3)
			elif event.keysym == 'Right':
				self.car.turn(-pi/3)
			elif event.keysym == 'space':
				self.car.stop

	def key_released(self, event):
		if self.car.mode == MODE_DRIVE:
			if event.keysym == 'Left':
				self.car.turn(0)
			elif event.keysym == 'Right':
				self.car.turn(0)

#	def mouse_click(self, event):
#		frame.focus_set()
#		print("clicked at %i %i" %( event.x, event.y)) 

if __name__ == '__main__':

	root = tk.Tk()

	app = Application(root)

	app.mainloop()

