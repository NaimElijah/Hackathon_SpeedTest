import threading, time, struct, sys, random
from socket import *
#*                ====================>>>>            Team Name:   "The United Front" / "The Speed Testing Association"            <<<<====================

# global variables
serverName = "servername"
serverPort = 12000
BroadcastIP = "255.255.255.255"
# setting up UDPserverSocket
UDPserverSocket = socket(AF_INET, SOCK_DGRAM)  # UDP from lecture
UDPserverSocket.bind(('',serverPort))  # UDP from lecture
# setting up TCPserverSocket
TCPserverSocket = socket(AF_INET, SOCK_STREAM)  # TCP from lecture
TCPserverSocket.bind(("", serverPort))  # TCP from lecture

def main():

    # The server is also a multi-threaded app - it constantly sends offer messages in one thread
    ListeningThread = threading.Thread(target=Request_Listening, args=())  #  see if args are needed here
    OfferingThread = threading.Thread(target=offering, args=())  #  see if args are needed here
    
    ListeningThread.start()
    OfferingThread.start()

    # and launches a new thread to handle each incoming speed test request (either UDP or TCP).
    ###############################################################################################   TTTCP
    while True:
        TCPserverSocket.listen(1) # put this line in the right place     # TCP from lecture
        connectionSocket, addr = TCPserverSocket.accept()

        sentence = connectionSocket.recv(1024)
        Processed_Sentence = sentence.upper()  #TODO:  <<<=========  do something with the received packet and return an appropriate packet
        connectionSocket.send(Processed_Sentence)
        connectionSocket.close()  # this line probably needs to be somewhere else maybe

    ###############################################################################################   TTTCP
    #TODO: start a thread for each incoming request.


    # end of main
    OfferingThread.join()  # won't get here because the threads run infinitly



if __name__ == "__main__":
    main()



def offering():   # send UDP offer every second, probably need to broadcast with address 255.255.255.255
    while True:
        # send offer
        Offer_Packet  #TODO: make the offer_Packet accordingly   <<==================
        UDPserverSocket.sendto(Offer_Packet, BroadcastIP)
        time.sleep(1)


def Request_Listening():  #  listening to UDP request
    # create a server socket or something like that so we can hear through that
    while True:   # always listen and create thread for each request heard
        message, clientAddress = UDPserverSocket.recvfrom(2048)  # ListeningThread waiting for request and getting it when it arrives

        # if request received, create a thread to take care of that request
        # do something..
        modifiedMessage = message.upper()  #TODO:   <<<<=================   do something with the message received and make the packet that is needed to be sent
        UDPserverSocket.sendto(modifiedMessage, clientAddress)



def thread_sending_data():
    # make an array of the data parts to send and send each one using the current thread
    return



















#  a class way:


class SpeedTestServer:
    def __init__(self):
        self.udp_port = random.randint(20000, 30000)
        self.tcp_port = random.randint(30001, 40000)
        self.magic_cookie = 0xabcddcba
        self.running = True

    def send_offers(self):
        """Send periodic UDP offer messages to announce server availability."""
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            print(f"Server started, listening on UDP port {self.udp_port}, TCP port {self.tcp_port}")
            
            offer_packet = struct.pack("!IBHH", self.magic_cookie, 0x2, self.udp_port, self.tcp_port)
            
            while self.running:
                sock.sendto(offer_packet, ("<broadcast>", 13117))
                time.sleep(1)  # Send offer every second

    def handle_tcp_request(self, conn, addr):
        """Handle TCP file size requests."""
        try:
            data = conn.recv(1024).decode().strip()
            file_size = int(data)
            print(f"TCP request from {addr}, file size: {file_size} bytes")

            # Simulate sending the file
            bytes_sent = 0
            while bytes_sent < file_size:
                chunk_size = min(4096, file_size - bytes_sent)
                conn.send(b"x" * chunk_size)
                bytes_sent += chunk_size
            
            print(f"TCP transfer to {addr} completed")
        except Exception as e:
            print(f"Error handling TCP request from {addr}: {e}")
        finally:
            conn.close()

    def handle_udp_request(self, sock, addr, file_size):
        """Handle UDP file size requests."""
        try:
            print(f"UDP request from {addr}, file size: {file_size} bytes")

            # Simulate sending data in UDP packets
            total_segments = (file_size + 1023) // 1024
            for segment in range(total_segments):
                packet = struct.pack("!IBQQ", self.magic_cookie, 0x4, total_segments, segment + 1) + b"x" * 1024
                sock.sendto(packet, addr)
            
            print(f"UDP transfer to {addr} completed")
        except Exception as e:
            print(f"Error handling UDP request from {addr}: {e}")

    def listen_for_requests(self):
        """Listen for TCP and UDP client requests."""
        # Start TCP listener
        tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_sock.bind(("", self.tcp_port))
        tcp_sock.listen()
        
        # Start UDP listener
        udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_sock.bind(("", self.udp_port))

        print("Server listening for client requests...")
        while self.running:
            # Handle TCP connections
            tcp_thread = threading.Thread(target=self.accept_tcp_requests, args=(tcp_sock,))
            tcp_thread.start()

            # Handle UDP requests
            data, addr = udp_sock.recvfrom(1024)
            self.process_udp_request(data, addr, udp_sock)

    def accept_tcp_requests(self, tcp_sock):
        """Accept and handle TCP requests."""
        conn, addr = tcp_sock.accept()
        thread = threading.Thread(target=self.handle_tcp_request, args=(conn, addr))
        thread.start()

    def process_udp_request(self, data, addr, udp_sock):
        """Process incoming UDP requests."""
        try:
            magic_cookie, message_type, file_size = struct.unpack("!IBQ", data[:13])
            if magic_cookie == self.magic_cookie and message_type == 0x3:
                thread = threading.Thread(target=self.handle_udp_request, args=(udp_sock, addr, file_size))
                thread.start()
        except Exception as e:
            print(f"Invalid UDP request from {addr}: {e}")

    def run(self):
        """Run the server."""
        offer_thread = threading.Thread(target=self.send_offers)
        offer_thread.start()

        self.listen_for_requests()





if __name__ == "__main__":
    server = SpeedTestServer()
    try:
        server.run()
    except KeyboardInterrupt:
        server.running = False
        print("Server shutting down...")
