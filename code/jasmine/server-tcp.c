/*##############################################################################
# Copyright (c) 2017 ZTE Coreporation and others.
# hu.zhijiang@zte.com.cn
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################*/

#include <unistd.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <fcntl.h>
#include <sys/poll.h>
#include <string.h>
#include <pthread.h>

#include "buffer.h"
#include "tcp-common.h"
#include "udp-common.h"
#include "tcp-queue.h"
#include "misc.h"
#include "server.h"

#define MAX_CLIENTS 128 /* Clients per TCP server */
#define TCP_BUFF_SIZE 65536

struct cdata {
    struct tcpq *tx;
    struct tcpq *rx;
    int await; /* non-zero if we are in the middle of receiving clients requests */
    struct sockaddr_in peer;
};

struct server_status_data {
    int state; /* state machine */
    int sync_count;
    int ccount;
    struct semlink sl;
    pthread_t pchild;

    struct pollfd ds[MAX_CLIENTS + 1];
    struct cdata cd[MAX_CLIENTS + 1];
    int cindex;
    int last_buff_pkt_count;
};

void init_sdata(struct server_status_data *sdata, void *thread_args)
{
    int i;

    sdata->sl.parent = (struct semaphores *)thread_args;
    sdata->sl.this = NULL;

    sdata->state = S_PREP;
    sdata->last_buff_pkt_count = 1;
    sdata->sync_count = 0;

    for (i = 0; i < MAX_CLIENTS + 1; i++) {
        sdata->ds[i].fd = -1;
        sdata->ds[i].events = POLLIN;
        sdata->cd[i].tx = tcpq_queue_init();
        sdata->cd[i].rx = tcpq_queue_init();
        sdata->cd[i].await = 0;
    }
}

/* disconnect one client and compress table */
void kill_client(struct server_status_data *sdata)
{
    struct pollfd *ds = sdata->ds;
    struct cdata *cd = sdata->cd;

    close((ds + sdata->cindex)->fd);
    tcpq_queue_free((cd + sdata->cindex)->rx);
    tcpq_queue_free((cd + sdata->cindex)->tx);

    /* Move last slot to this free slot and release the last slot */
    *(ds + sdata->cindex) = *(ds + sdata->ccount - 1);
    *(cd + sdata->cindex) = *(cd + sdata->ccount - 1);
    sdata->cindex--;
    sdata->ccount--;
    client_count--;
}

void send_buffctl_to_all_clients(struct server_status_data *sdata)
{
    int i;
    long send_sz;
    void *cpy;

    /* copy header to all queues */
    send_sz = sizeof(struct buffer_ctl);
    for (i = 1; i < sdata->ccount; i++) {
        cpy = wrapper_malloc(send_sz);
        memcpy(cpy, &buffctl, send_sz);
        tcpq_queue_tail(sdata->cd[i].tx, cpy, send_sz);
        sdata->ds[i].events |= POLLOUT;
    }
}

