import sys
from tkinter import Tk
from Client import Client
from RtpPacket import RtpPacket

if __name__ == "__main__":
	try:
		serverAddr = sys.argv[1]
		serverPort = sys.argv[2]
		rtpPort = sys.argv[3]
		fileName = sys.argv[4]	
	except:
		print("[Usage: ClientLauncher.py Server_name Server_port RTP_port Video_file]\n")	
	
	root = Tk()
	

	#  test rtp
	rt = RtpPacket()
	rt.encode(1,2,3,4,5,0,7,8,9)
	print(rt.seqNum())

	# Create a new client
	app = Client(root, serverAddr, serverPort, rtpPort, fileName)
	app.master.title("RTPClient")	
	root.mainloop()
	