/*##############################################################################
# Copyright (c) 2017 ZTE Coreporation and others.
# hu.zhijiang@zte.com.cn
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################*/

#include <stdlib.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <sys/types.h>
#include <fcntl.h>

#include "misc.h"

struct sockaddr_in make_addr(char *addr, unsigned short port)
{
    struct sockaddr_in sin;

    sin.sin_family = AF_INET;
    if (!addr) {
        sin.sin_addr.s_addr = htonl(INADDR_ANY);
    } else {
        if (!inet_aton(addr, &sin.sin_addr))
            crit("cant resolve address: %s", addr);
    }
    sin.sin_port = htons(port);
    return sin;
}

/* Better than using a macro */
void set_nonblock(int s)
{
    if (fcntl(s, F_SETFL, O_NONBLOCK) < 0) {
        crit("set_nonblock failed, can't set O_NONBLOCK");
    }
}

void * wrapper_malloc(size_t size)
{
    void * res;

    if (size == 0) {
        crit("wrapper_malloc: malloc 0 size not allowed");
    }

    res = malloc(size);
    if (res == NULL) {
        crit("wrapper_malloc: malloc failed");
    }

    return res;
}

size_t read_all(int fd, void *buf, size_t count)
{
    size_t t = 0;
    size_t r = 0;

    while (count > 0) {
        r = read(fd, buf + t, count);
        if (r <= 0) {
            return t ? t : r;
        }

        t += r;
        count -= r;
    }

    return t;
}