void send_sent_to_all_clients(struct server_status_data *sdata)
{
    int i;
    void *cpy;
    uint8_t byte = SERVER_SENT;

    /* Push data to clients */
    for (i = 1; i < sdata->ccount; i++) {
        cpy = wrapper_malloc(1);
        memcpy(cpy, &byte, 1);
        tcpq_queue_tail(sdata->cd[i].tx, cpy, 1);
        sdata->ds[i].events |= POLLOUT;
    }
}
void accept_clients(struct server_status_data *sdata)
{
	int res;
	int new_fd;
    socklen_t socklen;
    int poll_events;
    int timeout = -1;
    struct pollfd *ds = sdata->ds;
    struct cdata *cd = sdata->cd;

    ds->events = POLLIN;
    ds->revents = 0;
    sdata->ccount = 1;

    while (sdata->ccount <= MAX_CLIENTS && client_count < wait_count) {
        poll_events = poll(ds, 1, timeout);
        if (poll_events < 0) {
            crit("poll() failed");
        } else if (poll_events == 0) {
            log(2, "poll() returned with no results!");
            continue;
        }

        log(9, "poll: %d events", poll_events);

        if (ds->revents) {

            /* new connections come in */
            if (ds->revents & (POLLIN|POLLPRI)) {

                do {
                    socklen = sizeof((cd + sdata->ccount)->peer);
retry_accept:
                    new_fd = accept(ds->fd,
                                    (struct sockaddr *)&((cd + sdata->ccount)->peer),
                                    &socklen);
                    if (new_fd == -1 && errno == EINTR) {
                        goto retry_accept;
                    }

                    if (new_fd == -1) {
                        log(2, "accept() returned with error %d", errno);
                        break;
                    }

                    /* Send group info, before set non block */
                    res = write(new_fd, &mcinfo, sizeof(struct mc_info));
                    if (res < 0) {
                        log(3, "Error opening connection: %s",
                            inet_ntoa((cd + sdata->ccount)->peer.sin_addr));
                        close(new_fd);
                        continue;
                    }

                    /* Can set to non block becasue we will poll it in future. */
                    res = fcntl(new_fd, F_SETFL, O_NONBLOCK);
                    if (res == -1) {
                        log(2, "fcntl() returned with error %d", errno);
                        close(new_fd);
                        continue;
                    }

                    (ds + sdata->ccount)->fd = new_fd;

                    log(5, "New connection %d: %s",
                        sdata->ccount, inet_ntoa((cd + sdata->ccount)->peer.sin_addr));
                    sdata->ccount++;
                    client_count++;
                } while (sdata->ccount <= MAX_CLIENTS);

            } else {
                log(2, "Error on tcp socket");
            }

            poll_events--;
            ds->revents = 0;
        }
    }

    ds->events = 0;
}

void accept_clients_may_spawn(struct server_status_data *sdata)
{
    /* Wait the parent to let us accpet clients */
    sl_wait_parent(&(sdata->sl));

    sdata->ds[0].fd = sfd;
    accept_clients(sdata);
    if (client_count < wait_count) {
        sdata->sl.this = spawn_thread(&sdata->pchild, tcp_server_main, 1);

        /* Let child TCP servers accept connections */
        sl_release_child(&(sdata->sl));
        /* Wait until all childern TCP servers got all their clients */
        sl_wait_child(&(sdata->sl));
    }

    /* Tell parent all client are accepted/connected */
    sl_release_parent(&(sdata->sl));
}

void keep_on_receiving_client_request(struct server_status_data *sdata)
{
    char buf[TCP_BUFF_SIZE];
    void *cpy;
    struct request_ctl *req;
    uint32_t *rqb;
    struct packet_ctl *ans;
    long rq_index;
    long total_sz;

    long read_out;
    struct pollfd *ds;
    struct cdata *cd;

    ds = &(sdata->ds[sdata->cindex]);
    cd = &(sdata->cd[sdata->cindex]);

    read_out = read(ds->fd, buf, cd->await);
    if (read_out <= 0) {
        log(5, "Client disconnected (r): %s",
            inet_ntoa(cd->peer.sin_addr));
        kill_client(sdata);
        return;
    }

    log(7, "New data (%ld + %ld) on conn %d: %s",
        read_out, tcpq_queue_dsize(cd->rx), sdata->cindex,
        inet_ntoa(cd->peer.sin_addr));
    cpy = wrapper_malloc(read_out);
    memcpy(cpy, buf, read_out);
    tcpq_queue_tail(cd->rx, cpy, read_out);
    cd->await -= read_out;

    /* Full header received */
    if (tcpq_queue_dsize(cd->rx) == sizeof(struct request_ctl)) {
        cpy = tcpq_queue_flat_peek(cd->rx, &read_out);
        req = (struct request_ctl *)cpy;
        cd->await = req->req_count * sizeof(uint32_t);
        log(6, "Client request for %u packets on %d: %s",
            req->req_count, sdata->cindex, inet_ntoa(cd->peer.sin_addr));
        /* req->rqc may be zero? So do not return from here */
    }

    /* Whole request(struct request_ctl + all rq blocks) received */
    if (cd->await == 0) {
        cpy = tcpq_dqueue_flat(cd->rx, &read_out);
        req = (struct request_ctl *)cpy;
        rqb = (uint32_t *) (cpy + sizeof(struct request_ctl));
        for (rq_index = 0; rq_index < req->req_count; rq_index++) {
            ans = packet_get(*(rqb + rq_index));
            total_sz = ans->data_size + sizeof(struct packet_ctl);
            log(6, "Send packet %u (%u bytes) on %d",
                rqb[rq_index], ans->data_size, sdata->cindex);
            cpy = wrapper_malloc(total_sz);
            memcpy(cpy, ans, total_sz);
            tcpq_queue_tail(cd->tx, cpy, total_sz);
        }

        if (rq_index > 0) {
            /* Data need to be sent out */
            ds->events |= POLLOUT;
        }
    }
}

