#!/bin/bash
##############################################################################
# Copyright (c) 2016 ZTE Coreporation and others.
# hu.zhijiang@zte.com.cn
# sun.jing22@zte.com.cn
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# TODO: Let JJB to pass $WORKDIR instead of $BUILD_OUTPUT
DAISYDIR=$1/../


MD5_PATH=`exec <&- 2>&-; which md5sum || type md5sum`
echo $MD5_PATH

test -x $MD5_PATH || MD5_PATH=`exec <&- 2>&-; which md5 || type md5`
echo $MD5_PATH

test -x $MD5_PATH || MD5_PATH=`exec <&- 2>&-; which digest || type digest`RG=

echo $MD5_PATH

MD5_ARG=

tmpfile="${TMPDIR:=/tmp}/mkself$$"
echo "test" > $tmpfile
md5sum=`cat "$tmpfile" | eval "$MD5_PATH $MD5_ARG" | cut -b-32`;
rm -f "$tmpfile"

echo $md5sum









cd ci/build_rpm
./build_rpms.sh $DAISYDIR


