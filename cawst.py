#!/usr/bin/env python


"""

cawst.py --acccessId=X --secretKey=Y --hosts=Z | -h | --help

-h | --help => print this usage messages

X = 

Y =

Z = comma delimited list of short hostnames (eg, web1,db1)


"""

# TODO: Better Unit Tests.

import sys
import getopt


from boto.ec2.connection import EC2Connection


def poll(accId, secKey, hostArr ):

	# TODO: Error checking?
	conn = EC2Connection(accId, secKey)

	# TODO: config file items
	ami = "ami-31814f58"
	ssh = "cawst"
	instance = "m1.small"
	secGroup = "cawst"

	for host in hostArr:
		conn.run_instances(
			ami,
			key_name = ssh,
			instance_type = instance,
			security_groups = [secGroup])

	return 0

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

		# Config file(?)
		#if len(opts) == 0:
		#	readConfigFile();

		# TODO: Make chains on configs so that some things can be provided only a file, or can be overriden
		#       by commandline.

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


		# Now we have options, so make sure that we got good ones, or bail.
		# TODO: Better checks to make sure host names, are legit.  Namely,
		# we need the access info, and at least one host name.
		if accId.__len__() == 0 or secKey.__len__() == 0 or hostArr.__len__() == 0 or hostArr[0].__len__ == 0:
			raise Usage("one or more system parameters missing")

		# process args, but for us there should be no args
		#for arg in args:
		#	process(arg)
		if len(args) != 0:
			raise Usage("args should not be provided")

		poll(accId, secKey, hostArr)

	except Usage, err:
		print >>sys.stderr, err.msg
		print >>sys.stderr, "for help use --help"
		return 2



if __name__ == "__main__":
	sys.exit(main())
