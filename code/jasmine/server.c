/*##############################################################################
# Copyright (c) 2017 ZTE Coreporation and others.
# hu.zhijiang@zte.com.cn
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################*/

#include <pthread.h>
#include <string.h>
#include <stdlib.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>

#include "buffer.h"
#include "tcp-common.h"
#include "misc.h"
#include "server.h"

/* Global variables shared among server*.c */
int wait_count = 0;
int client_count = 0;
int server_port = DEF_PORT; /* Currently for both UDP and TCP */
struct in_addr local_addr;
/* listen socket - global for all TCP threads */
int sfd = -1;

void init_semaphores(struct semaphores *sp)
{
    if (sem_init(&sp->wait_parent, 0, 0) < 0) {
        crit("sem_init() wait_parent");
    }

    if (sem_init(&sp->wait_child, 0, 0) < 0) {
        crit("sem_init() wait_child");
    }
}

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
    P(sl->parent->wait_parent);
}

void sl_release_parent(struct semlink *sl)
{
    V(sl->parent->wait_child);
}

/* Wrapper for pthread_create, additionaly may initialize/pass thru 
   a semaphores parameter */
struct semaphores * spawn_thread(pthread_t *pchild,
                                 void *(*entry)(void *),
                                 int create_sems)
{
    struct semaphores *sp = NULL;

    if (create_sems != 0) {
        sp = (struct semaphores *) wrapper_malloc(sizeof(struct semaphores));
        init_semaphores(sp);
    }

    if (pthread_create(pchild, 0, entry, (void *)sp) != 0) {
        crit("pthread_create");
    }
    return sp;
}

int main(int argc, char *argv[])
{
    pthread_t pchild;

    log(9, "buffer size:%ld, buffer head size:%ld, data size:%ld",
        PACKET_SIZE, sizeof(struct packet_ctl), PACKET_PAYLOAD_SIZE);

    if (argc < 3) {
        printf("Usage: %s local_ip num_of_clients [port]\n", argv[0]);
        return -1;
    }

    if (!inet_aton(argv[1], &local_addr)) {
        crit("can not resolve address: %s", argv[1]);
    }

    wait_count = atoi(argv[2]);
    if (!wait_count) {
        crit("can not serv to 0 client\n");
    }

    if (argc > 3) {
        server_port = atoi(argv[3]);
        if (!server_port) {
            server_port = DEF_PORT;
        }
    }

    /* sfd is shared by all TCP threads as sdata->ds[0].fd */
    sfd = init_tcp_server_socket(0, server_port);
    set_nonblock(sfd);

    /* start UDP servers thread */
    (void)spawn_thread(&pchild, udp_server_main, 0);
    if (pthread_join(pchild, 0) < 0) {
        crit("pthread_join() UDP Server");
    }

    return 0;
}
