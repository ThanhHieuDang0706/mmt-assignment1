from tkinter import *
import tkinter.messagebox
from PIL import Image, ImageTk
import socket
import threading
import sys
import traceback
import os
import time
from RtpPacket import RtpPacket

CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"


class Client:
    INIT = 0
    READY = 1
    PLAYING = 2
    state = INIT

    SETUP = 0
    PLAY = 1
    PAUSE = 2
    TEARDOWN = 3
    DESCRIBE = 4

    RECV_LEN = 20480
    COUNT = 0
    TOTALLOSSPACKET = 0
    TOTALSIZE = 0
    PASTSTOP = 0
    TIMEEND = 0
    TIMESTART = 0

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
        self.frameNumber = 0
        self.TIMESTART = time.time()
    # THIS GUI IS JUST FOR REFERENCE ONLY, STUDENTS HAVE TO CREATE THEIR OWN GUI

    def createWidgets(self):
        """Build GUI."""
        # Create Setup button
        self.setup = Button(self.master, width=20, padx=3, pady=3)
        self.setup["text"] = "Thiết lập"
        self.setup["command"] = self.setupMovie
        self.setup.grid(row=1, column=0, padx=2, pady=2)

        # Create Play button
        self.start = Button(self.master, width=20, padx=3, pady=3)
        self.start["text"] = "Bắt đầu"
        self.start["command"] = self.playMovie
        self.start.grid(row=1, column=1, padx=2, pady=2)

        # Create Pause button
        self.pause = Button(self.master, width=20, padx=3, pady=3)
        self.pause["text"] = "Tạm ngưng"
        self.pause["command"] = self.pauseMovie
        self.pause.grid(row=1, column=2, padx=2, pady=2)

        # Create Teardown button
        self.teardown = Button(self.master, width=20, padx=3, pady=3)
        self.teardown["text"] = "Kết thúc"
        self.teardown["command"] = self.exitClient
        self.teardown.grid(row=1, column=3, padx=2, pady=2)

        self.desc = Button(self.master, width=20, padx=3, pady=3)
        self.desc["text"] = "Mô tả"
        self.desc["command"] = self.descHandler
        self.desc.grid(row=1, column=4, padx=2, pady=2)

        # Create a label to display the movie
        self.label = Label(self.master, height=19)
        self.label.grid(row=0, column=0, columnspan=4,
                        sticky=W+E+N+S, padx=5, pady=5)

    def setupMovie(self):
        """Setup button handler."""
        if self.state == self.INIT:
            self.sendRtspRequest(self.SETUP)
            # Gray button
            # self.setup["state"] = "disabled"

    def exitClient(self):
        """Teardown button handler."""
        if self.state != self.INIT:
            self.sendRtspRequest(self.TEARDOWN)
        # Close window
            if self.TIMEEND == 0:
                self.TIMEEND = time.time()
                # print("TIMEEND: " + str(self.TIMEEND))
                print("Rate loss packet: " + str((float(self.TOTALLOSSPACKET) /
                                                  float(self.COUNT))))
                print("Video Data Rate: " + str(round(float(self.TOTALSIZE) /
                                                      float(self.TIMEEND - self.TIMESTART), 2)) + "Bytes/s")
        self.master.destroy()
        cache_file = os.path.join(
            CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT)
        # Delete cache.

        os.remove(cache_file)

    def pauseMovie(self):
        """Pause button handler."""
        # if self.state != self.READY:
        #	tkinter.messagebox.showinfo("Bạn chưa thiết lập!")
        # else:
        if self.state == self.PLAYING:
            self.sendRtspRequest(self.PAUSE)

    def playMovie(self):
        """Play button handler."""
        if self.state != self.READY:
            tkinter.messagebox.showinfo("Bạn chưa thiết lập!")
        else:
            threading.Thread(target=self.listenRtp).start()
            self.playing = threading.Event()
            self.playing.clear()
            self.sendRtspRequest(self.PLAY)

    def descHandler(self):
        print("desc")
        self.sendRtspRequest(self.DESCRIBE)

    def listenRtp(self):
        """Listen for RTP packets."""
        while True:
            try:
                data = self.rtpSocket.recv(self.RECV_LEN)
                # print(str(data),data)
                if not data:
                    tkinter.messagebox.showerror("Có gì đó không ổn.")
                else:
                    packet = RtpPacket()
                    packet.decode(data)
                    self.TOTALSIZE += len(data)
                    # print(self.TOTALSIZE)
                    # print("Data length: " + self.TOTALSIZE)
                    currentFrameNumber = packet.seqNum()
                    self.COUNT += 1

                    if (self.COUNT != self.frameNumber + 1):
                        self.TOTALLOSSPACKET += 1
                        self.COUNT = currentFrameNumber
                        print("LOST PACKET")
                    print(f"seq: {currentFrameNumber}")

                    if currentFrameNumber > self.frameNumber:
                        # Ignore late

                        self.frameNumber = currentFrameNumber
                        self.updateMovie(self.writeFrame(packet.getPayload()))
            except:
                if self.playing.is_set():
                    if self.TIMEEND == 0:
                        self.TIMEEND = time.time()
                    # print("TIMEEND: " + str(self.TIMEEND))
                    print("Rate loss packet: " + str((float(self.TOTALLOSSPACKET) /
                          float(self.COUNT))))
                    print("Video Data Rate: " + str(round(float(self.TOTALSIZE) /
                          float(self.TIMEEND - self.TIMESTART), 2)) + "Bytes/s")
                    self.PASTSTOP = self.COUNT
                    # self.TOTALLOSSPACKET = 0
                    self.TIMESTART = self.TIMEEND
                    self.TIMEEND = 0
                    self.TOTALSIZE = 0

                    break

                if self.teardownAcked == 1:
                    self.rtpSocket.shutdown(socket.SHUT_RDWR)
                    self.rtpSocket.close()
                    break

    def writeFrame(self, data):
        """Write the received frame to a temp image file. Return the image file."""
        cache_file = os.path.join(
            CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT)
        try:
            with open(cache_file, 'wb') as file:
                file.write(data)
        except:
            tkinter.messagebox.showerror("lỗi", "Lỗi viết file.")
        return cache_file

    def updateMovie(self, imageFile):
        """Update the image file as video frame in the GUI."""
        try:
            pic = ImageTk.PhotoImage(Image.open(imageFile))
            self.label.configure(image=pic, height=288)
            self.label.image = pic
        except:
            tkinter.messagebox.showerror("lỗi", "Không thể mở hình")

    def connectToServer(self):
        """Connect to the Server. Start a new RTSP/TCP session."""
        self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.rtspSocket.connect((self.serverAddr, self.serverPort))
        except:
            tkinter.messagebox.showerror(
                "lỗi", f"Kết nối tới {self.serverAddr} thất bại.")

    def sendRtspRequest(self, requestCode):
        """Send RTSP request to the server."""
        # -------------
        # TO COMPLETE
        # -------------

        print("REQUEST SENT:", requestCode)

        if requestCode == self.SETUP:
            if self.state != self.INIT:
                tkinter.messagebox.showerror("lỗi", "movie đang chạy")
                return
            threading.Thread(target=self.recvRtspReply).start()
            self.rtspSeq = 1
            request = "SETUP " + self.fileName + "\nCSeq: " + \
                str(self.rtspSeq) + "\n" + \
                f"Transport: RTP/UDP; client_port= {self.rtpPort}"
            print(request.encode())
            self.rtspSocket.send(request.encode())
            self.requestSent = self.SETUP

        elif requestCode == self.PLAY:
            if self.state != self.READY:
                tkinter.messagebox.showerror("Chưa sẵn sàng")
                return
            self.rtspSeq += 1
            request = "PLAY " + "\nCseq: " + \
                str(self.rtspSeq) + "\n" + f"Session: {self.sessionId}"
            print(request)
            self.rtspSocket.send(request.encode())
            self.requestSent = self.PLAY

        elif requestCode == self.PAUSE:
            # if self.state != self.PLAYING:
            #	return
            self.rtspSeq += 1
            request = "PAUSE " + "\nCseq: " + \
                str(self.rtspSeq) + "\n" + f"Session: {self.sessionId}"
            print(request)
            self.rtspSocket.send(request.encode())
            self.requestSent = self.PAUSE

        elif requestCode == self.TEARDOWN:
            if self.state == self.INIT:
                return
            self.rtspSeq += 1
            request = "TEARDOWN " + "\nCseq: " + \
                str(self.rtspSeq) + "\n" + f"Session: {self.sessionId}"
            self.rtspSocket.send(request.encode())

            self.requestSent = self.TEARDOWN

        elif requestCode == self.DESCRIBE:
            self.rtspSeq += 1
            request = "DESCRIBE " + "\nCseq: " + \
                str(self.rtspSeq) + "\n" + f"Session: {self.sessionId}"
            self.rtspSocket.send(request.encode())

            self.requestSent = self.DESCRIBE

    def recvRtspReply(self):
        """Receive RTSP reply from the server."""
        while True:
            reply = self.rtspSocket.recv(1024)

            if reply:
                self.parseRtspReply(reply)

            if self.requestSent == self.TEARDOWN:
                self.rtspSocket.shutdown(socket.SHUT_RDWR)
                self.rtspSocket.close()
                break

    def parseRtspReply(self, data):
        """Parse the RTSP reply from the server."""
        print()
        print("parse data ", data)
        print("\n\n", data)
        data = data.decode()

        data = str(data).split('\n')

        if "Frame" in data[2]:
            tkinter.messagebox.showinfo("describe", data[2:])
            return

        print(data)

        sequence_number = int(data[1].split()[1])

        if sequence_number == self.rtspSeq:
            session = int(data[2].split()[1])
            if self.sessionId == 0:
                self.sessionId = session  # todooooooooo
            if self.sessionId == session:
                code = int(data[0].split()[1])
                if code == 200:
                    if self.requestSent == self.SETUP:
                        self.state = self.READY
                        self.openRtpPort()
                    elif self.requestSent == self.PLAY:
                        self.state = self.PLAYING

                    elif self.requestSent == self.PAUSE:
                        self.state = self.READY
                        self.playing.set()
                    elif self.requestSent == self.TEARDOWN:
                        self.state = self.INIT
                        self.teardownAcked = 1
                    elif self.requestSent == self.DESCRIBE:
                        tkinter.messagebox.showinfo(data)

    def openRtpPort(self):
        """Open RTP socket binded to a specified port."""
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
            self.state = self.READY
            self.rtpSocket.bind(('', self.rtpPort))
        except:
            tkinter.messagebox.showwarning(
                'Fail', 'PORT=%d không thể bind' % self.rtpPort)

    def handler(self):
        """Handler on explicitly closing the GUI window."""
        self.pauseMovie()
        if tkinter.messagebox.askokcancel("Exiting", " Bạn có muốn thoát?"):
            self.exitClient()
        else:
            self.playMovie()
