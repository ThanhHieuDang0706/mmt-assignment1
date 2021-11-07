from tkinter import *
import tkinter.messagebox
from PIL import Image, ImageTk
import socket
import threading
import sys
import traceback
import os

from RtpPacket import RtpPacket

CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"


class Client:
    SETUP_STR = "SETUP"
    PLAY_STR = "PLAY"
    PAUSE_STR = 'PAUSE'
    TEARDOWN_STR = 'TEARDOWN'
    RTSP_VER = "RTSP/1.0"
    TRANSPORT = "RTP/UDP"
    INIT = 0
    READY = 1
    PLAYING = 2
    state = INIT

    SETUP = 0
    PLAY = 1
    PAUSE = 2
    TEARDOWN = 3
    request = ""
    # Initiation..

    def __init__(self, master, serveraddr, serverport, rtpport, filename):
        self.master = master
        self.master.protocol("WM_DELETE_WINDOW", self.handler)
        self.createWidgets()
        self.serverAddr = serveraddr
        self.serverPort = int(serverport)
        self.rtpPort = int(rtpport)
        self.fileName = filename
        self.rtspSeq = 0
        self.sessionId = 0
        self.requestSent = -1
        self.teardownAcked = 0
        self.connectToServer()
        self.frameNbr = 0
        self.RTSP_VER = "RTSP/1.0"
        self.SETUP_STR = "SETUP"
        self.PLAY_STR = "PLAY"
        self.PAUSE_STR = 'PAUSE'
        self.TEARDOWN_STR = 'TEARDOWN'

    # THIS GUI IS JUST FOR REFERENCE ONLY, STUDENTS HAVE TO CREATE THEIR OWN GUI
    def createWidgets(self):
        """Build GUI."""
        # Create Setup button
        self.setup = Button(self.master, width=20, padx=3, pady=3)
        self.setup["text"] = "Setup"
        self.setup["command"] = self.setupMovie
        self.setup.grid(row=1, column=0, padx=2, pady=2)

        # Create Play button
        self.start = Button(self.master, width=20, padx=3, pady=3)
        self.start["text"] = "Play"
        self.start["command"] = self.playMovie
        self.start.grid(row=1, column=1, padx=2, pady=2)

        # Create Pause button
        self.pause = Button(self.master, width=20, padx=3, pady=3)
        self.pause["text"] = "Pause"
        self.pause["command"] = self.pauseMovie
        self.pause.grid(row=1, column=2, padx=2, pady=2)

        # Create Teardown button
        self.teardown = Button(self.master, width=20, padx=3, pady=3)
        self.teardown["text"] = "Teardown"
        self.teardown["command"] = self.exitClient
        self.teardown.grid(row=1, column=3, padx=2, pady=2)

        # Create a label to display the movie
        self.label = Label(self.master, height=19)
        self.label.grid(row=0, column=0, columnspan=4,
                        sticky=W+E+N+S, padx=5, pady=5)

    def setupMovie(self):
        """Setup button handler."""
    # TODO

    def exitClient(self):
        """Teardown button handler."""
    # TODO

    def pauseMovie(self):
        """Pause button handler."""
    # TODO

    def playMovie(self):
        """Play button handler."""
    # TODO

    def listenRtp(self):
        """Listen for RTP packets."""
        # TODO

    def writeFrame(self, data):
        """Write the received frame to a temp image file. Return the image file."""
    # TODO

    def updateMovie(self, imageFile):
        """Update the image file as video frame in the GUI."""
    # TODO

    def connectToServer(self):
        """Connect to the Server. Start a new RTSP/TCP session."""
    # TODO

    def sendRtspRequest(self, requestCode):
        """Send RTSP request to the server."""
        # -------------
        # TO COMPLETE
        # -------------
        # check the request code
        # request code == SETUP
        # request =
        # C: SETUP movie.Mjpeg RTSP/1.0
        # C: CSeq: 1
        # C: Transport: RTP/UDP; client_port= 25000
        if requestCode == self.SETUP and self.state == self.INIT:
            threading.Thread(target=self.recvRtspReply).start()
            # Update RTSP sequence number.
            # RTSP Sequence number starts at 1
            self.rtspSeq = 1
            # Write the RTSP request to be sent.
            # request = requestCode + movie file name + RTSP sequence number + Type of RTSP/Type of RTP + RTP port
            request = "SETUP" + self.fileName + "\n" + \
                str(self.rtspSeq) + "\n" + \
                " RTSP/1.0 RTP/UDP " + str(self.rtpPort)
            self.rtspSocket.send(request)
            # Keep track of the sent request.
            # self.requestSent = SETUP
            self.requestSent = self.SETUP
        # Play request
        elif requestCode == self.PLAY and self.state == self.READY:
            # Update RTSP sequence number.
            # RTSP sequence number increments up by 1
            self.rtspSeq = self.rtspSeq + 1
            # Write the RTSP request to be sent.
            # Must inster the Session header and use the session ID returned in the SETUP response.
            # Must not put the transport header in this request
            # request = PLAY + RTSP sequence
            request = "PLAY" + "\n" + str(self.rtspSeq)
            self.rtspSocket.send(request)
            # Keep track of the sent request.
            # self.requestSent = ...
            self.requestSent = self.PLAY
        # Pause request
        elif requestCode == self.PAUSE and self.state == self.PLAYING:
            # Update RTSP sequence number.
            # ...
            self.rtspSeq = self.rtspSeq + 1
            # Write the RTSP request to be sent.
            # request = ...
            request = "PAUSE" + "\n" + str(self.rtspSeq)
            self.rtspSocket.send(request)
            # Keep track of the sent request.
            # self.requestSent = ...
            self.requestSent = self.PAUSE
        # Teardown request
        elif requestCode == self.TEARDOWN and not self.state == self.INIT:
            # Update RTSP sequence number.
            # ...
            self.rtspSeq = self.rtspSeq + 1
            # Write the RTSP request to be sent.
            # request = ...
            request = "TEARDOWN" + "\n" + str(self.rtspSeq)
            self.rtspSocket.send(request)
            # Keep track of the sent request.
            # self.requestSent = ...
            self.requestSent = self.TEARDOWN
        else:
            return

        print('\nData sent:\n' + request)

    def recvRtspReply(self):
        """Receive RTSP reply from the server."""
        # TODO
        while True:
            reply = self.rtspSocket.recv(1024)

            if reply:
                self.parseRtspReply(reply.decode("utf-8"))

            # Close the RTSP socket upon requesting Teardown
            if self.requestSent == self.TEARDOWN:
                self.rtspSocket.shutdown(socket.SHUT_RDWR)
                self.rtspSocket.close()
                break

    def parseRtspReply(self, data):
        # """Parse the RTSP reply from the server."""
        # TODO
        lines = data.split('\n')
        seqNum = int(lines[1].split(' ')[1])
        if int(seqNum) == 200:
            if self.requestSent == self.SETUP:
                self.state = self.READY
                self.openRtpPort()
            elif self.requestSent == self.PLAY:
                self.state = self.PLAYING
            elif self.requestSent == self.PAUSE:
                self.state = self.READY
                self.playEvent.set()
            elif self.requestSent == self.TEARDOWN:
                self.state = self.INIT
                # flag to close socket
                self.teardownAcked = 1

    def openRtpPort(self):
        # """Open RTP socket binded to a specified port."""
        # -------------
        # TO COMPLETE
        # -------------
        # Create a new datagram socket to receive RTP packets from the server
        # self.rtpSocket = ...

        # Set the timeout value of the socket to 0.5sec
        # ...
        self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.rtpSocket.settimeout(0.5)

        try:
            # Bind the socket to the address using the RTP port given by the client user
            # ...
            self.rtpSocket.bind((self.serverAddr, self.rtpPort))
        except:
            tkinter.messagebox.showwarning(
                'Unable to Bind', 'Unable to bind PORT=%d' % self.rtpPort)

    def handler(self):
        #"""Handler on explicitly closing the GUI window."""
        # TODO
        self.pauseMovie()
        if tkinter.messagebox.askokcancel("Quit?", "Are you sure you want to quit?"):
            self.exitClient()
        else:  # When the user presses cancel, resume playing.
            self.playMovie()
