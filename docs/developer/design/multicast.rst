Detailed Design
===============

Protocol Design
---------------

1. All Protocol headers are 1 byte long or align to 4 bytes.
2. Packet size should not exceed above 1500(MTU) bytes including UDP/IP header and should
be align to 4 bytes. In future, MTU can be modified larger than 1500(Jumbo Frame) through
cmd line option to enlarge the data throughput.

/* Packet header definition (align to 4 bytes) */
struct packet_ctl {
    uint32_t seq; // packet seq number start from 0, unique in server life cycle.
    uint32_t crc; // checksum
    uint32_t data_size; // payload length
    uint8_t data[0];
};

/* Buffer info definition (align to 4 bytes) */
struct buffer_ctl {
    uint32_t buffer_id; // buffer seq number start from 0, unique in server life cycle.
    uint32_t buffer_size; // payload total length of a buffer
    uint32_t packet_id_base; // seq number of the first packet in this buffer.
    uint32_t pkt_count; // number of packet in this buffer, 0 means EOF.
};


3. 1-byte-long header definition

Signals such as the four below are 1 byte long, to simplify the receive process(since it
cannot be spitted ).

#define CLIENT_READY 0x1
#define CLIENT_REQ 0x2
#define CLIENT_DONE 0x4
#define SERVER_SENT 0x8

Note: Please see the collaboration diagram for their meanings.

4. Retransmission Request Header

/* Retransmition Request Header (align to 4 bytes) */
struct request_ctl {
    uint32_t req_count; // How many seqs below.
    uint32_t seqs[0]; // packet seqs.
};

5. Buffer operations

void buffer_init(); // Init the buffer_ctl structure and all(say 1024) packet_ctl
structures. Allocate buffer memory.
long buffer_fill(int fd); // fill a buffer from fd, such as stdin
long buffer_flush(int fd); // flush a buffer to fd, say stdout
struct packet_ctl *packet_put(struct packet_ctl *new_pkt);// put a packet to a buffer
and return a free memory slot for the next packet.
struct packet_ctl *packet_get(uint32_t seq);// get a packet data in buffer by
indicating the packet seq.


How to sync between server threads
----------------------------------

If children's aaa() operation need to wait the parents's init() to be done, then do it
literally like this:

   UDP Server
   TCP Server1 = spawn( )----> TCP Server1
    init()
                               TCP Server2 = spawn( )-----> TCP Server2
    V(sem)----------------------> P(sem)                // No child any more
                                  V(sem)---------------------> P(sem)
                                  aaa()           // No need to V(sem), for no child
                                                               aaa()

If parent's send() operation need to wait the children's ready() done, then do it
literally too, but is a reverse way:

   UDP Server                  TCP Server1                  TCP Server2
                                                       // No child any more
                                 ready()                       ready()
                                 P(sem) <--------------------- V(sem)
    P(sem) <------------------   V(sem)
    send()

Note that the aaa() and ready() operations above run in parallel. If this is not the
case due to race condition, the sequence above can be modified into this below:

   UDP Server                  TCP Server1                  TCP Server2
                                                       // No child any more
                                                               ready()
                                 P(sem) <--------------------- V(sem)
                                 ready()
    P(sem) <-------------------  V(sem)
    send()


In order to implement such chained/zipper sync pattern, a pair of semaphores is
needed between the parent and the child. One is used by child to wait parent , the
other is used by parent to wait child. semaphore pair can be allocated by parent
and pass the pointer to the child over spawn() operation such as pthread_create().

/* semaphore pair definition */
struct semaphores {
    sem_t wait_parent;
    sem_t wait_child;
};

Then the semaphore pair can be recorded by threads by using the semlink struct below:
struct semlink {
    struct semaphores *this; /* used by parent to point to the struct semaphores
                                which it created during spawn child. */
    struct semaphores *parent; /* used by child to point to the struct
                                  semaphores which it created by parent */
};

chained/zipper sync API:

void sl_wait_child(struct semlink *sl);
void sl_release_child(struct semlink *sl);
void sl_wait_parent(struct semlink *sl);
void sl_release_parent(struct semlink *sl);

API usage is like this.

