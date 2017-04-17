/*##############################################################################
# Copyright (c) 2017 ZTE Coreporation and others.
# hu.zhijiang@zte.com.cn
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################*/

#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <arpa/inet.h>

#include "buffer.h"
#include "udp-common.h"
#include "tcp-common.h"
#include "misc.h"

/* Global statistics */
long tot_dups = 0;
long tot_reps = 0;
long tot_pkts = 0;
long long tot_size = 0;

void recv_mcinfo(int tcp_socket)
{
    int res;

    res = read_all(tcp_socket, &mcinfo, sizeof(struct mc_info));
    if (res != sizeof(struct mc_info)) {
        crit("Error while reading initial data");
    }
}

void recv_buffctl(int tcp_socket)
{
    int res;

    res = read_all(tcp_socket, &buffctl, sizeof(struct buffer_ctl));
    if (res != sizeof(struct buffer_ctl)) {
        crit("Error reading buffer control");
    }
}

void send_client_ready(int tcp_socket)
{
    uint8_t cmd;

    /* Tell TCP server we are ready to receive */
    cmd = CLIENT_READY;
    write(tcp_socket, &cmd, 1);
}

/* Read out the SERVER_SENT signal */
void recv_server_sent(int tcp_socket)
{
    uint8_t cmd;
    int res;

    res = read_all(tcp_socket, &cmd, 1);
    if (res != 1) {
    //if (read(tcp_socket, &cmd, 1) < 1) {
        crit("Error reading SERVER_SENT");
    }

    if (cmd != SERVER_SENT) {
        crit("Error reading SERVER_SENT %d", cmd);
    }
}

void send_client_request(int tcp_socket, struct request_ctl *req)
{
    uint8_t cmd;

    /* Tell TCP server we are ready to receive */
    cmd = CLIENT_REQ;
    write(tcp_socket, &cmd, 1);
    write(tcp_socket, req,
          sizeof(struct request_ctl) + (req->req_count) * sizeof(uint32_t));
}

void recv_server_ack(int tcp_socket, struct packet_ctl *pkt)
{
    int res;

    res = read_all(tcp_socket, pkt, sizeof(struct packet_ctl));
    if (res != sizeof(struct packet_ctl)) {
        crit("Error on tcp socket");
    }

    res = read_all(tcp_socket,
                   ((char *)pkt) + sizeof(struct packet_ctl),
                   pkt->data_size);
    if (res != pkt->data_size) {
        crit("Error on tcp socket received %d of %d",
             res, pkt->data_size);
    }
}

void tcp_retransmition(int tcp_socket,
                       struct packet_ctl **curr_pkt,
                       struct packet_ctl **freed_pkt)
{
    struct request_ctl *reqctl;
    uint32_t *reqbody;
    uint8_t rqbuf[sizeof(struct request_ctl) + PACKETS_PER_BUFFER * sizeof(uint32_t)];
    uint32_t l;

    reqctl = (struct request_ctl *)rqbuf;
    reqbody = (uint32_t *)(rqbuf + sizeof(struct request_ctl));

    reqctl->req_count = 0;
    for (l = 0; l < buffctl.pkt_count; l++) {
        if (!packetctl[l]->data_size) {
            log(6, "Requesting packet %u", l + buffctl.packet_id_base);
            reqbody[reqctl->req_count] = l + buffctl.packet_id_base;
            reqctl->req_count++;
        }
    }

    if (reqctl->req_count > 0) {
        send_client_request(tcp_socket, reqctl);

        /* read retransmitted blocks via TCP */
        for (l = 0; l < reqctl->req_count; l++) {
            if (*freed_pkt) {
                *curr_pkt = *freed_pkt;
            }

            recv_server_ack(tcp_socket, *curr_pkt);

            *freed_pkt = packet_put(*curr_pkt);
            if (!(*freed_pkt)) {
                crit("Malformed packet on tcp socket");
            }
            if ((*freed_pkt)->data_size != 0) {
                crit("Malformed free packet slot or TCP data");
            }

            log(6, "Received retran packet %u", (*curr_pkt)->seq);
        }

        tot_reps += reqctl->req_count;
    }
}

/* Returns how many good packets received from UDP */
int recv_mcast(int tcp_socket, int udp_socket,
               struct packet_ctl **curr_pkt,
               struct packet_ctl **freed_pkt)
{
    int rcv_pkt_count;
    int got_sent;
    int maxfd;
    fd_set rfds;
    struct timeval tv;
    int res;

    maxfd = tcp_socket;
    if (maxfd < udp_socket) {
        maxfd = udp_socket;
    }
    maxfd++;
    FD_ZERO(&rfds);

