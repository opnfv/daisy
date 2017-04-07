/*##############################################################################
# Copyright (c) 2017 ZTE Coreporation and others.
# hu.zhijiang@zte.com.cn
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################*/

#include <stdlib.h>
#include <string.h>

#include "buffer.h"
#include "misc.h"

struct buffer_ctl buffctl;
struct packet_ctl *packetctl[PACKETS_PER_BUFFER];
struct packet_ctl empty;

void buffer_init()
{
    int i;

    for (i = 0; i < PACKETS_PER_BUFFER; i++) {
        packetctl[i] = (struct packet_ctl *)wrapper_malloc(PACKET_SIZE);
        memset(packetctl[i], 0, PACKET_SIZE);
        packetctl[i]->data_size = 0;
        packetctl[i]->seq = 0;
    }

    buffctl.buffer_id = 0;
    buffctl.packet_id_base = 0;
    buffctl.pkt_count = 0;
    empty.data_size = 0;
}

void packetctl_precheck()
{
    int i;

    for (i = 0; i < PACKETS_PER_BUFFER; i++) {
        if (packetctl[i]->data_size != 0) {
            crit("Error precheck packet slot %d,%d", i, packetctl[i]->data_size);
        }
    }
}

// Calculate packet checksum
uint32_t packet_csum(uint8_t *data, int len)
{
    uint32_t *item, sum = 0;
    int i = 0;

    while (len % 4) {
        data[len] = 0; len++;
    }

    while (i < len) {
        item = (uint32_t *)((char *)data + i);
        sum += *item;
        i += 4;
    }

    return sum;
}

// Fill buffers from file descriptor
long buffer_fill(int fd)
{
    int s = 0;
    int r = PACKET_PAYLOAD_SIZE;

    buffctl.buffer_id++;
    buffctl.packet_id_base += buffctl.pkt_count;
    buffctl.buffer_size = 0;
    while (r > 0 && s < PACKETS_PER_BUFFER) {
        if ((r = read(fd, packetctl[s]->data, PACKET_PAYLOAD_SIZE)) < 0) {
            crit("Error reading data from stdin");
        }

        // r == 0 means EOF

        if (r > 0) {
            buffctl.buffer_size += r;
            packetctl[s]->data_size = r;
            packetctl[s]->seq = buffctl.packet_id_base + s;
            packetctl[s]->crc = packet_csum(packetctl[s]->data, r);
            s++;
        }
    }

    log(6, "input %d bytes of data in %d packets", buffctl.buffer_size, s);
    buffctl.pkt_count = s;
    return s;
}

long buffer_flush(int fd)
{
    int s = 0;
    while (buffctl.pkt_count--) {
        write(fd, packetctl[s]->data, packetctl[s]->data_size);
        buffctl.buffer_size -= packetctl[s]->data_size;
        packetctl[s]->data_size = 0;
        packetctl[s]->seq = 0;
        packetctl[s]->crc = 0;
        s++;
    }

    return s;
}

/* Caller should use new_pkt as packet buffer again if this returns NULL */
struct packet_ctl *packet_put(struct packet_ctl *new_pkt)
{
    struct packet_ctl *freed_pkt;
    uint32_t i;

    if (new_pkt->seq < buffctl.packet_id_base ||
        new_pkt->seq - buffctl.packet_id_base >= buffctl.pkt_count) {
        return NULL;
    }

    if (new_pkt->data_size == 0) {
        return NULL;
    }

    i = packet_csum(new_pkt->data, new_pkt->data_size);
    if (new_pkt->crc != i) {
        return NULL;
    }

    i = new_pkt->seq - buffctl.packet_id_base;
    freed_pkt = packetctl[i];
    packetctl[i] = new_pkt;
    return freed_pkt;
}

struct packet_ctl *packet_get(uint32_t seq)
{
    empty.seq = seq;

    if (seq < buffctl.packet_id_base ||
        seq - buffctl.packet_id_base >= buffctl.pkt_count) {
        return &empty;
    }

    if (packetctl[seq - buffctl.packet_id_base]->data_size == 0) {
        return &empty;
    }

    return packetctl[seq - buffctl.packet_id_base];
}