Thread1(root parent)          Thread2(child)               Thread3(grandchild)
sl_wait_parent(noop op)
sl_release_child
                +---------->sl_wait_parent
                            sl_release_child
                                           +-----------> sl_wait_parent
                                                         sl_release_child(noop op)
                                                         ...
                                                         sl_wait_child(noop op)
                                                       + sl_release_parent
                            sl_wait_child <-------------
                          + sl_release_parent
sl_wait_child <------------
sl_release_parent(noop op)

API implementation:

void sl_wait_child(struct semlink *sl)
{
    if (sl->this) {
        P(sl->this->wait_child);
    }
}

void sl_release_child(struct semlink *sl)
{
    if (sl->this) {
        V(sl->this->wait_parent);
    }
}

void sl_wait_parent(struct semlink *sl)
{
    if (sl->parent) {
        P(sl->parent->wait_parent);
    }
}

void sl_release_parent(struct semlink *sl)
{
    if (sl->parent) {
        V(sl->parent->wait_child);
    }
}

Client flow chart
-----------------
See Collaboration Diagram

UDP thread flow chart
---------------------
See Collaboration Diagram

TCP thread flow chart
---------------------


S_INIT --- (UDP initialized) --->  S_ACCEPT --- (accept clients) --+
                                                                   |
  /----------------------------------------------------------------/
  V
S_PREP --- (UDP prepared abuffer)
  ^               |
  |               \--> S_SYNC --- (clients ClIENT_READY)
  |                                        |
  |                                        \--> S_SEND --- (clients CLIENT_DONE)
  |                                                                |
  |                                                                V
  \---------------(bufferctl.pkt_count != 0)-----------------------+
                                                                   |
                                                                   V
                                             exit() <--- (bufferctl.pkt_count == 0)


TCP using poll and message queue
--------------------------------

TCP uses poll() to sync with client's events as well as output event from itself, so
that we can use non-block socket operations to reduce the latency. POLLIN means there
are message from client and POLLOUT means we are ready to send message/retransmission
packets to client.

poll main loop pseudo code:
void check_clients(struct server_status_data *sdata)
{
    poll_events = poll(&(sdata->ds[1]), sdata->ccount - 1, timeout);

    /* check all connected clients */
    for (sdata->cindex = 1; sdata->cindex < sdata->ccount; sdata->cindex++) {
        ds = &(sdata->ds[sdata->cindex]);
        if (!ds->revents) {
            continue;
        }

        if (ds->revents & (POLLERR|POLLHUP|POLLNVAL)) {
            handle_error_event(sdata);
        } else if (ds->revents & (POLLIN|POLLPRI)) {
            handle_pullin_event(sdata);  // may set POLLOUT into ds->events
                                         // to trigger handle_pullout_event().
        } else if (ds->revents & POLLOUT) {
            handle_pullout_event(sdata);
        }
    }
}

For TCP, since the message from client may not complete and send data may be also
interrupted due to non-block fashion, there should be one send message queue and a
receive message queue on the server side for each client (client do not use non-block
operations).

TCP message queue definition:

struct tcpq {
    struct qmsg *head, *tail;
    long count; /* message count in a queue */
    long size; /* Total data size of a queue */
};

TCP message queue item definition:

struct qmsg {
    struct qmsg *next;
    void *data;
    long size;
};

TCP message queue API:

// Allocate and init a queue.
struct tcpq * tcpq_queue_init(void);

// Free a queue.
void tcpq_queue_free(struct tcpq *q);

// Return queue length.
long tcpq_queue_dsize(struct tcpq *q);

// queue new message to tail.
void tcpq_queue_tail(struct tcpq *q, void *data, long size);

// queue message that cannot be sent currently back to queue head.
void tcpq_queue_head(struct tcpq *q, void *data, long size);

// get one piece from queue head.
void * tcpq_dequeue_head(struct tcpq *q, long *size);

// Serialize all pieces of a queue, and move it out of queue, to ease the further
//operation on it.
void * tcpq_dqueue_flat(struct tcpq *q, long *size);

// Serialize all pieces of a queue, do not move it out of queue, to ease the further
//operation on it.
void * tcpq_queue_flat_peek(struct tcpq *q, long *size);
