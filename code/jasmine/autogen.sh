#!/bin/sh
# Run this to generate all the initial makefiles, etc.
mkdir -p m4
echo Building configuration system...
autoreconf -i
