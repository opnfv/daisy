/*##############################################################################
# Copyright (c) 2017 ZTE Coreporation and others.
# hu.zhijiang@zte.com.cn
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################*/

#ifndef _MCAST_MISC_H
#define _MCAST_MISC_H

#include <stdlib.h>
#include <stdio.h>
#include <error.h>
#include <errno.h>
#include <unistd.h>
#include <sys/syscall.h>
#define gettid() syscall(__NR_gettid)

#define level 6

#define crit(x, args...) do { \
    fprintf(stderr, "\nERROR: "); fprintf(stderr, x, ##args); \
    error(-1,errno, "\nERROR: [%s:%d:%ld] ", __FILE__, __LINE__, gettid()); \
} while (0);

#define log(l, f, args...) if (l < level) { \
    fprintf(stderr, "\n[%s:%d:%ld] ", __FILE__, __LINE__, gettid()); \
    fprintf(stderr, f, ##args); \
    fprintf(stderr, "\n"); \
}

struct sockaddr_in make_addr(char *addr, unsigned short port);
void * wrapper_malloc(size_t size);
void set_nonblock(int s);
size_t read_all(int fd, void *buf, size_t count);

#endif
