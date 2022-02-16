import logging
import rot2prog

def help():
	print()
	print('ROT2Prog Live Interface Commands.')
	print()
	print('options:')
	print('  help                       display this help message')
	print('  quit                       end the program')
	print('  ppd                        show pulses per degree')
	print('  stop                       send stop command')
	print('  status                     send status command')
	print('  set [azimuth] [elevation]  send set command with a position')

if __name__ == '__main__':
	log = logging.getLogger(__name__)
	
	debug = ''

	while debug.lower() not in ['y', 'n']:
		debug = input('Run debugger? (y/n) ')

	if debug.lower() == 'y':
		logging.basicConfig(level = logging.DEBUG)
		print('Running in debug mode')
	else:
		logging.basicConfig(level = logging.INFO)

	port = input('Please enter the serial port: ')

	rot = rot2prog.ROT2Prog(port)
	help()

	run = True
	# wait for user commands
	while run:
		cmd = input('\n> ')
		args = cmd.split(' ')

		try:
			if args[0].lower() == 'stop':
				rsp = rot.stop()
				log.info('Azimuth: ' + str(rsp[0]))
				log.info('Elevation: ' + str(rsp[1]))
			elif args[0].lower() == 'status':
				rsp = rot.status()
				log.info('Azimuth: ' + str(rsp[0]))
				log.info('Elevation: ' + str(rsp[1]))
			elif args[0].lower() == 'set':
				rot.set(float(args[1]), float(args[2]))
			elif args[0].lower() == 'ppd':
				log.info('Pulses Per Degree: ' + str(rot.get_pulses_per_degree()))
			elif args[0].lower() == 'help':
				help()
			elif args[0].lower() == 'quit':
				run = False
			else:
				raise Exception
		except:
			log.error('Invalid command!')
			help()