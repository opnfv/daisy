/*##############################################################################
# Copyright (c) 2017 ZTE Coreporation and others.
# hu.zhijiang@zte.com.cn
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################*/

#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <pthread.h>
#include <signal.h>

#include "buffer.h"
#include "udp-common.h"
#include "misc.h"
#include "server.h"

void * udp_server_main(void *args)
{
    pthread_t pchild;
    struct sockaddr_in maddr;
    int ms;
    int i;
    struct semlink sl;
    char adr[128];
    long long total = 0;
  
    sprintf(adr, "%s%s", MCAST_ADDR_BASE, MCAST_ADDR_SUFFIX);
    maddr = make_addr(adr, server_port);
    mcinfo.group = maddr;
    ms = init_mcast_socket(&local_addr, &maddr);

    sl.this = spawn_thread(&pchild, tcp_server_main, 1);  
    sl.parent = NULL;

    buffer_init();

    /* Let TCP servers accept connections */
    sl_release_child(&sl);
    /* Wait until all TCP servers got all their clients */
    sl_wait_child(&sl);

    log(7, "UDP Server: All clients were accepted");

    do {
        /* one buffer round */

        i = buffer_fill(STDIN_FILENO);

        if (!client_count) {
            /* No need to send, make it the last run of main loop, also let
               TCP Server to do dummy run right away(not waiting until all
               data sent). */
            i = 0;
            buffctl.pkt_count = 0;
        }

        log(7, "Signal TCP Server to send buffctl");

        /* Tell tcp to Send headers, release child */
        sl_release_child(&sl);
        /* Wait all clients ready to start receiving */
        sl_wait_child(&sl);

        /* multicast data */
        while (i--) {
            sendto(ms, packetctl[i],
                   packetctl[i]->data_size + sizeof(struct packet_ctl), 0,
                   (struct sockaddr *)&maddr, sizeof(maddr));
        }

        log(7, "send finish");
        /* Tell tcp to Send SERVER_SENT, release child */
        sl_release_child(&sl);
        /* wait tcp to send SERVER_SENT */
        sl_wait_child(&sl);

        total = total + buffctl.buffer_size;
        log(1, "Buffer Done: sent %lld bytes", total);
    } while (buffctl.pkt_count);


    if (pthread_join(pchild, 0) < 0) {
        crit("pthread_join() TCP Server");
    }

    log(1, "All Done");
    close(ms);
    return 0;
}
