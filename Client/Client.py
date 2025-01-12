import threading, time, struct, sys, socket, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Colors import bcolors

#*                    ====================>>>>            Team Name:  "Ping Floyd", "ACK/DC"               <<<<====================
stdout_lock = threading.Lock()

class SpeedTestClient:
    BROADCAST_PORT = 13117
    MAGIC_COOKIE = 0xabcddcba
    TYPE_OFFER = 0x2
    TYPE_REQUEST = 0x3
    TYPE_PAYLOAD = 0x4
    RECIEVE_SIZE = 1024
    Payload_Packet_Header_Size = 21

    def __init__(self):
        self.server_ip = None
        self.udp_port = None
        self.tcp_port = None

    def print_safe(self, message):
        with stdout_lock:
            print(message)

    def get_user_input(self):
        self.file_size = int(input(f"{bcolors.YELLOW}Enter file size in bytes: {bcolors.ENDC}"))
        self.tcp_connections = int(input(f"{bcolors.YELLOW}Enter the number of TCP connections: {bcolors.ENDC}"))
        self.udp_connections = int(input(f"{bcolors.YELLOW}Enter the number of UDP connections: {bcolors.ENDC}"))

    def listen_for_offers(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # maybe REUSEPORT
            # TODO: consider binding to all ports from 1024 to 65535
            sock.bind(("", self.BROADCAST_PORT))  # Bind to UDP port 13117
            print(f"{bcolors.BLUE}Client started, listening for offer requests..{bcolors.ENDC}.")
            
            while True:
                try:
                    data, addr = sock.recvfrom(self.RECIEVE_SIZE)
                    magic_cookie, message_type, udp_port, tcp_port = struct.unpack("!IBHH", data)
                    if magic_cookie == self.MAGIC_COOKIE and message_type == self.TYPE_OFFER:
                        self.server_ip = addr[0]
                        self.udp_port = udp_port
                        self.tcp_port = tcp_port
                        print(f"{bcolors.GREEN}Received offer from {self.server_ip}, UDP port: {self.udp_port}, TCP port: {self.tcp_port} {bcolors.ENDC}")  # TODO: make sure the prints in the assignment are as instructed
                        return
                except (ConnectionResetError, socket.error) as e:
                    self.print_safe(f"{bcolors.RED}{bcolors.BOLD}{bcolors.UNDERLINE}Error receiving offer: {e}{bcolors.ENDC}")

    def tcp_speed_test(self, connection_id):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((self.server_ip, self.tcp_port))
                request_packet = struct.pack("!IBQ1s", self.MAGIC_COOKIE, self.TYPE_REQUEST, self.file_size, b"\n")
                sock.sendall(request_packet)
                
                bytes_received = 0
                total_expected_segments = 1
                current_segment = 0
                start_time = time.time()

                while current_segment < total_expected_segments:
                    self.print_safe(f"{bcolors.BLUE}receiving data{bcolors.ENDC}")
                    data = sock.recv(self.file_size + self.Payload_Packet_Header_Size)
                    self.print_safe(f"{bcolors.BLUE}data received{bcolors.ENDC}")
                    (magic, msg_type, total_segments, current_received_segment) = struct.unpack('!IBQQ', data[0:self.Payload_Packet_Header_Size])

                    if magic != self.MAGIC_COOKIE or msg_type != self.TYPE_PAYLOAD:
                        raise ValueError(f"{bcolors.UNDERLINE}{bcolors.RED}{bcolors.BOLD}Invalid Paylaod received - magic or type error{bcolors.ENDC}")
                        
                    if current_received_segment != current_segment + 1:
                        raise ValueError(f"{bcolors.UNDERLINE}{bcolors.RED}{bcolors.BOLD}Invalid segment received, current_received_segment != current_segment + 1{bcolors.ENDC}")
                    
                    current_segment = current_received_segment
                    
                    if not data[self.Payload_Packet_Header_Size:]:
                        break
                    bytes_received += len(data[self.Payload_Packet_Header_Size:])
                
                elapsed_time = time.time() - start_time
                if elapsed_time == 0:
                    speed = (bytes_received * 8)  # so we won't get division by 0 error
                else:
                    speed = (bytes_received * 8) / elapsed_time  # Speed in bits/second
                self.print_safe(f"{bcolors.GREEN}TCP transfer #{connection_id} finished, total time: {elapsed_time} seconds, total speed: {speed:.2f} bits/second, total bytes received: {bytes_received}{bcolors.ENDC}")
        except (ConnectionResetError, socket.error) as e:
            self.print_safe(f"{bcolors.RED}{bcolors.BOLD}{bcolors.UNDERLINE}Error connecting to server: {e}{bcolors.ENDC}")



    def udp_speed_test(self, connection_id):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                request_packet = struct.pack("!IBQ", self.MAGIC_COOKIE, self.TYPE_REQUEST, self.file_size)
                sock.sendto(request_packet, (self.server_ip, self.udp_port))
                
                sock.settimeout(1.0)  # Timeout for UDP transfer
                packets_received = 0
                packets_total = 0
                total_expected_segments = 1
                current_segment = 0
                start_time = time.time()

                try:
                    while current_segment < total_expected_segments:
                        data, _ = sock.recvfrom(4096)  # generally, our server sends 1024+21 each packet
                        packets_total += 1
                        magic_cookie, message_type, total_segments, current_received_segment = struct.unpack("!IBQQ", data[:self.Payload_Packet_Header_Size])
                        if magic_cookie != self.MAGIC_COOKIE or message_type != self.TYPE_PAYLOAD:
                            raise ValueError(f"{bcolors.UNDERLINE}{bcolors.RED}{bcolors.BOLD}Invalid Paylaod received{bcolors.ENDC}")
                    
                        if total_expected_segments == 1:
                            total_expected_segments = total_segments
                        
                        if current_received_segment == current_segment + 1:
                            current_segment = current_received_segment
                            if magic_cookie == self.MAGIC_COOKIE and message_type == self.TYPE_PAYLOAD:
                                packets_received += 1
                            
                except socket.timeout:
                    pass
                
                elapsed_time = time.time() - start_time
                if elapsed_time == 0:
                    speed = (packets_received * 8 * self.RECIEVE_SIZE)  # so we won't get division by 0 error
                else:
                    speed = (packets_received * 8 * self.RECIEVE_SIZE) / elapsed_time  # Speed in bits/second
                packet_loss = 100 - (packets_received / packets_total * 100 if packets_total > 0 else 0)
                self.print_safe(f"{bcolors.GREEN}UDP transfer #{connection_id} finished, total time: {elapsed_time:.2f} seconds, total speed: {speed:.2f} bits/second, percentage of packets received successfully: {100 - packet_loss:.2f}%{bcolors.ENDC}")
        except (ConnectionResetError, socket.error) as e:
            self.print_safe(f"{bcolors.RED}{bcolors.BOLD}{bcolors.UNDERLINE}Error connecting to server: {e}{bcolors.ENDC}")

    def run_speed_test(self):
        threads = []
        print(f"{bcolors.BLUE}Starting speed test...{bcolors.ENDC}")
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
        print(f"{bcolors.UNDERLINE}{bcolors.BLUE}{bcolors.BOLD}All transfers complete, listening to offer requests{bcolors.ENDC}")

    def run(self):
        self.get_user_input()
        while True:
            self.listen_for_offers()
            self.run_speed_test()





if __name__ == "__main__":
    client = SpeedTestClient()
    try:
        client.run()
    except KeyboardInterrupt:
        print(f"\n{bcolors.BG_BLUE}{bcolors.BOLD}KeyboardInterrupt - Exiting...{bcolors.ENDC}\n")
        sys.exit(0)
    except ValueError:
        print(f"\n{bcolors.RED}{bcolors.BOLD}{bcolors.UNDERLINE}ValueError - Exiting...{bcolors.ENDC}\n")
        sys.exit(0)
