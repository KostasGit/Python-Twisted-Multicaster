#K. Beroukas kns_29ber@hotmail.com collaboration with A.Xinogala
import optparse
import re
from twisted.internet.protocol import Protocol, ClientFactory
from twisted.internet import reactor
import time
counterMsg = 0
timeStamp = "0.0"
lamportClock=0
messagesList = []
ackList =[]
delivered_messages =[]

def parse_args():
	usage = """usage: %prog [options] [0|1|2] [hostname]:port

	python peer.py 0 127.0.0.1:port """

	parser = optparse.OptionParser(usage)

	_, args = parser.parse_args()

	if len(args) != 2:
		print parser.format_help()
		parser.exit()

	serial_process_num, addresses = args

	def parse_address(addr):
		if ':' not in addr:
			host = '127.0.0.1'
			port = addr
		else:
			host, port = addr.split(':', 1)

		if not port.isdigit():
			parser.error('Ports must be integers.')

		return host, int(port)

	return serial_process_num, parse_address(addresses)

def split_string(list):
	extracted_numbers=re.findall(r"[-+]?\d*\.\d+|\d+", list)
	return extracted_numbers
			
def sort(message,processID,lamClock) :
	global messagesList 
	for index,line in enumerate(messagesList) :
		tempList = split_string(line)
		otherProcessID, otherlamClock = tempList[1].split('.',1)
		if lamClock < int(otherlamClock) :
			messagesList.insert(index,message)
			return
		elif lamClock == int(otherlamClock) and processID < int(otherProcessID):
			messagesList.insert(index,message)
			return
	messagesList.append(message)
				

def deliveredMsg():
	global ackList,messagesList,delivered_messages
	counterAck =0
	point = ''
	tempList = split_string(messagesList[0])
	numberMsg = tempList[0]
	processID, timeStampMsg = tempList[1].split('.',1)
	if processID=='0':
		processID='Zero'
	elif processID=='1':
		processID= 'First'
	else:
		processID= 'Second'
	for index,line in enumerate(ackList) :
		if line.find(processID) != -1 and line.find(numberMsg +',') : #kanei delivered_messages tou self.pt
			counterAck=counterAck+1
			if counterAck == 1:
				point = ackList[index]
			if counterAck == 2 :
				message=messagesList[0]
				delivered_messages.append(message)
				messagesList.remove(message)
				ackList.remove(point)
				ackList.remove(line)
				break

class Peer(Protocol):
	global counterMsg,timeStamp,lamportClock
	acks = 0
	connected = False

	def __init__(self, factory, serial_process_num):
		self.pt = serial_process_num
		self.factory = factory
	
	def connectionMade(self):
		self.factory.clients.append(self)
		self.connected = True
		reactor.callLater(3, self.sendUpdate)
	
	def sendUpdate(self):
		global counterMsg,timeStamp,lamportClock
		print "Sending update" + str(counterMsg)
		try:
			timeStamp= self.pt + '.' + str(lamportClock)
			message= '< msgNum:'+str(counterMsg)+',Clock:'+timeStamp+'>'
			sort(message,int(self.pt),int(lamportClock)) 
			for client in self.factory.clients:
				client.transport.write(message)
				lamportClock = lamportClock + 1
				timeStamp= self.pt + '.' + str(lamportClock)
				message= '< msgNum:'+str(counterMsg)+',Clock:'+timeStamp+'>'
			counterMsg = counterMsg+1
		except Exception, ex1:
			print "Exception trying to send: ", ex1.args[0]
		if self.connected == True and counterMsg < 20 :
			reactor.callLater(3, self.sendUpdate)

	def sendAck(self,numberMsg,processID):
		global timeStamp,lamportClock
		print "sendAck"
		try:
			for client in self.factory.clients:
				timeStamp=  self.pt + '.' + str(lamportClock)
				if processID == '0':
					ack='<Zero : Ack number is :'+ numberMsg +',Lamport Clock:'+timeStamp+'>'
				elif processID == '1':
					ack='<First : Ack number is :'+ numberMsg +',Lamport Clock:'+timeStamp+'>'
				else :
					ack ='<Second : Ack number is :'+ numberMsg +',Lamport Clock:'+timeStamp+'>'
				client.transport.write(ack)
				lamportClock = lamportClock + 1
		except Exception, e:
			print e.args[0]

	def dataReceived(self, data):
		global counterMsg,timeStamp,lamportClock,messagesList,ackList
		temp_list = data.split(">")
		for line in temp_list: 
			temp_list2 = split_string(line)
			if len(temp_list2)!=0 :		#auto ginetai gt erxetai mia kenh apo to split_string
				numberMsg =temp_list2[0]
				otherTimestamp=temp_list2[1]
				processID,otherLamportClock = otherTimestamp.split('.',1)
				if int(otherLamportClock) >= lamportClock :
					lamportClock = int(otherLamportClock) + 1
				if line.find('Ack') == -1:
					sort(line,int(processID),int(otherLamportClock))
					self.sendAck(numberMsg,processID)
					self.acks += 1
				else:
					ackList.append(line)
					deliveredMsg()

	def connectionLost(self, reason):
		self.factory.clients.remove(self)
		print "Disconnected"
		self.connected = False
		if self.pt == '0':
			with open("delivered-messages-0.txt", "w") as f:
				for line in delivered_messages:
					print>>f, line
				
		elif self.pt == '1':
			with open("delivered-messages-1.txt", "w") as f:
				for line in delivered_messages:
					print>>f, line
			
		else:
			with open("delivered-messages-2", "w") as f:
				for line in delivered_messages:
					print>>f, line	
		self.done()
			
	def done(self):
		self.factory.finished(self.acks)


class PeerFactory(ClientFactory):
	def __init__(self, serial_process_num, fname):
		print '@__init__'
		self.clients = []
		self.pt = serial_process_num
		self.acks = 0
		self.fname = fname

	def finished(self, arg):
		self.acks = arg
		self.report()

	def report(self):
		print 'Received %d acks' % self.acks

	def clientConnectionFailed(self, connector, reason):
		print 'Failed to connect to:', connector.getDestination()
		self.finished(0)

	def clientConnectionLost(self, connector, reason):
		print 'Lost connection.  Reason:', reason

	def startFactory(self):
		print "@startFactory"
		

	def stopFactory(self):
		print "@stopFactory"


	def buildProtocol(self, addr):
		print "@buildProtocol"
		protocol = Peer(self, self.pt)
		return protocol


if __name__ == '__main__':
	serial_process_num, address = parse_args()
	if serial_process_num == '0':
		factory = PeerFactory('0', 'log')
		reactor.listenTCP(address[1], factory)
		print "Process 0 is listening @" + address[0] + " port " + str(address[1])
	elif serial_process_num == '1':
		factory = PeerFactory('1', '')
		host, port = address
		print "Connecting to process 0 " + host + " port " + str(port)
		reactor.connectTCP(host, port, factory)
		print "Process 1 is listening @" + address[0] + " port " + str(address[1]+1)
		reactor.listenTCP(port+1, factory)
	else:
		factory = PeerFactory('2', '')
		host, port = address
		print "Connecting to process 0 " + host + " port " + str(port)
		reactor.connectTCP(host, port, factory)
		print "Connecting to process 1 " + host + " port " + str(port+1)
		reactor.connectTCP(host, port+1, factory)
                
	reactor.run()
