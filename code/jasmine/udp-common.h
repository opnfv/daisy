/*##############################################################################
# Copyright (c) 2017 ZTE Coreporation and others.
# hu.zhijiang@zte.com.cn
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################*/

#ifndef _MCAST_UDP_COMMON_H
#define _MCAST_UDP_COMMON_H

#include <unistd.h>
#include <netinet/ip.h>
#include <netinet/udp.h>

#define MCAST_DPORT DEF_PORT

#define MCAST_TTL 8
/*
 * Force reuse
 */
#define MCAST_REUSE 1

/*
 * Loop to let server host itself can receive data too.
 */
#define MCAST_LOOP 1
#define MCAST_ADDR_BASE "224.238.0."
#define MCAST_ADDR_SUFFIX "31"

// Initial data
struct mc_info {
    struct sockaddr_in group;
};

extern struct mc_info mcinfo;

// How to capture udp packets: tcpdump -i ethx udp -vv -n

int init_mcast_socket(struct in_addr *local_addr, struct sockaddr_in *maddr);
#endif
