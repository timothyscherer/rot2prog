"""This is a python interface for simulating the Alfa ROT2Prog Controller.
"""
import logging
import rot2prog

if __name__ == '__main__':
	debug = ''
	resolution = 0

	while debug.lower() not in ['y', 'n']:
		debug = input('Run debugger? (y/n) ')

	if debug.lower() == 'y':
		logging.basicConfig(level = logging.DEBUG)
		print('Running in debug mode')
	else:
		logging.basicConfig(level = logging.INFO)

	while resolution not in [1, 2, 4]:
		resolution = input('Pulses per degree: ')
		try:
			resolution = int(resolution)
		except ValueError:
			pass

	port = input('Please enter the serial port: ')
	sim = rot2prog.ROT2ProgSim(port, resolution)

	logging.getLogger().info('Press [Enter] to close simulator')
	input()
	sim.stop()