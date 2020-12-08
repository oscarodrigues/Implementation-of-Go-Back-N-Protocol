import socket
import sys
import os
import math
import time
import hashlib
import pickle



#Setup Server
serverAddress=('localhost', 10000)

#UDP client socket
clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
clientSocket.settimeout(10)

print ("Server to Send Data to is as %s on Port %s" % (serverAddress))
#Create Window Variables (Only the Client has to keep track of the Window) This is because of Cumulative Acknowledgment and no Buffer
base=1
nextSeqnum=1
windowSize=7
window = []

#Message to Send
message = 'hello'

#Flag to Set after Transmission is Complete
Done = False

#Time the last Acknowledgement from the server was received
lastackreceived = time.time()

while not Done:
#Check that Done is not set or if the window is empty ("[]" evaluates to false)

	if(nextSeqnum<base+windowSize and nextSeqnum<11):
		#Create packet(Seqnum,Data,Checksum)
		sndpkt = []
		sndpkt.append(nextSeqnum)
		sndpkt.append(message)

		#Create Hash of Packet (The Checksum) And Add it to Packet
		pktHash = hashlib.md5()
		pktHash.update(pickle.dumps(sndpkt))
		sndpkt.append(pktHash.digest())

		#Send the Packet Unless The Packet is Sequence Number 5
		if (nextSeqnum==5 or nextSeqnum==7):
			sndpktCorrupt = sndpkt[:]
			pktHash.update(b"This Hash Will Corrupt Packet")
			sndpktCorrupt[-1] = pktHash.digest()
			clientSocket.sendto(pickle.dumps(sndpktCorrupt),serverAddress)

		else:
			clientSocket.sendto(pickle.dumps(sndpkt),serverAddress)

		#Print out Sequence Number of Packet Sent
		print ("Sending Sequence Number %d" % (nextSeqnum))

		#Increment Variable nextSeqnum
		nextSeqnum = nextSeqnum + 1

		#Append Packet to Window
		window.append(sndpkt)

#Receipt of Acknowledgement from Server
	try:
		packet,server = clientSocket.recvfrom(4096)
		rcvpkt = []
		rcvpkt = pickle.loads(packet)

		#Get Checksum from Received Packet
		checksum = rcvpkt[-1]
		del rcvpkt[-1]

		#Calculate Hash of Packet
		h = hashlib.md5()
		h.update(pickle.dumps(rcvpkt))

		#Check to see if the Hashes Match
		if checksum == h.digest():

			#Check if Done has reached
			if(rcvpkt[0] == 10):
				Endpkt=[]
				Endpkt.append("Close Connection")
				EndHash = hashlib.md5()
				EndHash.update(pickle.dumps(Endpkt))
				Endpkt.append(EndHash.digest())
				clientSocket.sendto(pickle.dumps(Endpkt), serverAddress)
				Done = True
				print("All Packets Have been Sent")

			#Close Connection if Server Requests it
			if (rcvpkt[0]=="Close Connection"):
				break
			#Otherwise Print out Status of Window and Update the Window and Base
			else:
				print ("I just Received %d " % (rcvpkt[0]))
				#print ("I have to Send %d" % (rcvpkt[0]+1))

				#If the Checksum is good we Slide the Window and Reset the Timer
				while rcvpkt[0]>=base and window:
					lastackreceived = time.time()
					del window[0]
					base = base + 1
		else:
			#If the Hashes Don't Match just discard the Packet, the Timeout Will handle this error
			print ("There was an Error in Transmission")

#Timout Event
	except:
		#If the Server isn't Responding with any Acknowledgments Terminate the Connection
		if (time.time()-lastackreceived>20):
			print("Server is Not Responding")
			break

		#If the Server Hasn't Responded in 5 seconds Resend all the Packets in the Window
		elif(time.time()-lastackreceived>5):
			for i in window:
				clientSocket.sendto(pickle.dumps(i), serverAddress)
			print("Did Not Receive Acknowledgement for Packet %d" % (base))
			print("Resending Packets %d through %d" % (base,nextSeqnum-1))
			time.sleep(5)

print ("Connection Closed")
clientSocket.close()
