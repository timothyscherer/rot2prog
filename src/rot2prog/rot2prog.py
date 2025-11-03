"""This is a python interface to the Alfa ROT2Prog Controller.
"""
import logging
import serial
import time
from threading import Lock, Thread

class ReadTimeout(Exception):

	"""A serial read timed out.
	"""
	
	pass

class PacketError(Exception):

	"""A received packet contained an error.
	"""
	
	pass

class ROT2Prog:

	"""Sends commands and receives responses from the ROT2Prog controller.
	"""
	_log = logging.getLogger(__name__)

	_ser = None

	_pulses_per_degree_lock = Lock()
	_pulses_per_degree = 1

	_limits_lock = Lock()

	def __init__(self, port, timeout = 5):
		"""Creates object and opens serial connection.
		
		Args:
		    port (str): Name of serial port to connect to.
		    timeout (int, optional): Maximum response time from the controller.
		"""
		# open serial port
		self._ser = serial.Serial(
			port = port,
			baudrate = 600,
			bytesize = 8,
			parity = 'N',
			stopbits = 1,
			timeout = timeout,
			inter_byte_timeout = 0.1) # inter_byte_timeout allows continued operation after a bad packet

		self._log.debug('\'' + str(self._ser.name) + '\' opened with ' + str(timeout) + "s timeout")

		# get resolution from controller
		self.status()
		# set the limits to default values
		self.set_limits()

	def _send_command(self, command_packet):
		"""Sends a command packet.
		
		Args:
		    command_packet (list of int): Command packet queued.
		"""
		self._ser.write(bytearray(command_packet))
		self._log.debug('Command packet sent: ' + str(list(map(hex, list(command_packet)))))
		
	def _recv_response(self):
		"""Receives a response packet.
		
		Returns:
		    az (float), el (float): Tuple of current azimuth and elevation.
		
		Raises:
		    PacketError: The response packet is incomplete or contains bad values.
		    ReadTimeout: The controller was unresponsive.
		"""
		# read with timeout
		response_packet = list(self._ser.read(12))

		# attempt to receive 12 bytes, the length of response packet
		self._log.debug('Response packet received: ' + str(list(map(hex, list(response_packet)))))
		if len(response_packet) != 12:
			if len(response_packet) == 0:
				raise ReadTimeout('Response timed out')
			else:
				raise PacketError('Incomplete response packet')
		else:
			# convert from byte values
			az = (response_packet[1] * 100) + (response_packet[2] * 10) + response_packet[3] + (response_packet[4] / 10.0) - 360.0
			el = (response_packet[6] * 100) + (response_packet[7] * 10) + response_packet[8] + (response_packet[9] / 10.0) - 360.0
			PH = response_packet[5]
			PV = response_packet[10]

			az = float(round(az, 1))
			el = float(round(el, 1))

			# check resolution value
			valid_pulses_per_degree = [1, 2, 4, 10]
			if PH != PV or PH not in valid_pulses_per_degree:
				raise PacketError('Invalid controller resolution received (PH = ' + str(PH) + ', PV = ' + str(PV) + ')')
			else:
				with self._pulses_per_degree_lock:
					self._pulses_per_degree = PH

			self._log.debug('Received response')
			self._log.debug('-> Azimuth:   ' + str(az) + '°')
			self._log.debug('-> Elevation: ' + str(el) + '°')
			self._log.debug('-> PH:        ' + str(PH))
			self._log.debug('-> PV:        ' + str(PV))

			return (az, el)

	def stop(self):
		"""Sends a stop command to stop the rotator in the current position.
		
		Returns:
		    az (float), el (float): Tuple of current azimuth and elevation.
		"""
		self._log.debug('Stop command queued')

		cmd = [0x57, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0f, 0x20]
		self._send_command(cmd)
		return self._recv_response()

	def status(self):
		"""Sends a status command to determine the current position of the rotator.
		
		Returns:
		    az (float), el (float): Tuple of current azimuth and elevation.
		"""
		self._log.debug('Status command queued')

		cmd = [0x57, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x1f, 0x20]
		self._send_command(cmd)
		return self._recv_response()

	def set(self, az, el):
		"""Sends a set command to turn the rotator to the specified position.
		
		Args:
		    az (float): Azimuth angle to turn rotator to.
		    el (float): Elevation angle to turn rotator to.
		
		Raises:
		    ValueError: The inputs cannot be sent to the controller.
		"""
		# make sure the inputs are within limits
		az = float(az)
		el = float(el)

		with self._limits_lock:
			if az > self._max_az or az < self._min_az:
				raise ValueError('Azimuth of ' + str(az) + '° is out of range [' + str(self._min_az) + '°, ' + str(self._max_az) + '°]')
			if el > self._max_el or el < self._min_el:
				raise ValueError('Elevation of ' + str(el) + '° is out of range [' + str(self._min_el) + '°, ' + str(self._max_el) + '°]')

		self._log.debug('Set command queued')
		self._log.debug('-> Azimuth:   ' + str(az) + '°')
		self._log.debug('-> Elevation: ' + str(el) + '°')

		# encode with resolution
		with self._pulses_per_degree_lock:
			resolution = self._pulses_per_degree

		H = int(resolution * (float(az) + 360))
		V = int(resolution * (float(el) + 360))

		# convert to ascii characters
		H = "0000" + str(H)
		V = "0000" + str(V)

		# build command
		cmd = [
			0x57,
			int(H[-4]) + 0x30, int(H[-3]) + 0x30, int(H[-2]) + 0x30, int(H[-1]) + 0x30,
			resolution,
			int(V[-4]) + 0x30, int(V[-3]) + 0x30, int(V[-2]) + 0x30, int(V[-1]) + 0x30,
			resolution,
			0x2f,
			0x20]

		self._send_command(cmd)

	def get_limits(self):
		"""Returns the minimum and maximum limits for azimuth and elevation.
		
		Returns:
		    min_az (float), max_az (float), min_el (float), max_el (float): Tuple of minimum and maximum azimuth and elevation.
		"""
		with self._limits_lock:
			return (self._min_az, self._max_az, self._min_el, self._max_el)

	def set_limits(self, min_az = -180, max_az = 540, min_el = -21, max_el = 180):
		"""Sets the minimum and maximum limits for azimuth and elevation.
		
		Args:
		    min_az (int, optional): Minimum azimuth. Defaults to -180.
		    max_az (int, optional): Maximum azimuth. Defaults to 540.
		    min_el (int, optional): Minimum elevation. Defaults to -21.
		    max_el (int, optional): Maximum elevation. Defaults to 180.
		"""
		with self._limits_lock:
			self._min_az = min_az
			self._max_az = max_az
			self._min_el = min_el
			self._max_el = max_el

	def get_pulses_per_degree(self):
		"""Returns the number of pulses per degree.
		
		Returns:
		    int: Pulses per degree defining the resolution of the controller.
		"""
		with self._pulses_per_degree_lock:
			return self._pulses_per_degree