void handle_error_event(struct server_status_data *sdata)
{
    struct cdata *cd;

    cd = &(sdata->cd[sdata->cindex]);
    log(5, "Closing connection %d: %s",
        sdata->cindex, inet_ntoa(cd->peer.sin_addr));
    kill_client(sdata);
}

void handle_client_ready(struct server_status_data *sdata)
{
    if (sdata->state == S_SYNC) {
        sdata->sync_count++;

        log(7, "Client SYNC %d of %d",
            sdata->sync_count, sdata->ccount - 1);

        if (sdata->sync_count == sdata->ccount - 1) {
            /* All client SYNC done */
            sdata->state = S_SEND;

            /* Wait child ready */
            sl_wait_child(&(sdata->sl));
            /* Tell parent I am ready, release parent */
            sl_release_parent(&(sdata->sl));

            /* Wait parent to send mcast */
            sl_wait_parent(&(sdata->sl));
            /* tell child mcast done, release child */
            sl_release_child(&(sdata->sl));

            send_sent_to_all_clients(sdata);
        }
    }
}

void handle_client_done(struct server_status_data *sdata)
{
    if (sdata->state == S_SEND) {
        log(7, "Client START %d of %d",
            sdata->sync_count, sdata->ccount - 1);

        sdata->sync_count--;
        if (sdata->sync_count == 0) {
            /* Got all client START */
            sdata->state = S_PREP;
            log(7, "All received, now tell UDP Server prepare next buffer");
            /* Remeber old buffctl.pkt_count before it change */
            sdata->last_buff_pkt_count = buffctl.pkt_count;

            /* Wait child clients done */
            sl_wait_child(&(sdata->sl));
            /* Tell parent all our clients are done, release parent */
            sl_release_parent(&(sdata->sl));
        }
    }
}

void handle_client_events(struct server_status_data *sdata)
{
    struct pollfd *ds;
    struct cdata *cd;
    int read_out;
    uint8_t msgtype;

    ds = &(sdata->ds[sdata->cindex]);
    cd = &(sdata->cd[sdata->cindex]);

    /* read message type */
    read_out = read(ds->fd, &msgtype, 1);
    if (read_out <= 0) {
        log(5, "Client disconnected due to read error %d, ret:%d (r): %s",
            errno, read_out, inet_ntoa(cd->peer.sin_addr));
        kill_client(sdata);
        return; /* continue to check other clients */
    }

    switch (msgtype) {
    case CLIENT_READY:
        handle_client_ready(sdata);
        break;
    case CLIENT_DONE:
        handle_client_done(sdata);
        break;
    case CLIENT_REQ:
        /* wait a whole struct request_ctl */
        cd->await = sizeof(struct request_ctl);
        break;
    default:
        log(4, "Wrong message type from %s",
            inet_ntoa(cd->peer.sin_addr));
        break;
    }
}

void handle_pullin_event(struct server_status_data *sdata)
{
    struct cdata *cd;

    cd = &(sdata->cd[sdata->cindex]);

    /* Await is set only for repeat request */
    if (cd->await) {
        keep_on_receiving_client_request(sdata);
    } else {
        handle_client_events(sdata);
    }
}