    rcv_pkt_count = 0;
    got_sent = 0;

    if (buffctl.pkt_count != 0) {
        do {
            FD_SET(tcp_socket, &rfds);
            FD_SET(udp_socket, &rfds);
            tv.tv_sec = 5;
            tv.tv_usec = 0;

            res = select(maxfd, &rfds, 0, 0, &tv);
            if (res < 0) {
                crit("select error");
            }

            if (res == 0) {
                crit("select timed out");
            }

            /* Read multicast packet */
            if (FD_ISSET(udp_socket, &rfds)) {
                log(7, "Reading multicast packet");
                if (*freed_pkt) {
                    *curr_pkt = *freed_pkt;
                }

                res = recv(udp_socket, *curr_pkt, PACKET_SIZE, 0);
                if (res <= 0) {
                    crit("error on multicast socket");
                }

                if (res < sizeof(struct packet_ctl) ) {
                    log(7, "Truncated packet received (%d bytes)", res);
                } else if (res != (*curr_pkt)->data_size + sizeof(struct packet_ctl)) {
                    log(7,
                        "Truncated packet received (%d of %ld bytes)",
                        res, (*curr_pkt)->data_size + sizeof(struct packet_ctl));
                } else {
                    log(9, "Normal packet seq:%d", (*curr_pkt)->seq);
                    (*freed_pkt) = packet_put((*curr_pkt));
                    if (!(*freed_pkt)) {
                        log(5, "Malformed packet");
                    } else {
                        if ((*freed_pkt)->data_size == 0) {
                            rcv_pkt_count++;
                        } else {
                            log(6, "Duplicated packet");
                            tot_dups++;
                        }
                    }
                }
            } else if (FD_ISSET(tcp_socket, &rfds)) {
                /* Check TCP, only if there was no more data from UDP */
                log(6, "No more data path1");
                recv_server_sent(tcp_socket);
                got_sent = 1;
                break;
            }
        } while (rcv_pkt_count < buffctl.pkt_count);
    }

    if (got_sent == 0) {
        log(6, "No more data path2");
        recv_server_sent(tcp_socket);
    }

    return rcv_pkt_count;
}

void send_client_done(int tcp_socket)
{
    uint8_t cmd;

    /* Tell TCP server we are ready to receive */
    cmd = CLIENT_DONE;
    write(tcp_socket, &cmd, 1);
}

int main(int argc, char *argv[])
{
    int ms, ts;
    struct packet_ctl *alloc_pkt, *curr_pkt, *freed_pkt;
    int udp_rcv_count;
    u_short port = DEF_PORT;
    struct in_addr local_addr;

    if (argc < 3) {
        printf("Usage: %s <local_ip> <server_ip> [port]\n", argv[0]);
        return -1;
    }

    if (!inet_aton(argv[1], &local_addr)) {
        crit("can not resolve address: %s", argv[1]);
    }

    if (argc > 3) {
        port = atoi(argv[3]);
        if (!port) {
            port = DEF_PORT;
        }
    }

    buffer_init();
    /* Init first time packet slot */
    alloc_pkt = (struct packet_ctl *)wrapper_malloc(PACKET_SIZE);
    memset(alloc_pkt, 0, PACKET_SIZE);
    freed_pkt = curr_pkt = alloc_pkt;

    ts = init_tcp_client_socket(argv[2], port);
    recv_mcinfo(ts);
    ms = init_mcast_socket(&local_addr, &mcinfo.group);
    /* Do we need set_nonblock(ms)??? ; */

    /* Will do dummy run even if buffctl.pkt_count is zero at the first round */
    do { /* one buffer a round */
        packetctl_precheck();
        recv_buffctl(ts);
        send_client_ready(ts);

        udp_rcv_count = recv_mcast(ts, ms, &curr_pkt,&freed_pkt);
        if (udp_rcv_count == buffctl.pkt_count) {
            log(6, "All packets of current buffer received from UDP");
        } else {
            tcp_retransmition(ts, &curr_pkt, &freed_pkt);
        }

        tot_pkts += buffctl.pkt_count;
        tot_size += buffctl.buffer_size;
        log(1, "\rBuffer received %lld Bytes, %ld Packets(%ld Repeats %ld Dups)",
            tot_size, tot_pkts, tot_reps, tot_dups);

        if (buffctl.pkt_count) {
            buffer_flush(STDOUT_FILENO);
        }

        send_client_done(ts);
    } while (buffctl.pkt_count != 0);

    shutdown(ts, 2);
    close(ts);
    close(ms);
    log(1, "All buffers receive done.\n");
    return 0;
}
