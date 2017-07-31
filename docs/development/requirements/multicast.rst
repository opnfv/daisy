Requirement
===========
1. When deploying a large OPNFV/OpenStack cluster, we would like to take the advantage of UDP
multicast to prevent the network bottleneck when distributing Kolla container from one
Installer Server to all target hosts by using unicast.

2. When it comes to auto scaling (extension) of compute nodes, use unicast is acceptable, since
the number of nodes in this condition is usually small.

The basic step to introduce multicast to deployment is:
a. Still setup the monopolistic docker registry server on Daisy server as a failsafe.
b. Daisy server, as the multicast server, prepares the image file to be transmitted, and count
how many target hosts(as the multicast clients)that should receive the image file
simultaneously.
c. Multicast clients tell the multicast server about ready to receive the image.
d. Multicast server transmits image over UDP multicast channel.
e. Multicast clients report success after received the whole image.
f. Setup docker registry server on each target hosts based upon received docker image.
g. Setup Kolla ansible to use 127.0.0.1 as the registry server IP so that the real docker
container retrieving network activities only take place inside target hosts.


Design
======

Methods to achieve
------------------

TIPC
++++

TIPC or its wrapper such as ZeroMQ is good at multicast, but it is not suitable as an
installer:
1. The default TIPC kernel module equipped by CentOS7(kernel verison 3.10) is NOT stable
especially in L3 multicast(although we can use L2 multicast, but the network will be limited to
L2). If errors happen, it is hard for us to recover a node from kernel panic.

2. TIPC's design is based on a stable node cluster environment, esp in Lossless Ethernet. But
the real environment is generally not in that case. When multicast is broken, Installer should
switch to unicast, but TIPC currently do not have such capability.

Top level design
----------------
1. There are two kinds of thread on the server side, one is UDP multicast thread the other is
TCP sync/retransmit thread. There will be more than one TCP threads since one TCP thread can
only serve a limited client (say 64~128) in order to limit the CPU load and unicast retransmit
network usage.

2. There is only one thread on client side.

3. All the packets that a client lost during UDP multicast will be request by client to the TCP
thread and resend by using TCP unicast, if unicast still cannot deliver the packets successfully,
the client will failback to using the monopolistic docker registry server on Daisy server as a
failsafe option.

4. Each packet needs checksum.


UDP Server Design (runs on Daisy Server)
----------------------------------------

1. Multicast group IP and Port should be configurable, as well as the interface that will be
used as the egress of the multicast packets. The user will pass the interface's IP as the
handle to find the egress.

2. Image data to be sent is passed to server through stdin.

3. Consider the size of image is large (xGB), the server cannot pre-allocate whole buffer to
hold all image at once. Besides, since the data is from stdin and the actual length is
unpredictable. So the server should split the data into small size buffers and send to the
clients one by one. Furthermore, buffer shall be divided into packets which size is MTU
including the UDP/IP header. Then the buffer size can be , for example 1024 * MTU including the
UDP/IP header.

4. After sending one buffer to client the server should stop and get feedback from client to
see if all clients have got all packets in that buffer. If any clients lost any buffer, client
should request the server to resend packets from a more stable way(TCP).

5. when got the EOF from stdin, server should send a buffer which size is 0 as an EOF signal to
the client to let it know about the end of sending.


TCP Server Design (runs on Daisy Server)
----------------------------------------

1. All TCP server threads and the only one UDP thread share one process. The UDP thread is the
parent thread, and the first TCP thread is the child, while the second TCP thread is the
grandchild, and so on. Thus, for each TCP thread, there is only one parent and at most one
child.

2. TCP thread accepts the connect request from client. The number of client is predefined by
server cmdline parameter. Each TCP thread connect with at most ,say 64 clients, if there are
more clients to be connected to, then a child TCP thread is spawned by the parent.

3. Before UDP thread sending any buffer to client, all TCP threads should send UDP multicast
IP/Port information to their clients beforehand.

4. During each buffer sending cycle, TCP threads send a special protocol message to tell
clients about the size/id of the buffer and id of each packet in it. After getting
acknowledgements from all clients, TCP threads then signal the UDP thread to start
multicasting buffer over UDP. After multicasting finished, TCP threads notifies clients
multicast is done, and wait acknowledgements from clients again. If clients requests
retransmission, then it is the responsibility of TCP threads to resend packets over unicast.
If no retransmission needed, then clients should signal TCP threads that they are ready for
the next buffer to come.

5. Repeat step 4 if buffer size is not 0 in the last round, otherwise, TCP server shutdown
connection and exit.


Server cmdline usage example
----------------------------

./server <local_ip> <number_of_clients> [port] < kolla_image.tgz

<local_ip> is used here to specify the multicast egress interface. But which interface will be
used by TCP is leaved to route table to decide.
<number_of_clients> indicates the number of clients , thus the number of target hosts which
need to receive the image.
[port] is the port that will be used by both UDP and TCP. Default value can be used if user
does not provide it.


Client Design(Target Host side)
--------------------------------

1. Each target hosts has only one client process.

2. Client connect to TCP server according to the cmdline parameters right after start up.

3. After connecting to TCP server, client first read from TCP server the multicast group
information which can be used to create the multicast receive socket then.

4. During each buffer receiving cycle, the client first read from TCP server the buffer info,
prepare the receive buffer, and acknowledge the TCP server that it is ready to receive. Then,
client receive buffer from the multicast socket until TCP server notifying the end of
multicast. By compare the buffer info and the received packets, the client knows whether to
send the retransmission request or not and whether to wait retransmission packet or not.
After all packets are received from UDP/TCP, the client eventually flush buffer to stdout
and tells the TCP server about ready to receive the next buffer.

5. Repeat step 4 if buffer size is not 0 in the last round, otherwise, client shutdowns
connection and exit.

Client cmdline usage example
----------------------------

./client <local_ip> <server_ip> [port] > kolla_image.tgz

<local_ip> is used here to specify the multicast ingress interface. But which interface
will be used by TCP is leaved to route table to decide.
<server_ip> indicates the TCP server IP to be connected to.
[port] is the port that will be used by both connect to TCP server and receive multicast
data.


Collaboration diagram among UDP Server, TCP Server(illustrate only one TCP thread)
and Clients:


UDP Server                        TCP Server                                         Client
    |                                  |                                                |
init mcast group
init mcast send socket
    ---------------------------------->
                                  accept clients
                                       <------------------------connet------------------
                                       --------------------send mcast group info------->
    <----------------------------------
                                  state = PREP
do {
read data from stdin
prepare one buffer
    ----------------------------------->
                                  state = SYNC
                                       -------------------send buffer info-------------->
                                      <----------------------send ClIENT_READY-----------
    <----------------------------------
                                  state = SEND

    ================================================send buffer over UDP multicast======>
    ----------------------------------->
                                      -----------------------send SERVER_SENT----------->
                                      [<-------------------send CLIENT_REQUEST----------]
                                      [--------------send buffer over TCP unicast------>]
                                                                   flush buffer to stdout
                                      <-------------------send CLIENT_DONE---------------
    <----------------------------------
                                  state = PREP
while (buffer.len != 0)
