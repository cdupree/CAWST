#!/usr/bin/env python


"""

cawst.py --acccessId=X --secretKey=Y --hosts=Z | -h | --help 

-h | --help => print this usage messages

X = 

Y =

Z = comma delimited list of short hostnames (eg, web1,db1)

Alternatively the 3 options above may be placed in a config 
file which you may provide as a command line argument


"""

# TODO: Better Unit Tests.

import sys
import getopt


from boto.ec2.connection import EC2Connection

def getConn(accId, secKey):
	return  EC2Connection(accId, secKey)

def startMachine(conn, host):
	# TODO: config file items
	# TODO: make key be dynamic, and upload with import_key_pair
	ami = "ami-31814f58"
	ssh = "cawst"
	instance = "m1.small"
	secGroup = "cawst"

	conn.run_instances(
		ami,
		key_name = ssh,
		instance_type = instance,
		security_groups = [secGroup],
		client_token = host)

def hostExistsInAWS(conn,host):
	hdict = dict([('client_token',host)])

	return conn.get_all_instances(instance_ids=None, filters=hdict)

def poll(accId, secKey, hostArr ):

	# TODO:  Still Error Checking 
	conn =  getConn(accId,secKey)

	for host in hostArr:
		hostExists = hostExistsInAWS(conn,host)
		if not hostExists:
			print 'starting host ',host
			startMachine(conn,host)
		else:
			print 'host ', host,' exists'
			if hostExists[0].instances[0].update() == "terminated":
				print 'host ', host, ' is not running, so I will start it'
				# Not working with terminated?
				hostExists[0].instances[0].reboot()
				#startMachine(conn,host)
			else:
				print 'host ', host, ' is running'

	return 0

def readConfigFile(cfg):
	fin = open(cfg);

	for line in fin:
		# strip \n (well any whitespace) from beginning and end of line
		line = line.rstrip()
		(key, val) = line.split("=")
		if key == "accessId":
			accId = val
		elif key == "secretKey":
			secKey = val
		elif key == "hosts":
			hostArr = val.split(',')

	return accId, secKey, hostArr

# main routine as suggested by Guido von Rossum:
# (http://www.artima.com/weblogs/viewpost.jsp?thread=4829)

class Usage(Exception):
	def __init__(self, msg):
		self.msg = msg

def main(argv=None):


	accId = ""
	secKey = ""
	hostArr = []

	if argv is None:
		argv = sys.argv

	# parse command line arguments
	try:
		try:
			opts, args = getopt.getopt(sys.argv[1:], "h", ["help", "accessId=", "secretKey=", "hosts="])
		except getopt.error, msg:  
			raise Usage(msg)

		# Config file: read if no command line options are read in.
		# TODO: Make chains on configs so that some things can be provided only a file, or can be overriden
		#       by commandline.
		if len(opts) == 0:
			try: 
				accId, secKey, hostArr = readConfigFile(args[0])
			except:
				raise Usage("Please provide either command line options or a config file")
		else:
			# process options
			for o,a in opts:
				if o in ("-h", "--help"):
					print __doc__
					return 0

				if o == "--accessId":
					accId = a
				elif  o == "--secretKey":
					secKey = a
				else:
					hostArr = a.split(',')

		print accId
		print secKey
		print hostArr

		# Now we have options, so make sure that we got good ones, or bail.
		# TODO: Better checks to make sure host names, are legit.  Namely,
		# we need the access info, and at least one host name.
		if accId.__len__() == 0 or secKey.__len__() == 0 or hostArr.__len__() == 0 or hostArr[0].__len__ == 0:
			raise Usage("one or more system parameters missing")

		# process args, but for us there should be no args
		#for arg in args:
		#	process(arg)
		#if len(args) != 0:
		#	raise Usage("args should not be provided")

		poll(accId, secKey, hostArr)

	except Usage, err:
		print >>sys.stderr, err.msg
		print >>sys.stderr, "for help use --help"
		return 2



if __name__ == "__main__":
	sys.exit(main())
