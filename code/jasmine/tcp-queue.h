/*##############################################################################
# Copyright (c) 2017 ZTE Coreporation and others.
# hu.zhijiang@zte.com.cn
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################*/

#ifndef _MCAST_TCP_QUEUE_H
#define _MCAST_TCP_QUEUE_H

struct tcpq {
    struct qmsg *head, *tail;
    long count; /* message count in a queue */
    long size; /* Total data size of a queue */
};

struct qmsg {
    struct qmsg *next;
    void *data;
    long size;
};

struct tcpq * tcpq_queue_init(void);
void tcpq_queue_free(struct tcpq *q);
long tcpq_queue_dsize(struct tcpq *q);
void tcpq_queue_tail(struct tcpq *q, void *data, long size);
void tcpq_queue_head(struct tcpq *q, void *data, long size);
void * tcpq_dequeue_head(struct tcpq *q, long *size);
void * tcpq_queue_peek(struct tcpq *q, long *size);
void * tcpq_dqueue_flat(struct tcpq *q, long *size);
void * tcpq_queue_flat_peek(struct tcpq *q, long *size);

#endif
