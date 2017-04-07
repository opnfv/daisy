/*##############################################################################
# Copyright (c) 2017 ZTE Coreporation and others.
# hu.zhijiang@zte.com.cn
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################*/

#include <sys/types.h>
#include <sys/socket.h>
#include <arpa/inet.h>

#include "buffer.h"
#include "tcp-common.h"
#include "misc.h"

int init_tcp_server_socket(char *addr, unsigned short port) 
{
    int s;
    struct sockaddr_in sin;

    port = port ? port : TCP_DPORT;
    sin = make_addr(addr, port);

    if ((s = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
        crit("socket() failed");
    }

    if (bind(s, (struct sockaddr *)&sin, sizeof(struct sockaddr_in)) < 0) {
        crit("bind() failed, error binding tcp socket");
    }

    if (listen(s, 5) < 0) {
        crit("listen() failed, error listening on socket");
    }

    log(4, "init_tcp_server_socket %s:%d", inet_ntoa(sin.sin_addr), port);
    return s;
}

int init_tcp_client_socket(char *addr, unsigned short port)
{
    int s;
    struct sockaddr_in sin;

    port = port ? port : TCP_DPORT;
    sin = make_addr(addr, port);

    if ((s = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
        crit("socket() failed");
    }

    if (connect(s, (struct sockaddr *)&sin, sizeof(struct sockaddr_in)) < 0) {
        crit("connect() failed");
    }

    log(4, "init_tcp_client_socket %s:%d", inet_ntoa(sin.sin_addr), port);
    return s;
}
