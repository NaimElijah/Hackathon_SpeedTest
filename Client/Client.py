import threading, time, struct, sys, socket

#*                ====================>>>>            Team Name:  "The Speed Testing Association"            <<<<====================

class SpeedTestClient:
    BROADCAST_PORT = 13117
    MAGIC_COOKIE = 0xabcddcba
    TYPE_OFFER = 0x2
    TYPE_REQUEST = 0x3
    TYPE_PAYLOAD = 0x4

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
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # maybe REUSEPORT
            # TODO: consider binding to all ports from 1024 to 65535
            sock.bind(("", self.BROADCAST_PORT))  # Bind to UDP port 13117
            print("Client started, listening for offer requests...")
            
            while True:
                data, addr = sock.recvfrom(1024)
                magic_cookie, message_type, udp_port, tcp_port = struct.unpack("!IBHH", data)
                if magic_cookie == self.MAGIC_COOKIE and message_type == self.TYPE_OFFER:
                    self.server_ip = addr[0]
                    self.udp_port = udp_port
                    self.tcp_port = tcp_port
                    print(f"Received offer from {self.server_ip}, UDP port: {self.udp_port}, TCP port: {self.tcp_port}")   # TODO: make sure the prints in the assignment are as instructed
                    return

    def tcp_speed_test(self, connection_id):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((self.server_ip, self.tcp_port))
            request_packet = struct.pack("!IBQ1s", self.MAGIC_COOKIE, self.TYPE_REQUEST, self.file_size, b"\n")
            sock.sendall(request_packet)
            
            bytes_received = 0
            total_expected_segments = 1
            current_segment = 0
            start_time = time.time()

            while current_segment < total_expected_segments:
                print("receiving data")
                data = sock.recv(self.file_size + 21)
                print("data received")
                (magic, msg_type, total_segments, current_received_segment) = struct.unpack('!IBQQ', data[0:21])

                if magic != self.MAGIC_COOKIE or msg_type != self.TYPE_PAYLOAD:
                    raise ValueError("Invalid Paylaod received - magic or type error")
                     
                if current_received_segment != current_segment + 1:
                    raise ValueError("Invalid segment received, current_received_segment != current_segment + 1")
                
                current_segment = current_received_segment
                
                if not data[21:]:
                    break
                bytes_received += len(data[21:])
            
            elapsed_time = time.time() - start_time
            if elapsed_time == 0:
                speed = (bytes_received * 8)  # so we won't get division by 0 error
            else:
                speed = (bytes_received * 8) / elapsed_time  # Speed in bits/second
            print(f"TCP transfer #{connection_id} finished, total time: {elapsed_time} seconds, total speed: {speed:.2f} bits/second, total bytes received: {bytes_received}")


    def udp_speed_test(self, connection_id):
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
                    magic_cookie, message_type, total_segments, current_received_segment = struct.unpack("!IBQQ", data[:21])
                    if magic_cookie != self.MAGIC_COOKIE or message_type != self.TYPE_PAYLOAD:
                        raise ValueError("Invalid Paylaod received")
                
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
                speed = (packets_received * 8 * 1024)  # so we won't get division by 0 error
            else:
                speed = (packets_received * 8 * 1024) / elapsed_time  # Speed in bits/second
            packet_loss = 100 - (packets_received / packets_total * 100 if packets_total > 0 else 0)
            print(f"UDP transfer #{connection_id} finished, total time: {elapsed_time:.2f} seconds, total speed: {speed:.2f} bits/second, percentage of packets received successfully: {100 - packet_loss:.2f}%")

    def run_speed_test(self):
        threads = []
        print("Starting speed test...")
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
    try:
        client.run()
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt - Exiting...\n")
        sys.exit(0)
    except ValueError:
        print("\nValueError - Exiting...\n")
        sys.exit(0)
