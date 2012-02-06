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
import random
import time


from boto.ec2.connection import EC2Connection


class Host:
	def __init__(self,name,instance = None):
		self.name = name

		if instance is not None:
			self.instance = instance

	def getPublicDNS(self):
		return self.instance.public_dns_name

	def getPrivateDNS(self):
		return self.instance.private_dns_name

	def getPrivateIP(self):
		return self.instance.private_ip_address

	def getState(self):
		return self.instance.update() 

def getConn(accId, secKey):
	return  EC2Connection(accId, secKey)

def startMachine(conn, host):
	# TODO: config file items
	# TODO: make key be dynamic, and upload with import_key_pair
	ami = "ami-31814f58"
	ssh = "cawst"
	instance = "m1.small"
	secGroup = "cawst"
	# make this unique so that we have a way to check a host.  Need to look
	# at host data which we can set via the web, and determine how to  set it
	# with boto.
	token = host + "-" + random.random().__str__()

	reservation  = conn.run_instances(
		ami,
		key_name = ssh,
		instance_type = instance,
		security_groups = [secGroup],
		client_token = token)

	return reservation.instances[0]

def getRunningInstances(conn):

	running = 0
	hosts = dict()
	reservations = conn.get_all_instances()

	for resv in reservations:
		instances = resv.instances
		for inst in instances:
			# TODO: Check also for pending.
			if inst.update() == "running":
				token = inst.client_token
				name =  token.split('-')[0]
				host = Host(name,inst)
				hosts[name] = host

	return hosts

# instance variables are:
#{'kernel': u'aki-805ea7e9', 'root_device_type': u'ebs', 'private_dns_name': '', 'previous_state': None, 'spot_instance_request_id': None, 'hypervisor': u'xen', 'id': u'i-afc747ca', 'state_reason': {u'message': u'pending', u'code': u'pending'}, 'monitored': False, 'item': u'\n        ', 'subnet_id': None, 'block_device_mapping': {}, 'instance_class': None, 'shutdown_state': None, 'group_name': None, 'state': u'pending', 'client_token': '', '_in_monitoring_element': False, 'architecture': u'i386', 'ramdisk': None, 'virtualizationType': u'paravirtual', 'tags': {}, 'key_name': u'cawst', 'image_id': u'ami-31814f58', 'reason': '', 'groups': [<boto.ec2.instance.Group instance at 0xed78638>], 'public_dns_name': '', 'monitoring': u'\n            ', 'requester_id': None, 'state_code': 0, 'ip_address': None, 'placement': u'us-east-1b', 'ami_launch_index': u'0', 'dns_name': '', 'region': RegionInfo:us-east-1, 'launch_time': u'2012-02-05T16:44:12.000Z', 'persistent': False, 'instance_type': u'm1.small', 'connection': EC2Connection:ec2.amazonaws.com, 'root_device_name': u'/dev/sda1', 'instanceState': u'\n            ', 'private_ip_address': None, 'vpc_id': None, 'product_codes': []}

def hostExistsInAWS(conn,host):
	hdict = dict([('client_token',host)])

	return conn.get_all_instances(instance_ids=None, filters=hdict)

def poll(accId, secKey, hostArr ):
	# TODO:  Still Error Checking 
	conn =  getConn(accId,secKey)
	hQueue = list()

	runningMachines = getRunningInstances(conn)

	for hname in hostArr:
		if hname not in runningMachines:
			print hname + " is not running, so I will start it."
			inst = startMachine(conn,hname)
			host = Host(hname,inst)
			runningMachines[hname] = host 
			hQueue.append(host)

	if hQueue.__len__() != 0:
		print "sleeping 30 seconds to give new hosts time to spin up"
		time.sleep(60)

	# check one last time.
	while hQueue.__len__() != 0:
		host = hQueue.pop()
		print "checking on last time.  Is %s up?" % host.name
		if host.getState() != "running":
			print "No!  Please wait and re-run script"
			return
		else: 
			print "Yes!  Ready to continue"

		

	# Now loop over machines to do things with them.
	for h in runningMachines.values():
		print h.getState()
		print h.getPublicDNS()
		print h.getPrivateDNS()
		print h.getPrivateIP()

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
