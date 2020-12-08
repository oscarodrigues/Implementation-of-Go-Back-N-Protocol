import socket
import sys
import os
import math
import time
import hashlib
import pickle

# Define and Create Server Socket
server_address = ('localhost', 10000)
serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
clientAddress = ()

# Bind IP Address and Port to a Socket
serverSocket.bind(server_address)
serverSocket.settimeout(25)
print ("Starting up on %s Port %s" % (server_address))

# Server Variables (The Server Only Needs to Compare Recieved SequenceNum with Expected Sequence Number)
expectedseqnum = 1

# All the Acknoledged Packets
Output = []

# Flag for When the Transmission is Done
Done = False

# Received Data Event
lastpktreceived = time.time()
starttime = time.time()

while not Done:
    try:
        packet, clientAddress = serverSocket.recvfrom(4096)
        rcvpkt = []
        rcvpkt = pickle.loads(packet)

        ''' First We Check the Checksum to Make Sure the Packet wasn't Modified During Transmission 
        (There is no reason to check the sequence numbers if the packet was corrupted) '''
        Checksum = rcvpkt[-1]
        del rcvpkt[-1]

        RcvHash = hashlib.md5()
        RcvHash.update(pickle.dumps(rcvpkt))

        # If Checksums match then we check sequence numbers
        if Checksum == RcvHash.digest():
            # Check is Sequence Number Received equals Expected Sequence Number
            if (rcvpkt[0] == expectedseqnum):

                print ("Received Packet %d from %s it has %d bytes" % (
                rcvpkt[0], clientAddress, len(packet)))

                # If the Sequence Numbers Match Add the Data of the Received Packet to the final "Output" List
                Output.append(rcvpkt[1])

                # Create ACK When we Received A Good Packet ACK Format: (Seqnum,Checksum)
                sndpkt = []
                sndpkt.append(expectedseqnum)
                sndHash = hashlib.md5()
                sndHash.update(pickle.dumps(sndpkt))
                sndpkt.append(sndHash.digest())
                serverSocket.sendto(pickle.dumps(sndpkt), clientAddress)
                print ("Sending Ack for %d" % (expectedseqnum))

                '''Always Increment Expected Sequece Number when a good packet is recieved 
                (Good Packet meaning not corrupt and its sequence number matches the expected one)'''
                expectedseqnum = expectedseqnum + 1

                # Reset the time for the last packet received
                lastpktreceived = time.time()

            elif (rcvpkt[0] == "Close Connection"):
                print ("Connection Closed by Client")
                Done = True
                break

            else:
                # If the Packet Sequence Numbers Don't Mactch
                print (
                            "Received Out of Order, I recieved %d I was Expecting %d" % (
                    rcvpkt[0], expectedseqnum))
                Errpkt = []
                Errpkt.append(expectedseqnum - 1)
                h = hashlib.md5()
                h.update(pickle.dumps(Errpkt))
                Errpkt.append(h.digest())
                serverSocket.sendto(pickle.dumps(Errpkt), clientAddress)
                print ("Sent ACK for Last Received Packet: %d" % (
                            expectedseqnum - 1))
        else:
            print ("Error in Transmission: The Checksums Don't Match")
    except:
        # If the last packet received was more than 10 seconds ago end the connection
        if (time.time() - lastpktreceived > 10 and len(clientAddress) != 0):
            Endpkt = []
            Endpkt.append("Close Connection")
            EndHash = hashlib.md5()
            EndHash.update(pickle.dumps(Endpkt))
            Endpkt.append(EndHash.digest())
            serverSocket.sendto(pickle.dumps(Endpkt), clientAddress)
            print ("Connection Ended, Sent Close Conneciton Packet to Client")
            break
        elif (time.time() - lastpktreceived > 50):
            print ("Not Receiving any Transmisisons, Connection Closed")
            break

endtime = time.time()
print ("The Final Output is %s" % (Output))