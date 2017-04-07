/*##############################################################################
# Copyright (c) 2017 ZTE Coreporation and others.
# hu.zhijiang@zte.com.cn
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################*/

#include <fcntl.h>
#include <net/if.h>
#include <sys/ioctl.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <arpa/inet.h>

#include "buffer.h"
#include "udp-common.h"
#include "misc.h"

struct mc_info mcinfo;

int init_mcast_socket(struct in_addr *local_addr,
                      struct sockaddr_in *maddr)
{
    struct ip_mreqn mreqn;  /* multicast request new */
    int ms;  /* multicast socket */
    u_short msock_port;
    struct sockaddr_in bind_addr;

    int msock_reuse = MCAST_REUSE;
    u_char msock_loop = MCAST_LOOP;
    u_char msock_ttl = MCAST_TTL; 

    if ((ms = socket(PF_INET, SOCK_DGRAM, 0)) < 0) {
        crit("socket() failed, error allocating multicast socket");
    }

    // In order to let client and server on same host to use same port 
    if (setsockopt(ms, SOL_SOCKET, SO_REUSEADDR,
        &msock_reuse, sizeof(msock_reuse)) < 0) {
        crit("setsockopt() failed, can't set reuse flag");
    }

    if (setsockopt(ms, IPPROTO_IP, IP_MULTICAST_TTL,
        &msock_ttl,sizeof(msock_ttl)) < 0) {
        crit("setsockopt() failed, can't set ttl value");
    }

    if (setsockopt(ms, IPPROTO_IP, IP_MULTICAST_LOOP,
        &msock_loop, sizeof(msock_loop)) < 0) {
        crit("setsockopt() failed, can't set multicast packet looping");
    }

    /* TODO: Do we neet non-block? */

    log(4, "Using multicast address: %s:%d",
        inet_ntoa(maddr->sin_addr), ntohs(maddr->sin_port));

	mreqn.imr_multiaddr = maddr->sin_addr;
	mreqn.imr_address = *local_addr;
    mreqn.imr_ifindex = 0;

    /* Interface and remote mcast address choosing */

	/* This tell interface which has mreqn.imr_address to join
       mreqn.imr_multiaddr group, it has nothing to do with socket, port, and
       mreqn.imr_address. */
    if (setsockopt(ms, IPPROTO_IP, IP_ADD_MEMBERSHIP,
        &mreqn, sizeof(mreqn)) < 0) {
        crit("setsockopt() failed, %s can't join multicast group",
             inet_ntoa(*local_addr));
    }

    /* local address choosing */

	/* This tell kernel to use interface which has mreqn.imr_address as device 
       and mreqn.imr_address as source addr when sending any multicast through
       socket. */
	if (setsockopt(ms, IPPROTO_IP, IP_MULTICAST_IF,
        &mreqn, sizeof(mreqn)) < 0) {
		crit("setsockopt() failed to IP_MULTICAST_IF.\n");
	}

    /* Local port choosing, remote port is choosed when calling sendto()! */

	/* This let us uses specific udp port number as source port when sending
       any multicast datagrams. So ip in maddr is useless here and should be
       INADDR_ANY, otherwise, bind will return Invalid argument. */
    msock_port = ntohs(maddr->sin_port);
    bind_addr = make_addr(0, msock_port); 
    if (bind(ms, (struct sockaddr *)&bind_addr, sizeof(bind_addr)) < 0) {
        crit("bind() error, can't bind mcast port");
    }
     
    return ms;
}
