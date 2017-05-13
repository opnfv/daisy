#                                               -*- Autoconf -*-
# Process this file with autoconf to produce a configure script.

# bootstrap / init
AC_PREREQ([2.61])

AC_INIT([jasmine],
	[1.2],
	[hu.zhijiang@zte.com.cn])

AC_USE_SYSTEM_EXTENSIONS

AM_INIT_AUTOMAKE([-Wno-portability])

AC_CONFIG_HEADER([config.h])

AC_CONFIG_MACRO_DIR([m4])

AC_SUBST(WITH_LIST, [""])

dnl Fix default variables - "prefix" variable if not specified
if test "$prefix" = "NONE"; then
	prefix="/usr"

	dnl Fix "localstatedir" variable if not specified
	if test "$localstatedir" = "\${prefix}/var"; then
		localstatedir="/var"
	fi
	dnl Fix "sysconfdir" variable if not specified
	if test "$sysconfdir" = "\${prefix}/etc"; then
		sysconfdir="/etc"
	fi
	dnl Fix "libdir" variable if not specified
	if test "$libdir" = "\${exec_prefix}/lib"; then
		if test -e /usr/lib64; then
			libdir="/usr/lib64"
		else
			libdir="/usr/lib"
		fi
	fi
fi

# Checks for programs.
AC_PATH_PROG([BASHPATH], [bash])

AC_CONFIG_FILES([Makefile])

PACKAGE_FEATURES=""

ENV_CFLAGS="$CFLAGS"
OPT_CFLAGS=""
GDB_FLAGS=""
EXTRA_WARNINGS="-Wall"
CFLAGS="$ENV_CFLAGS $OPT_CFLAGS $GDB_FLAGS $EXTRA_WARNINGS"

# substitute what we need:
AC_SUBST([BASHPATH])

AC_OUTPUT

AC_MSG_RESULT([  Version                  = ${PACKAGE_VERSION}])
AC_MSG_RESULT([  Final        CFLAGS      = ${CFLAGS}])
AC_MSG_RESULT([  Final        CPPFLAGS    = ${CPPFLAGS}])
AC_MSG_RESULT([  Final        LDFLAGS     = ${LDFLAGS}])
AC_MSG_RESULT([  Features                 = ${PACKAGE_FEATURES}])
