import threading, time, struct, sys
from socket import *
#*                ====================>>>>            Team Name:   "The United Front" / "The Speed Testing Association"            <<<<====================

# global variables
serverName = "servername"
serverPort = 12000

def main():
    # ● Startup. You leave this state when you’re done asking the user for parameters.
    # ask for the parameteres and store them in variables.
    FileSize = input("Enter file size: ")
    TCPConnCount = input("Choose amount of TCP  connections: ")
    UDPConnCount = input("Enter amount of UDP connection: ")

    if (FileSize != None) and (TCPConnCount != None) and (UDPConnCount != None):   # input checking, so that only if legit, we start the client.

        #####################################################################################   UUUDP Client from lecture
        # set up the listening UDP socket
        UDPclientSocket = socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
        UDPclientSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)  # from assignment, for multiple clients to be able to listen from the same port
        UDPclientSocket.bind(('',serverPort))

        returning_Message, serverAddress = UDPclientSocket.recvfrom(2048)  # receive UDP offer from the server

        message = "somethingggggggggggggggggg"  #TODO:  make the message into the packet needed     <<<=======================

        UDPclientSocket.sendto(message, (serverName, serverPort))  # send  UDP

        # while   -  receive the data until no more data sending, just a sketch
        returning_Message, serverAddress = UDPclientSocket.recvfrom(2048)  # receive  UDP

        #####################################################################################   UUUDP Client from lecture



        #####################################################################################   TTTCP Client from lecture
        TCPclientSocket = socket(AF_INET, SOCK_STREAM)
        TCPclientSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)  # from assignment, for multiple clients to be able to listen from the same port
        TCPclientSocket.bind(('',serverPort))
        TCPclientSocket.connect((serverName, serverPort))
        
        sentence = "messageee"  #TODO:  a packet that needs to be sent, if something is needed to be sent because we only receive data from the server

        TCPclientSocket.send(sentence)
        modifiedMessage = TCPclientSocket.recv(1024)
        # do something with modifiedMessage

        #####################################################################################   TTTCP Client from lecture


        print("Client started, listening for offer requests...")


        # ● Looking for a server. You leave this state when you get an offer message.
        #TODO: listen and receive a server's offer
        

        # ● Speed test. When you enter this state you should launch multiple threads, one for each
        # TCP and UDP connection. You leave this state when all file transfers are finished. And then return to listening stage again.   <<===========  TCPThread and UDPThread are made.
        #TODO: 

        # end of client program, the threads run infinitly so we won't get here
        UDPclientSocket.close()
        TCPclientSocket.close()

if __name__ == "__main__":
    main()




















#  a class way:


class SpeedTestClient:
    def __init__(self):
        self.server_ip = None
        self.udp_port = None
        self.tcp_port = None

    def get_user_input(self):
        self.file_size = int(input("Enter file size in bytes: "))
        self.tcp_connections = int(input("Enter the number of TCP connections: "))
        self.udp_connections = int(input("Enter the number of UDP connections: "))

    def listen_for_offers(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("", 13117))  # Bind to UDP port 13117
            print("Client started, listening for offer requests...")
            
            while True:
                data, addr = sock.recvfrom(1024)
                magic_cookie, message_type, udp_port, tcp_port = struct.unpack("!IBHH", data)
                if magic_cookie == 0xabcddcba and message_type == 0x2:
                    self.server_ip = addr[0]
                    self.udp_port = udp_port
                    self.tcp_port = tcp_port
                    print(f"Received offer from {self.server_ip}, UDP port: {self.udp_port}, TCP port: {self.tcp_port}")
                    return

    def tcp_speed_test(self, connection_id):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((self.server_ip, self.tcp_port))
            sock.sendall(f"{self.file_size}\n".encode())
            
            start_time = time.time()
            bytes_received = 0
            
            while bytes_received < self.file_size:
                data = sock.recv(4096)
                if not data:
                    break
                bytes_received += len(data)
            
            elapsed_time = time.time() - start_time
            speed = (bytes_received * 8) / elapsed_time  # Speed in bits/second
            print(f"TCP transfer #{connection_id} finished, total time: {elapsed_time:.2f} seconds, total speed: {speed:.2f} bits/second")

    def udp_speed_test(self, connection_id):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            request_packet = struct.pack("!IBQ", 0xabcddcba, 0x3, self.file_size)
            sock.sendto(request_packet, (self.server_ip, self.udp_port))
            
            sock.settimeout(1.0)  # Timeout for UDP transfer
            start_time = time.time()
            packets_received = 0
            packets_total = 0

            try:
                while True:
                    data, _ = sock.recvfrom(1024)
                    packets_total += 1
                    magic_cookie, message_type, total_segments, current_segment = struct.unpack("!IBQQ", data[:21])
                    if magic_cookie == 0xabcddcba and message_type == 0x4:
                        packets_received += 1
            except socket.timeout:
                pass
            
            elapsed_time = time.time() - start_time
            speed = (packets_received * 8 * 1024) / elapsed_time  # Speed in bits/second
            packet_loss = 100 - (packets_received / packets_total * 100 if packets_total > 0 else 0)
            print(f"UDP transfer #{connection_id} finished, total time: {elapsed_time:.2f} seconds, total speed: {speed:.2f} bits/second, percentage of packets received successfully: {100 - packet_loss:.2f}%")

    def run_speed_test(self):
        threads = []
        
        for i in range(1, self.tcp_connections + 1):
            thread = threading.Thread(target=self.tcp_speed_test, args=(i,))
            threads.append(thread)
            thread.start()
        
        for i in range(1, self.udp_connections + 1):
            thread = threading.Thread(target=self.udp_speed_test, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()
        print("All transfers complete, listening to offer requests")

    def run(self):
        self.get_user_input()
        while True:
            self.listen_for_offers()
            self.run_speed_test()





if __name__ == "__main__":
    client = SpeedTestClient()
    client.run()
