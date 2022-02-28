"""Standalone program to manually interact with the ROT2Prog hardware.
"""
import logging
import rot2prog

def help():
	"""Displays a help message.
	"""
	print()
	print('ROT2Prog Live Interface Commands.')
	print()
	print('options:')
	print('  help                       display this help message')
	print('  quit                       end the program')
	print('  stop                       send stop command')
	print('  status                     send status command')
	print('  ppd                        show pulses per degree')
	print('  set [azimuth] [elevation]  send set command with a position')

def connect():
	port = input('Please enter the serial port: ')
	try:
		return rot2prog.ROT2Prog(port)
	except Exception as e:
		print(e)

if __name__ == '__main__':
	logging.basicConfig(level = logging.DEBUG)

	rot = None
	while not rot:
		rot = connect()

	help()

	run = True
	# wait for user commands
	while run:
		cmd = input('\n> ')
		args = cmd.split(' ')

		try:
			if args[0].lower() == 'help':
				help()
			elif args[0].lower() == 'quit':
				run = False
			elif args[0].lower() == 'stop':
				try:
					rsp = rot.stop()
					print('Azimuth:   ' + str(rsp[0]) + '°')
					print('Elevation: ' + str(rsp[1]) + '°')
				except:
					print('Failed to stop')
			elif args[0].lower() == 'status':
				try:
					rsp = rot.status()
					print('Azimuth:   ' + str(rsp[0]) + '°')
					print('Elevation: ' + str(rsp[1]) + '°')
				except:
					print('Failed to get status')
			elif args[0].lower() == 'ppd':
				print('Pulses Per Degree: ' + str(rot.get_pulses_per_degree()))
			elif args[0].lower() == 'set':
				rot.set(float(args[1]), float(args[2]))
			else:
				raise Exception('Invalid command!')
		except Exception as e:
			print(e)
			help()