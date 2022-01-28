import logging
import serial
import time

class rot2prog:

	ser = None
	retry = 5
	timeout = 5
	pulse = 1
	max_az = float(360)
	min_az = float(0)
	max_el = float(180)
	min_el = float(0)

	def __init__(self, port):
		# open serial port
		while(self.ser is None):
			try:
				self.ser = serial.Serial(
					port = port,
					baudrate = 600,
					bytesize = 8,
					parity = 'N',
					stopbits = 1,
					timeout = self.timeout)
			except:
				logging.error('Connection to serial port failed, retrying in ' + str(self.retry) + ' seconds')
				time.sleep(self.retry)

		logging.info('ROT2Prog interface opened on ' + str(self.ser.name))

		self.status()
	
	def __del__(self):
		if(self.ser is not None):
			self.ser.close()

	def command(self, cmd):
		self.ser.flush()
		self.ser.write(bytearray(cmd))
		logging.debug('Command packet sent' + str(cmd))

	def response(self):
		response_packet = list(self.ser.read(12)) # read with timeout

		if(len(response_packet) != 12):
			if(len(response_packet) == 0):
				logging.error('Response timed out')
			else:
				logging.error('Invalid response packet')
			return [0, 0]
		else:
			logging.debug('Response packet received: ' + str(list(response_packet)))

			# convert from byte values
			az = (response_packet[1] * 100) + (response_packet[2] * 10) + response_packet[3] + (response_packet[4] / 10) - 360.0
			el = (response_packet[6] * 100) + (response_packet[7] * 10) + response_packet[8] + (response_packet[9] / 10) - 360.0
			PH = response_packet[5]
			PV = response_packet[10]

			# check pulse value
			valid_pulse = [0x1, 0x2, 0x4]
			if(PH != PV or PH not in valid_pulse or PV not in valid_pulse):
				logging.error('Invalid controller resolution [PH = ' + str(hex(PH)) + ', PV = ' + str(hex(PV)) + ']')
			else:
				self.pulse = PH

			logging.info('')
			logging.info('#########################')
			logging.info('# RESPONSE')
			logging.info('#########################')
			logging.info('# Azimuth:   ' + str(az))
			logging.info('# Elevation: ' + str(el))
			logging.info('# PH: ' + str(PH))
			logging.info('# PV: ' + str(PV))
			logging.info('#########################')
			logging.info('')

			return [az, el]

	def status(self):
		logging.info('')
		logging.info('#########################')
		logging.info('# STATUS COMMAND')
		logging.info('#########################')
		logging.info('')

		cmd = [0x57, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x1f, 0x20]
		self.command(cmd)
		return self.response()

	def stop(self):
		logging.info('')
		logging.info('#########################')
		logging.info('# STOP COMMAND')
		logging.info('#########################')
		logging.info('')

		cmd = [0x57, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0f, 0x20]
		self.command(cmd)
		return self.response()

	def set(self, az, el):
		if(az > self.max_az):
			logging.warning('Invalid azimuth [az = ' + str(float(az)) + ', too large]')
			while(az > self.max_az):
				az -= 360
			logging.warning('Azimuth corrected to ' + str(float(az)))
		if(az < self.min_az):
			logging.warning('Invalid azimuth [az = ' + str(float(az)) + ', too small]')
			while(az < self.min_az):
				az += 360
			logging.warning('Azimuth corrected to ' + str(float(az)))

		if(el > self.max_el):
			logging.warning('Invalid elevation [el = ' + str(float(el)) + ', too large]')
			el = self.max_el
			logging.warning('Elevation corrected to ' + str(float(el)))
		if(el < self.min_el):
			logging.warning('Invalid elevation [el = ' + str(float(el)) + ', too small]')
			el = self.min_el
			logging.warning('Elevation corrected to ' + str(float(el)))

		logging.info('')
		logging.info('#########################')
		logging.info('# SET COMMAND')
		logging.info('#########################')
		logging.info('# Azimuth:   ' + str(float(az)))
		logging.info('# Elevation: ' + str(float(el)))
		logging.info('#########################')
		logging.info('')

		# encode with pulse
		H = int(self.pulse * (float(az) + 360))
		V = int(self.pulse * (float(el) + 360))

		# convert to ascii characters
		H = "000" + str(H)
		V = "000" + str(V)

		# build command
		cmd = [
			0x57,
			int(H[-4]), int(H[-3]), int(H[-2]), int(H[-1]),
			self.pulse,
			int(V[-4]), int(V[-3]), int(V[-2]), int(V[-1]),
			self.pulse,
			0x2f,
			0x20]

		self.command(cmd)

	def test(self):
		logging.debug('Running test sequence')
		rot.set(0, 0)
		time.sleep(1)
		rot.set(180, 45)
		time.sleep(1)
		rot.set(360, 90)
		time.sleep(1)
		rot.set(380, 180)
		time.sleep(1)
		rot.set(-180, 200)
		time.sleep(1)
		rot.stop()

if __name__ == "__main__":
	debug = ''

	while(debug not in ['y', 'n']):
		debug = input('Run debugger? (y/n) ')

	if(debug in ['y']):
		logging.basicConfig(level = logging.DEBUG)
		logging.info('Running in debug mode')
	else:
		logging.basicConfig(level = logging.INFO)

	port = input('Please enter the serial port: ')

	rot = rot2prog(port)
	rot.test()

	print("Done")