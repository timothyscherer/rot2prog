"""This is a python interface to the Alfa ROT2Prog Controller.
"""
import logging
import serial
import time
from threading import Thread

class ROT2Prog:

	"""Sends commands and receives responses from the ROT2Prog controller.
	
	Attributes:
	    max_az (float): Maximum azimuth angle.
	    max_el (float): Maximum elevation angle.
	    min_az (float): Minimum azimuth angle.
	    min_el (float): Minimum elevation angle.
	"""

	_log = logging.getLogger(__name__)
	_ser = None
	_resolution = 1

	min_az = 0.0
	max_az = 360.0
	min_el = 0.0
	max_el = 180.0

	def __init__(self, port, timeout = 5):
		"""Initializes object and opens serial connection.
		
		Args:
		    port (str): Name of serial port to connect to.
		    timeout (int, optional): Worst case response time of the controller.
		"""
		# open serial port
		self._ser = serial.Serial(
			port = port,
			baudrate = 600,
			bytesize = 8,
			parity = 'N',
			stopbits = 1,
			timeout = timeout)

		self._log.info('ROT2Prog interface opened on ' + str(self._ser.name))

		# get resolution from controller
		self.status()

	def _send_command(self, cmd):
		"""Sends a command packet.
		
		Args:
		    cmd (list of int): Command packet to be sent.
		"""
		self._ser.flush()
		self._ser.write(bytearray(cmd))
		self._log.debug('Command packet sent: ' + str(cmd))

	def _recv_response(self):
		"""Receives a response packet.
		
		Returns:
		    list of float: List containing azimuth and elevation.
		"""
		# read with timeout
		response_packet = list(self._ser.read(12))

		# attempt to receive 12 bytes (length of response packet)
		if len(response_packet) != 12:
			if len(response_packet) == 0:
				self._log.error('Response timed out')
			else:
				self._log.error('Invalid response packet')
			return [0, 0]
		else:
			self._log.debug('Response packet received: ' + str(list(response_packet)))

			# convert from byte values
			az = (response_packet[1] * 100) + (response_packet[2] * 10) + response_packet[3] + (response_packet[4] / 10) - 360.0
			el = (response_packet[6] * 100) + (response_packet[7] * 10) + response_packet[8] + (response_packet[9] / 10) - 360.0
			PH = response_packet[5]
			PV = response_packet[10]

			# check resolution value
			valid_resolution = [0x1, 0x2, 0x4]
			if PH != PV or PH not in valid_resolution:
				self._log.error('Invalid controller resolution [PH = ' + str(hex(PH)) + ', PV = ' + str(hex(PV)) + ']')
			else:
				self._resolution = PH

			self._log.debug('Received response')
			self._log.debug('-> Azimuth:   ' + str(round(float(az), 2)))
			self._log.debug('-> Elevation: ' + str(round(float(el), 2)))
			self._log.debug('-> PH:        ' + str(PH))
			self._log.debug('-> PV:        ' + str(PV))

			return [az, el]

	def status(self):
		"""Sends a status command to determine the current position of the rotator.
		
		Returns:
		    list of float: List containing azimuth and elevation.
		"""
		self._log.debug('Status command to be sent')

		cmd = [0x57, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x1f, 0x20]
		self._send_command(cmd)
		return self._recv_response()

	def stop(self):
		"""Sends a stop command to stop the rotator in the current position.
		
		Returns:
		    list of float: List containing azimuth and elevation.
		"""
		self._log.debug('Stop command to be sent')

		cmd = [0x57, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0f, 0x20]
		self._send_command(cmd)
		return self._recv_response()

	def set(self, az, el):
		"""Sends a set command to turn the rotator to the specified position.
		
		Args:
		    az (float): Azimuth angle to turn rotator to.
		    el (float): Elevation angle to turn rotator to.
		"""
		# make sure the inputs are within bounds and correct violations
		if az > self.max_az:
			while az > self.max_az:
				az -= 360
			self._log.warning('Azimuth corrected to: ' + str(round(float(az), 2)))
		if az < self.min_az:
			while az < self.min_az:
				az += 360
			self._log.warning('Azimuth corrected to: ' + str(round(float(az), 2)))

		if el > self.max_el:
			el = self.max_el
			self._log.warning('Elevation corrected to: ' + str(round(float(el), 2)))
		if el < self.min_el:
			el = self.min_el
			self._log.warning('Elevation corrected to: ' + str(round(float(el), 2)))

		self._log.debug('Set command to be sent')
		self._log.debug('-> Azimuth:   ' + str(round(float(az), 2)))
		self._log.debug('-> Elevation: ' + str(round(float(el), 2)))

		# encode with resolution
		H = int(self._resolution * (float(az) + 360))
		V = int(self._resolution * (float(el) + 360))

		# convert to ascii characters
		H = "0000" + str(H)
		V = "0000" + str(V)

		# build command
		cmd = [
			0x57,
			int(H[-4]), int(H[-3]), int(H[-2]), int(H[-1]),
			self._resolution,
			int(V[-4]), int(V[-3]), int(V[-2]), int(V[-1]),
			self._resolution,
			0x2f,
			0x20]

		self._send_command(cmd)