void handle_pullout_event(struct server_status_data *sdata)
{
    char buf[TCP_BUFF_SIZE];
    struct pollfd *ds;
    struct cdata *cd;
    long transmit_sz;
    void *cpy;
    long written_in;

    ds = &(sdata->ds[sdata->cindex]);
    cd = &(sdata->cd[sdata->cindex]);

    if (cd->tx->count == 0) {
        ds->events = POLLIN; /* Just make sure */
        return;
    }

    log(7, "handle_pullout_event servs No.%d conn", sdata->cindex);

    /* If there is some data to be sent, try to do it now */
    cpy = tcpq_dequeue_head(cd->tx, &transmit_sz);
    memcpy(buf, cpy, transmit_sz);
    free(cpy);

    written_in = write(ds->fd, buf, transmit_sz);
    if (written_in <= 0) {
        log(5, "Client disconnected (w): %s",
            inet_ntoa(cd->peer.sin_addr));
        kill_client(sdata);
        return;
    }

    if (written_in != transmit_sz) {
        log(6, "Partial wrote: %ld out of %ld bytes sent",
            written_in, transmit_sz);
        cpy = wrapper_malloc(transmit_sz - written_in);
        memcpy(cpy, buf + written_in, transmit_sz - written_in);
        tcpq_queue_head(cd->tx, cpy, transmit_sz - written_in);
    } else {
        log(7, "Sent %ld bytes to %s",
            written_in, inet_ntoa(cd->peer.sin_addr));
        if (cd->tx->count == 0) {
            /* Do not listen pollout event anymore */
            ds->events = POLLIN;
        }
    }
}

void check_clients(struct server_status_data *sdata)
{
    int poll_events;
    struct pollfd *ds;
    int timeout = -1;

    if (sdata->ccount == 1) {
        log(5, "No more clients, start exiting. s,c,p:%d,%d,%d",
            sdata->state, sdata->ccount, buffctl.pkt_count);
        /* No client existed */
        switch(sdata->state) {
        case S_SYNC:
            /* Wait all children ready */
            sl_wait_child(&(sdata->sl));
            /* Tell parent I am ready, release parent */
            sl_release_parent(&(sdata->sl));

            /* Wait parent to send mcast */
            sl_wait_parent(&(sdata->sl));
            /* Tell child mcast done, release child */
            sl_release_child(&(sdata->sl));
        case S_SEND:
            sdata->state = S_PREP;
            /* Remeber old buffctl.pkt_count before it change */
            sdata->last_buff_pkt_count = buffctl.pkt_count;

            /* Wait child clients done */
            sl_wait_child(&(sdata->sl));
            /* Tell parent all our clients are done */
            sl_release_parent(&(sdata->sl));
        }
        /* return to main loop to finish the dummy run */
        return;
    }

    /* poll clients only */
    poll_events = poll(&(sdata->ds[1]), sdata->ccount - 1, timeout);
    if (poll_events < 0) {
        crit("poll() failed");
    } else if (poll_events == 0) {
        log(2, "poll() returned with no results!");
        return;
    }

    log(9, "poll clients: %d events", poll_events);

    /* check all connected clients */
    for (sdata->cindex = 1; sdata->cindex < sdata->ccount; sdata->cindex++) {
        ds = &(sdata->ds[sdata->cindex]);
        if (!ds->revents) {
            continue;
        }

        if (ds->revents & (POLLERR|POLLHUP|POLLNVAL)) {
            handle_error_event(sdata);
        } else if (ds->revents & (POLLIN|POLLPRI)) {
            handle_pullin_event(sdata);
        } else if (ds->revents & POLLOUT) {
            handle_pullout_event(sdata);
        }
    }
}

void * tcp_server_main(void *args)
{
    int i;
    struct server_status_data ssdata;
    struct server_status_data *sdata;

    sdata = &ssdata;
    init_sdata(sdata, args);

    accept_clients_may_spawn(sdata);

    while (1) {
        if (sdata->state == S_PREP) {
            /* Wait UDP server to prepare the buffctl of this round to send */
            sl_wait_parent(&(sdata->sl));
            log(6, "After waiting UDP server preparation. s,c,p:%d,%d,%d",
                sdata->state, sdata->ccount - 1, buffctl.pkt_count);
            /* Tell children buffer pareparation done, release child */
            sl_release_child(&(sdata->sl));
            send_buffctl_to_all_clients(sdata);
            sdata->state = S_SYNC;
        }

        check_clients(sdata);

        if (sdata->state == S_PREP && sdata->last_buff_pkt_count == 0) {
            log(5, "No more output, TCP server finished");
            if (sdata->sl.this && pthread_join(sdata->pchild, 0) < 0) {
                crit("pthread_join()");
            }

            /* shutdown conn to clients */
            for (i = sdata->ccount - 1; i > 0; i--) {
                shutdown((sdata->ds[i]).fd, 2);
            }

            if (!sdata->sl.this) {
                /* leaf server */
                close(sfd);
                sfd = -1;
            }
            return 0;
        }
    }
}
