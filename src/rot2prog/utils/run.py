import logging
import rot2prog

if __name__ == '__main__':
	debug = ''

	while(debug not in ['y', 'n']):
		debug = input('Run debugger? (y/n) ')

	if(debug in ['y']):
		debug = True
		logging.basicConfig(level = logging.DEBUG)
		logging.info('Running in debug mode\n')
	else:
		debug = False

	port = input('Please enter the serial port: ')

	rot = rot2prog.ROT2Prog(port)
	rot._help()

	# wait for user commands
	while True:
		cmd = input('> ')
		args = cmd.split(' ')

		try:
			if args[0] == 'stop':
				rsp = rot.stop()
				print('azimuth:   ' + str(rsp[0]))
				print('elevation: ' + str(rsp[1]))
				print()
			elif args[0] == 'status':
				rsp = rot.status()
				print('azimuth:   ' + str(rsp[0]))
				print('elevation: ' + str(rsp[1]))
				print()
			elif args[0] == 'set':
				rot.set(float(args[1]), float(args[2]))
				if not debug:
					print()
			else:
				raise Exception
		except:
			print('Invalid command!')
			rot._help()