/*##############################################################################
# Copyright (c) 2017 ZTE Coreporation and others.
# hu.zhijiang@zte.com.cn
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################*/

#ifndef _MCAST_SERVER_H
#define _MCAST_SERVER_H

#include <pthread.h>
#include <semaphore.h>

struct semaphores {
    sem_t wait_parent;
    sem_t wait_child;
};

struct semlink {
    struct semaphores *this; /* used by parent to point to the struct semaphores
                                which it created during spawn child. */
    struct semaphores *parent; /* used by child to point to the struct
                                  semaphores which it created by parent */
};

void sl_wait_child(struct semlink *sl);
void sl_release_child(struct semlink *sl);
void sl_wait_parent(struct semlink *sl);
void sl_release_parent(struct semlink *sl);

/* Server state machine */
#define S_PREP 0
#define S_SYNC 1
#define S_SEND 2

extern int wait_count;
extern int client_count;
extern int server_port;
extern struct in_addr local_addr;
extern int sfd;

void *udp_server_main(void *args);
void *tcp_server_main(void *args);
void init_semaphores(struct semaphores *sp);
struct semaphores * spawn_thread(pthread_t *pchild,
                                 void *(*entry)(void *),
                                 int create_sems);

#define V(x) do { \
    if (sem_post(&x) < 0) { \
        crit("sem_post()"); \
    } \
} while(0)

#define P(x) do { \
    if (sem_wait(&x) != 0) { \
        crit("sem_wait()"); \
    } \
} while(0)

#endif
