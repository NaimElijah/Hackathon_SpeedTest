# **Ping Floyd MiniHackaton Team — Network Speed Test (TCP & UDP)**

*A mini-hackathon project by two developers*

This project implements a full **network speed test tool** using both **TCP** and **UDP**, built entirely during a short hackathon session.
It includes:

* A **broadcasting discovery server**
* A **TCP/UDP file-transfer speed tester**
* Multi-threaded client and server logic
* A custom **binary messaging protocol**
* Color-coded terminal UI
* Separate TCP & UDP performance metrics

The system allows any client on the LAN to automatically detect the server, request a specific file-size transfer, and measure actual throughput & packet loss.

---

## 🚀 **How It Works**

### **1. Server (SpeedTestServer)**

Located in `Server.py`


The server:

* Randomizes a TCP and UDP port for testing
* Broadcasts presence every second using **UDP offers**
* Accepts TCP requests and sends a one-shot payload
* Accepts UDP requests and streams segmented packets
* Handles multiple clients simultaneously via **threading**
* Uses color-coded output for readability

**Protocol details:**

| Field          | Value        |
| -------------- | ------------ |
| `MAGIC_COOKIE` | `0xabcddcba` |
| Offer Type     | `0x2`        |
| Request Type   | `0x3`        |
| Payload Type   | `0x4`        |

The server responds differently based on the request protocol:

### **TCP transfer behavior:**

* Client requests a file size
* Server sends header + big monolithic payload
* Client measures total download time

### **UDP transfer behavior:**

* Client requests desired file size
* Server sends **1024-byte segments**
* Client measures:

  * Total packets received
  * Packet loss %
  * UDP speed

The server prints logs such as:

```
Server started, listening on IP address x.x.x.x
TCP request from (addr), file size: N bytes
UDP request from (addr), file size: N bytes
```

---

## 🎮 **2. Client (SpeedTestClient)**

Located in `Client.py`


The client:

1. Listens for broadcast offers
2. Connects automatically upon receiving a valid offer
3. Asks user for:

   * Test file size
   * Number of TCP connections
   * Number of UDP connections
4. Runs multiple concurrent speed tests (threads)
5. Displays:

   * Download speed (bits/sec)
   * Total bytes received
   * Total UDP packet success rate
   * Total elapsed time

### Example output:

```
Received offer from 192.168.1.52, UDP port: 23456, TCP port: 34567
TCP transfer #1 finished, total speed: XXXXX bits/sec
UDP transfer #1 finished, packets received successfully: XX%
```

---

## 🎨 **3. Terminal Colors (bcolors)**

Located in `Colors.py`


The project includes a custom ANSI color class for:

* Titles
* Errors
* Warnings
* Highlights
* Background colors

This makes logs much easier to read during fast-paced debugging.

---

## 🔧 **How to Run**

### **On the server machine:**

```bash
python3 Server.py
```

### **On the client machine:**

```bash
python3 Client.py
```

The client will:

* Automatically discover the server
* Prompt the user for file size & connection count
* Begin sending parallel TCP/UDP test requests

---

## 🧩 **Protocol Overview**

All messages begin with:

```
MAGIC_COOKIE (4 bytes)
TYPE (1 byte)
```

### Offer packet (server → clients)

```
MAGIC_COOKIE (4)
TYPE_OFFER = 0x2 (1)
UDP port (2)
TCP port (2)
```

### TCP Request packet (client → server)

```
MAGIC_COOKIE (4)
TYPE_REQUEST = 0x3 (1)
File size (8)
Endline '\n' (1)
```

### UDP Request packet (client → server)

```
MAGIC_COOKIE (4)
TYPE_REQUEST = 0x3 (1)
File size (8)
```

### Payload packet (server → client)

```
MAGIC_COOKIE (4)
TYPE_PAYLOAD = 0x4 (1)
Total segments (8)
Current segment (8)
Payload (...)
```

---

## ⚙️ **Technologies Used**

* Python 3
* UDP & TCP networking (`socket`)
* Multi-threading (`threading`)
* Binary protocol packing (`struct`)
* System interface detection (`psutil`)
* ANSI terminal coloring
* Mini hackathon collaboration workflow 😄

---

## 🧠 **What This Project Demonstrates**

* Designing binary network protocols
* Robust TCP/UDP communication
* Broadcast-based service discovery
* Multi-threaded client/server architecture
* Handling packet segmentation & reassembly
* Real throughput benchmarking
* Clean and colorful CLI design
* Building something fast under hackathon pressure

---

## **In a Nutshell**

What was implemented:

* Complete server and client architectures
* Binary packet protocol
* Multi-threaded transfer logic
* UDP packet segmentation and tracking
* Logging, color formatting, and error handling
* Test orchestration across multiple connections

---

## 📜 **License**

This project was created during a mini hackathon.
