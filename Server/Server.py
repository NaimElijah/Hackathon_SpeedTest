import threading, time, struct, sys, random, socket, psutil, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Colors import bcolors

#*                    ====================>>>>            Team Name:  "Ping Floyd", "ACK/DC"               <<<<====================
stdout_lock = threading.Lock()

class SpeedTestServer:
    MAGIC_COOKIE = 0xabcddcba
    TYPE_OFFER = 0x2
    TYPE_REQUEST = 0x3
    TYPE_PAYLOAD = 0x4

    def __init__(self):
        self.udp_port = random.randint(20000, 30000)
        self.tcp_port = random.randint(30001, 40000)
        self.running = True
        self.broadcast_port = 13117
        self.udp_lock = threading.Lock()

    def print_safe(self, message):
        with stdout_lock:
            print(message)

    def get_ip_address(self, ifname):
        for iface, addrs in psutil.net_if_addrs().items():
            if iface == ifname:
                for addr in addrs:
                    if addr.family == socket.AF_INET:
                        return addr.address
        raise ValueError(f"{bcolors.UNDERLINE}{bcolors.RED}{bcolors.BOLD}No IPv4 address found for interface {ifname}{bcolors.ENDC}")


    def send_offers(self):
        """Send periodic UDP offer messages to announce server availability."""
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.print_safe(f"{bcolors.BLUE}Server started, listening on Ip address {self.get_ip_address('Ethernet 4')} {bcolors.ENDC}")
            
            offer_packet = struct.pack("!IBHH", self.MAGIC_COOKIE, self.TYPE_OFFER, self.udp_port, self.tcp_port)
            
            while self.running:
                sock.sendto(offer_packet, ("<broadcast>", self.broadcast_port))
                time.sleep(1)  # Send offer every second


    def handle_tcp_request(self, conn, addr):
        """Handle TCP file size requests."""
        try:
            data = conn.recv(1024)
            (magic, msg_type, file_size, endline_char) = struct.unpack('!IBQ1s', data)
            if magic != self.MAGIC_COOKIE or msg_type != self.TYPE_REQUEST or endline_char != b"\n":
                raise ValueError(f"{bcolors.UNDERLINE}{bcolors.RED}{bcolors.BOLD}Invalid TCP request{bcolors.ENDC}")
            self.print_safe(f"{bcolors.GREEN}TCP request from {addr}, file size: {file_size} bytes{bcolors.ENDC}")

            # Simulate sending the file
            payload_msg = struct.pack("!IBQQ", self.MAGIC_COOKIE, self.TYPE_PAYLOAD, 1, 1) + b"x" * file_size # TODO: fix in client and server
           
            conn.send(payload_msg)

            self.print_safe(f"{bcolors.BLUE}TCP transfer to {addr} completed{bcolors.ENDC}")
        except (ConnectionResetError, socket.error) as e:
            self.print_safe(f"{bcolors.UNDERLINE}{bcolors.RED}{bcolors.BOLD}Client {addr} disconnected: {e}{bcolors.ENDC}")
        except Exception as e:
            self.print_safe(f"{bcolors.UNDERLINE}{bcolors.RED}{bcolors.BOLD}Error handling TCP request from {addr}: {e}{bcolors.ENDC}")
        finally:
            conn.close()


    def handle_udp_request(self, sock, addr, file_size):
        """Handle UDP file size requests."""
        try:
            self.print_safe(f"{bcolors.GREEN}UDP request from {addr}, file size: {file_size} bytes{bcolors.ENDC}")

            # Simulate sending data in UDP packets
            total_segments = (file_size + 1023) // 1024
            remaining_bytes = file_size

            for segment in range(total_segments):
                payload_size = min(remaining_bytes, 1024)
                packet = struct.pack("!IBQQ", self.MAGIC_COOKIE, self.TYPE_PAYLOAD, total_segments, segment + 1) + b"x" * payload_size
                remaining_bytes -= 1024
                with self.udp_lock:
                    sock.sendto(packet, addr)
            
            self.print_safe(f"{bcolors.BLUE}UDP transfer to {addr} completed{bcolors.ENDC}")
        except (ConnectionResetError, socket.error) as e:
            self.print_safe(f"Client {addr} disconnected: {e}")
        except Exception as e:
            self.print_safe(f"{bcolors.UNDERLINE}{bcolors.RED}{bcolors.BOLD}Error handling UDP request from {addr}: {e}{bcolors.ENDC}")


    def listen_for_requests(self):
        """Listen for TCP and UDP client requests."""
        self.print_safe(f"{bcolors.BLUE}Server listening for client requests...{bcolors.ENDC}")
        # Start TCP listener
        listenToTCPThread = threading.Thread(target=self.listen_for_TCP, args=())
        # Start UDP listener
        listenToUDPThread = threading.Thread(target=self.listen_for_UDP, args=())
        
        try:
            listenToTCPThread.start()
            listenToUDPThread.start()
        except KeyboardInterrupt as e:
            self.print_safe(f"{bcolors.UNDERLINE}{bcolors.RED}{bcolors.BOLD}Error listening for requests: {e}{bcolors.ENDC}")


    def listen_for_TCP(self):
        tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_sock.bind(("", self.tcp_port))
        while self.running:
        # Handle TCP connections
            tcp_sock.listen()
            self.accept_tcp_requests(tcp_sock)
    
    
    def listen_for_UDP(self):
        udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_sock.bind(("", self.udp_port))
        while self.running:
            # Handle UDP requests
            data, addr = udp_sock.recvfrom(4096)
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
            if magic_cookie == self.MAGIC_COOKIE and message_type == self.TYPE_REQUEST:
                thread = threading.Thread(target=self.handle_udp_request, args=(udp_sock, addr, file_size))
                thread.start()
        except Exception as e:
            self.print_safe(f"{bcolors.RED}{bcolors.BOLD}{bcolors.UNDERLINE}Invalid UDP request from {addr}: {e}{bcolors.ENDC}")


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
        print(f"\n{bcolors.BG_BLUE}{bcolors.BOLD}Server shutting down...{bcolors.ENDC}\n")
