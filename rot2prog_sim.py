import logging
import serial
import time
from threading import Thread

class rot2prog_sim:

	ser = None
	retry = 5
	keep_running = True
	az = 0
	el = 0
	pulse = 1

	def __init__(self, port, pulse = 1):
		self.pulse = pulse

		# open serial port
		while(self.ser is None):
			try:
				self.ser = serial.Serial(
					port = port,
					baudrate = 600,
					bytesize = 8,
					parity = 'N',
					stopbits = 1,
					timeout = None)
			except:
				logging.error('Connection to serial port failed, retrying in ' + str(self.retry) + ' seconds')
				time.sleep(self.retry)

		logging.info('ROT2Prog simulated hardware interface opened on ' + str(self.ser.name))

		Thread(target = self.run, daemon = True).start()
	
	def __del__(self):
		if(self.ser is not None):
			self.ser.close()

	def run(self):
		while(self.keep_running):
			command_packet = list(self.ser.read(13))
			logging.debug('Command packet: ' + str(command_packet))

			K = command_packet[-2]

			if(K in [0x0F, 0x1F]):
				if(K == 0x0F):
					logging.info('')
					logging.info('#########################')
					logging.info('# STOP COMMAND')
					logging.info('#########################')
					logging.info('')
				elif(K == 0x1F):
					logging.info('')
					logging.info('#########################')
					logging.info('# STATUS COMMAND')
					logging.info('#########################')
					logging.info('')

				# convert to byte values
				H = "000" + str(round(float(self.az + 360), 1))
				V = "000" + str(round(float(self.el + 360), 1))

				rsp = [
					0x57,
					int(H[-5]), int(H[-4]), int(H[-3]), int(H[-1]),
					self.pulse,
					int(V[-5]), int(V[-4]), int(V[-3]), int(V[-1]),
					self.pulse,
					0x20]

				logging.info('')
				logging.info('#########################')
				logging.info('# RESPONSE')
				logging.info('#########################')
				logging.info('# Azimuth:   ' + str(float(self.az)))
				logging.info('# Elevation: ' + str(float(self.el)))
				logging.info('# PH: ' + str(self.pulse))
				logging.info('# PV: ' + str(self.pulse))
				logging.info('#########################')
				logging.info('')

				self.ser.flush()
				self.ser.write(bytearray(rsp))

				logging.debug('Response packet sent' + str(rsp))
			elif(K == 0x2F):
				logging.debug('Set command received')

				# convert from ascii characters
				H = (command_packet[1] * 1000) + (command_packet[2] * 100) + (command_packet[3] * 10) + command_packet[4]
				V = (command_packet[6] * 1000) + (command_packet[7] * 100) + (command_packet[8] * 10) + command_packet[9]

				# decode with pulse
				self.az = H/self.pulse - 360.0
				self.el = V/self.pulse - 360.0

				logging.info('')
				logging.info('#########################')
				logging.info('# SET COMMAND')
				logging.info('#########################')
				logging.info('# Azimuth:   ' + str(self.az))
				logging.info('# Elevation: ' + str(self.el))
				logging.info('#########################')
				logging.info('')
			else:
				logging.error('Invalid command received [K = ' + str(hex(K)) + ']')

if __name__ == "__main__":
	debug = ''
	pulse = 0

	while(debug not in ['y', 'n']):
		debug = input('Run debugger? (y/n) ')

	if(debug in ['y']):
		logging.basicConfig(level = logging.DEBUG)
		logging.info('Running in debug mode')
	else:
		logging.basicConfig(level = logging.INFO)

	while(pulse not in [1, 2, 4]):
		pulse = int(input('Pulses per degree: '))

	port = input('Please enter the serial port: ')

	rot = rot2prog_sim(port, pulse)

	input('PRESS ANY KEY TO STOP\n')
	rot.keep_running = False