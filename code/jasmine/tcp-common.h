/*##############################################################################
# Copyright (c) 2017 ZTE Coreporation and others.
# hu.zhijiang@zte.com.cn
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################*/

#ifndef _MCAST_TCP_COMMON_H
#define _MCAST_TCP_COMMON_H

#define TCP_DPORT DEF_PORT

int init_tcp_server_socket(char *addr, unsigned short port);
int init_tcp_client_socket(char *addr, unsigned short port);

#endif
