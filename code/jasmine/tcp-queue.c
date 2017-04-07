/*##############################################################################
# Copyright (c) 2017 ZTE Coreporation and others.
# hu.zhijiang@zte.com.cn
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################*/

/* TCP poll message single linked queue */
#include <stdlib.h>
#include <string.h>

#include "misc.h"
#include "tcp-queue.h"

void tcpq_queue_tail(struct tcpq *q, void *data, long size)
{
    struct qmsg *tmp;

    if (!q) {
        return;
    }

    tmp = (struct qmsg *)wrapper_malloc(sizeof(struct qmsg));
    tmp->next = NULL;

    if (!q->head) {
        q->head = q->tail = tmp; 
    } else {
        q->tail->next = tmp; 
        q->tail = tmp;
    }

    q->tail->data = data;
    q->tail->size = size;
    q->size += size;
    q->count++;
}

void tcpq_queue_head(struct tcpq *q, void *data, long size)
{
    struct qmsg *tmp;

    if (!q) {
        return;
    }

    tmp = (struct qmsg *)wrapper_malloc(sizeof(struct qmsg));
    tmp->next = NULL;

    if (!q->head) {
        q->head = q->tail = tmp; 
    } else {
        tmp->next = q->head;
        q->head = tmp;
    }

    q->head->data = data;
    q->head->size = size;
    q->size += size;
    q->count++;
}

void * tcpq_dequeue_head(struct tcpq *q, long *size)
{
    void *res = NULL;
    struct qmsg *tmp;

    if (q && q->head) {
        res = q->head->data;
        *size = q->head->size;

        tmp = q->head;
        q->head = q->head->next;
        if (!q->head) {
            q->tail = NULL;
        }

        free(tmp);
        q->count--;
        q->size -= *size;
    }
    return res;
}

void * tcpq_queue_peek(struct tcpq *q, long *size)
{
    if (q && q->head) {
        *size = q->head->size;
        return q->head->data;
    }

    return NULL;
}

long tcpq_queue_dsize(struct tcpq *q)
{
    if (q) {
        return q->size;
    }

    return 0;
}

void tcpq_queue_free(struct tcpq *q)
{
    struct qmsg *tmp;

    if (!q) {
        return;
    }

    while (q->head) {
        tmp = q->head;
        q->head = tmp->next;
        free(tmp->data);
        free(tmp);
    }

    q->count = 0;
    q->size = 0;
    q->head = q->tail = NULL;
} 

struct tcpq * tcpq_queue_init(void)
{
    struct tcpq *q = wrapper_malloc(sizeof(struct tcpq)); 

    q->count = 0;
    q->size = 0;
    q->head = q->tail = NULL;
    return q;
}

void * tcpq_dqueue_flat(struct tcpq *q, long *size)
{
    void *res;
    struct qmsg *tmp;
    long offs = 0;

    if (!q || q->count == 0) {
        return NULL;
    }

    res = wrapper_malloc(q->size);
    *size = q->size;

    while (q->head) {
        memcpy(res + offs, q->head->data, q->head->size);
        offs += q->head->size;

        tmp = q->head;
        q->head = tmp->next;
        free(tmp->data);
        free(tmp);
    }
    tcpq_queue_free(q);
    return res; 
}

void * tcpq_queue_flat_peek(struct tcpq *q, long *size)
{
    void *cpy;

    if (!q) {
        return NULL;
    }

    if (q->count > 1) {
        cpy = tcpq_dqueue_flat(q, size);
        tcpq_queue_tail(q, cpy, *size); /* use tcpq_queue_head is also OK */
    } else {
        cpy = tcpq_queue_peek(q, size);
    }

    return cpy;
}