class ROT2ProgSim:

	"""Receives commands and sends responses to simulate the ROT2Prog controller.
	
	Attributes:
	    az (int): Current azimuth angle of rotator.
	    el (int): Current elevation angle of rotator.
	"""
	
	_log = None
	_ser = None
	_retry = 5
	_keep_running = True
	_resolution = 0

	az = 0
	el = 0

	def __init__(self, port, resolution):
		"""Initializes object, opens serial connection, and starts daemon thread to run simulator..
		
		Args:
		    port (str): Name of serial port to connect to.
		    resolution (int): Resolution of simulated ROT2Prog controller. Options are 0x1, 0x2, and 0x4.
		"""
		self._log = logging.getLogger(__name__)

		# open serial port
		self._ser = serial.Serial(
			port = port,
			baudrate = 600,
			bytesize = 8,
			parity = 'N',
			stopbits = 1,
			timeout = None)

		self._resolution = resolution
		self._log.info('ROT2Prog simulation interface opened on ' + str(self._ser.name))

		# start daemon thread to communicate on serial port
		Thread(target = self.run, daemon = True).start()

	def run(self):
		"""Receives command packets, parses them to update the state of the simulator, and sends response packets when necessary.
		"""
		while self._keep_running:
			command_packet = list(self._ser.read(13))
			self._log.debug('Command packet received: ' + str(command_packet))

			K = command_packet[11]

			if K in [0x0F, 0x1F]:
				if K == 0x0F:
					self._log.info('Stop command received')
				elif K == 0x1F:
					self._log.info('Status command received')

				# convert to byte values
				H = "00000" + str(round(float(self.az + 360), 1))
				V = "00000" + str(round(float(self.el + 360), 1))

				rsp = [
					0x57,
					int(H[-5]), int(H[-4]), int(H[-3]), int(H[-1]),
					self._resolution,
					int(V[-5]), int(V[-4]), int(V[-3]), int(V[-1]),
					self._resolution,
					0x20]

				self._log.debug('Response to be sent')
				self._log.debug('-> Azimuth:   ' + str(float(self.az)))
				self._log.debug('-> Elevation: ' + str(float(self.el)))
				self._log.debug('-> PH:        ' + str(self._resolution))
				self._log.debug('-> PV:        ' + str(self._resolution))

				self._ser.flush()
				self._ser.write(bytearray(rsp))

				self._log.debug('Response packet sent: ' + str(rsp))
			elif K == 0x2F:
				# convert from ascii characters
				H = (command_packet[1] * 1000) + (command_packet[2] * 100) + (command_packet[3] * 10) + command_packet[4]
				V = (command_packet[6] * 1000) + (command_packet[7] * 100) + (command_packet[8] * 10) + command_packet[9]

				# decode with resolution
				self.az = H/self._resolution - 360.0
				self.el = V/self._resolution - 360.0

				self._log.info('Set command received')
				self._log.info('-> Azimuth:   ' + str(self.az))
				self._log.info('-> Elevation: ' + str(self.el))
			else:
				self._log.error('Invalid command received [K = ' + str(hex(K)) + ']')

	def stop(self):
		"""Stops the daemon thread running the simulator.
		"""
		self._keep_running = False