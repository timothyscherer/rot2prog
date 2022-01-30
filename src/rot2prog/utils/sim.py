"""This is a python interface for simulating the Alfa ROT2Prog Controller.
"""
import logging
import rot2prog

if __name__ == '__main__':
	debug = ''
	resolution = 0

	while(debug not in ['y', 'Y', 'n', 'N']):
		debug = input('Run debugger? (y/n) ')

	if debug in ['y', 'Y']:
		logging.basicConfig(level = logging.DEBUG)
		logging.info('Running in debug mode\n')
	else:
		logging.basicConfig(level = logging.INFO)

	while resolution not in [1, 2, 4]:
		resolution = int(input('Pulses per degree: '))

	port = input('Please enter the serial port: ')

	sim = rot2prog.ROT2ProgSim(port, resolution)

	input('PRESS ENTER TO STOP\n')
	sim.stop()