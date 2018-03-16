#!/bin/sh
##############################################################################
# Copyright (c) 2018 ZTE Corporation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Run this to generate all the initial makefiles, etc.
mkdir -p m4
echo Building configuration system...
autoreconf -i
