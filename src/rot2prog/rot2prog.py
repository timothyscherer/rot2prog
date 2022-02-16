"""This is a python interface to the Alfa ROT2Prog Controller.
"""
import logging
import serial
import time
from threading import Lock, Thread

class ROT2Prog:

	"""Sends commands and receives responses from the ROT2Prog controller.
	"""

	_log = logging.getLogger(__name__)

	_ser = None

	_pulses_per_degree_lock = Lock()
	_pulses_per_degree = 1

	_bounds_lock = Lock()
	_min_az = 0.0
	_max_az = 360.0
	_min_el = 0.0
	_max_el = 180.0

	def __init__(self, port, timeout = 5):
		"""Creates object and opens serial connection.
		
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
		# set the bounds to default values
		self.set_bounds()

	def _send_command(self, cmd):
		"""Sends a command packet.
		
		Args:
		    cmd (list of int): Command packet queued.
		"""
		self._ser.flush()
		self._ser.write(bytearray(cmd))
		self._log.debug('Command packet sent: ' + str(cmd))

	def _recv_response(self):
		"""Receives a response packet.
		
		Returns:
		    float: Azimuth and elevation.
		"""
		# read with timeout
		response_packet = list(self._ser.read(12))

		# attempt to receive 12 bytes, the length of response packet
		if len(response_packet) != 12:
			if len(response_packet) == 0:
				self._log.error('Response timed out')
			else:
				self._log.error('Invalid response packet')
			return [0, 0]
		else:
			self._log.debug('Response packet received: ' + str(list(response_packet)))

			# convert from byte values
			az = (response_packet[1] * 100) + (response_packet[2] * 10) + response_packet[3] + (response_packet[4] / 10.0) - 360.0
			el = (response_packet[6] * 100) + (response_packet[7] * 10) + response_packet[8] + (response_packet[9] / 10.0) - 360.0
			PH = response_packet[5]
			PV = response_packet[10]

			az = float(round(az, 1))
			el = float(round(el, 1))

			# check resolution value
			valid_pulses_per_degree = [1, 2, 4]
			if PH != PV or PH not in valid_pulses_per_degree:
				self._log.critical('Invalid controller resolution [PH = ' + str(PH) + ', PV = ' + str(PV) + ']')
				with self._pulses_per_degree_lock:
					self._log.info('Resolution remaining at ' + str(self._pulses_per_degree) + ' pulses per degree')
			else:
				with self._pulses_per_degree_lock:
					self._pulses_per_degree = PH

			self._log.debug('Received response')
			self._log.debug('-> Azimuth:   ' + str(az))
			self._log.debug('-> Elevation: ' + str(el))
			self._log.debug('-> PH:        ' + str(PH))
			self._log.debug('-> PV:        ' + str(PV))

			return (az, el)

	def status(self):
		"""Sends a status command to determine the current position of the rotator.
		
		Returns:
		    (float, float): Tuple of current azimuth and elevation.
		"""
		self._log.debug('Status command queued')

		cmd = [0x57, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x1f, 0x20]
		self._send_command(cmd)
		return self._recv_response()

	def stop(self):
		"""Sends a stop command to stop the rotator in the current position.
		
		Returns:
		    (float, float): Tuple of current azimuth and elevation.
		"""
		self._log.debug('Stop command queued')

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
		with self._bounds_lock:
			if az > self._max_az:
				az = self._max_az
				self._log.warning('Azimuth too large, corrected to: ' + str(az))
			if az < self._min_az:
				az = self._min_az
				self._log.warning('Azimuth too small, corrected to: ' + str(az))

			if el > self._max_el:
				el = self._max_el
				self._log.warning('Elevation too large, corrected to: ' + str(el))
			if el < self._min_el:
				el = self._min_el
				self._log.warning('Elevation too small, corrected to: ' + str(el))

		self._log.debug('Set command queued')
		self._log.debug('-> Azimuth:   ' + str(az))
		self._log.debug('-> Elevation: ' + str(el))

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
			int(H[-4]), int(H[-3]), int(H[-2]), int(H[-1]),
			resolution,
			int(V[-4]), int(V[-3]), int(V[-2]), int(V[-1]),
			resolution,
			0x2f,
			0x20]

		self._send_command(cmd)

	def get_bounds(self):
		"""Returns the minimum and maximum bounds for azimuth and elevation.
		
		Returns:
		    (float, float, float, float): Tuple of minimum azimuth, maximum azimuth, minimum elevation, and maximum elevation.
		"""
		with self._bounds_lock:
			return (self._min_az, self._max_az, self._min_el, self._max_el)

	def set_bounds(self, min_az = -180, max_az = 540, min_el = -21, max_el = 180):
		"""Sets the minimum and maximum bounds for azimuth and elevation.
		
		Args:
		    min_az (int, optional): Minimum azimuth. Defaults to -180.
		    max_az (int, optional): Maximum azimuth. Defaults to 540.
		    min_el (int, optional): Minimum elevation. Defaults to -21.
		    max_el (int, optional): Maximum elevation. Defaults to 180.
		"""
		with self._bounds_lock:
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
	
	Attributes:
	    az (float): Current azimuth angle of rotator.
	    el (float): Current elevation angle of rotator.
	"""
	
	_log = None

	_ser = None
	_retry = 5
	_keep_running = True

	az = 0
	el = 0
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
			timeout = None)

		self._pulses_per_degree = pulses_per_degree
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
					self._pulses_per_degree,
					int(V[-5]), int(V[-4]), int(V[-3]), int(V[-1]),
					self._pulses_per_degree,
					0x20]

				self._log.info('Response queued')
				self._log.info('-> Azimuth:   ' + str(self.az))
				self._log.info('-> Elevation: ' + str(self.el))
				self._log.info('-> PH:        ' + str(self._pulses_per_degree))
				self._log.info('-> PV:        ' + str(self._pulses_per_degree))

				self._ser.flush()
				self._ser.write(bytearray(rsp))

				self._log.debug('Response packet sent: ' + str(rsp))
			elif K == 0x2F:
				# convert from ascii characters
				H = (command_packet[1] * 1000) + (command_packet[2] * 100) + (command_packet[3] * 10) + command_packet[4]
				V = (command_packet[6] * 1000) + (command_packet[7] * 100) + (command_packet[8] * 10) + command_packet[9]

				# decode with resolution
				self.az = H/self._pulses_per_degree - 360.0
				self.el = V/self._pulses_per_degree - 360.0

				self.az = float(round(self.az, 1))
				self.el = float(round(self.el, 1))

				self._log.info('Set command received')
				self._log.info('-> Azimuth:   ' + str(self.az))
				self._log.info('-> Elevation: ' + str(self.el))
			else:
				self._log.error('Invalid command received [K = ' + str(hex(K)) + ']')

	def stop(self):
		"""Stops the daemon thread running the simulator.
		"""
		self._keep_running = False