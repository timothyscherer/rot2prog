"""This is a python interface for simulating the Alfa ROT2Prog Controller.
"""
import logging
import rot2prog

if __name__ == '__main__':
	pulses_per_degree = 0

	# set log level
	logging.basicConfig(level = logging.DEBUG)

	# get serial port
	port = input('Please enter the serial port: ')

	# set pulses per degree
	while pulses_per_degree not in [1, 2, 4]:
		pulses_per_degree = input('Pulses per degree: ')
		try:
			pulses_per_degree = int(pulses_per_degree)
		except ValueError:
			print('Please select 1, 2, or 4 pulses per degree.')

	sim = rot2prog.ROT2ProgSim(port, pulses_per_degree)

	logging.getLogger().info('Press [Enter] to close simulator')
	input()
	sim.stop()