class ROT2ProgSim:

	"""Receives commands and sends responses to simulate the ROT2Prog controller.
	"""
	
	_log = None

	_ser = None
	_retry = 5
	_keep_running = True

	_az = 0
	_el = 0
	_pulses_per_degree = 0

	def __init__(self, port, pulses_per_degree):
		"""Creates object, opens serial connection, and starts daemon thread to run simulator..
		
		Args:
		    port (str): Name of serial port to connect to.
		    pulses_per_degree (int): Resolution of simulated ROT2Prog controller. Options are 1, 2, and 4.
		"""
		self._log = logging.getLogger(__name__)

		# open serial port
		self._ser = serial.Serial(
			port = port,
			baudrate = 600,
			bytesize = 8,
			parity = 'N',
			stopbits = 1,
			timeout = None,
			inter_byte_timeout = 0.1) # inter_byte_timeout allows continued operation after a bad packet

		self._pulses_per_degree = int(pulses_per_degree)
		self._log.info('ROT2Prog simulation interface opened on ' + str(self._ser.name))

		# start daemon thread to communicate on serial port
		Thread(target = self._run, daemon = True).start()

	def _run(self):
		"""Receives command packets, parses them to update the state of the simulator, and sends response packets when necessary.
		"""
		while self._keep_running:
			command_packet = list(self._ser.read(13))
			self._log.debug('Command packet received: ' + str(list(map(hex, list(command_packet)))))
			if len(command_packet) != 13:
				self._log.critical('Incomplete command packet')
			else:
				K = command_packet[11]

				if K in [0x0F, 0x1F]:
					if K == 0x0F:
						self._log.debug('Stop command received')
					elif K == 0x1F:
						self._log.debug('Status command received')

					# convert to byte values
					H = "00000" + str(round(float(self._az + 360), 1))
					V = "00000" + str(round(float(self._el + 360), 1))

					response_packet = [
						0x57,
						int(H[-5]), int(H[-4]), int(H[-3]), int(H[-1]),
						self._pulses_per_degree,
						int(V[-5]), int(V[-4]), int(V[-3]), int(V[-1]),
						self._pulses_per_degree,
						0x20]

					self._log.debug('Response queued')
					self._log.debug('-> Azimuth:   ' + str(self._az) + '°')
					self._log.debug('-> Elevation: ' + str(self._el) + '°')
					self._log.debug('-> PH:        ' + hex(self._pulses_per_degree))
					self._log.debug('-> PV:        ' + hex(self._pulses_per_degree))

					self._ser.write(bytearray(response_packet))

					self._log.debug('Response packet sent: ' + str(list(map(hex, list(response_packet)))))
				elif K == 0x2F:
					# convert from ascii characters
					H = ((command_packet[1] - 0x30) * 1000) + ((command_packet[2] - 0x30) * 100) + ((command_packet[3] - 0x30) * 10) + (command_packet[4] - 0x30)
					V = ((command_packet[6] - 0x30) * 1000) + ((command_packet[7] - 0x30) * 100) + ((command_packet[8] - 0x30) * 10) + (command_packet[9] - 0x30)

					# decode with resolution
					self._az = H/self._pulses_per_degree - 360.0
					self._el = V/self._pulses_per_degree - 360.0

					self._az = float(round(self._az, 1))
					self._el = float(round(self._el, 1))

					self._log.debug('Set command received')
					self._log.debug('-> Azimuth:   ' + str(self._az) + '°')
					self._log.debug('-> Elevation: ' + str(self._el) + '°')
				else:
					self._log.error('Invalid command received (K = ' + str(hex(K)) + ')')

	def stop(self):
		"""Stops the daemon thread running the simulator.
		"""
		self._keep_running = False