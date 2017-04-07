/*##############################################################################
# Copyright (c) 2017 ZTE Coreporation and others.
# hu.zhijiang@zte.com.cn
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################*/

#ifndef _MCAST_BUFFER_H
#define _MCAST_BUFFER_H

#include <unistd.h>
#include <netinet/ip.h>
#include <netinet/udp.h>

#define MTU 1500

#define PACKET_SIZE ((MTU) - sizeof(struct iphdr) - sizeof(struct udphdr))

/* Exclude padding */
#define PACKET_PAYLOAD_SIZE (((PACKET_SIZE) - sizeof(struct packet_ctl)) & ~0x3)

#define PACKETS_PER_BUFFER 1024

#define DEF_PORT 18383 /* for both UDP and TCP */

/* Buffer header (align to 4 Byte) */
struct buffer_ctl {
    uint32_t buffer_id;
    uint32_t buffer_size;
    uint32_t packet_id_base;
    uint32_t pkt_count;
};

/* Packet header (align to 4 Byte) */
struct packet_ctl {
    uint32_t seq;
    uint32_t crc;
    uint32_t data_size;
    uint8_t data[0];
};

#define CLIENT_READY 0x1
#define CLIENT_REQ 0x2
#define CLIENT_DONE 0x4
#define SERVER_SENT 0x8

/* Retransmition Request Header (align to 4 Byte) */
struct request_ctl {
    uint32_t req_count; /* Requested packet slot count */
};

extern struct buffer_ctl buffctl;
extern struct packet_ctl *packetctl[PACKETS_PER_BUFFER];

void buffer_init();
long buffer_fill(int fd);
long buffer_flush(int fd);
struct packet_ctl *packet_put(struct packet_ctl *new_pkt);
struct packet_ctl *packet_get(uint32_t seq);
void packetctl_precheck();

#endif
