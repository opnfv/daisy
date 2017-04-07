# Copyright (c) 2015 ZTE, Inc.

SPEC			= $(PACKAGE_NAME).spec

TARFILE			= $(PACKAGE_NAME)-$(VERSION).tar.gz

EXTRA_DIST		= autogen.sh $(SPEC).in \
			  build-aux/git-version-gen \
			  .version

AUTOMAKE_OPTIONS	= foreign

ACLOCAL_AMFLAGS		= -I m4

MAINTAINERCLEANFILES = Makefile.in aclocal.m4 configure depcomp \
			  config.guess config.sub missing install-sh \
			  autoheader automake autoconf \
			  autoscan.log configure.scan ltmain.sh test-driver config.h.in

noinst_HEADERS		= buffer.h misc.h server.h tcp-common.h tcp-queue.h udp-common.h

dist-clean-local:
	rm -f autoconf automake autoheader

clean-generic:
	rm -rf $(SPEC) $(TARFILE)

## make rpm/srpm section.

$(SPEC): $(SPEC).in
	rm -f $@-t $@
	ver="$(VERSION)" && \
	sed \
		-e "s#@version@#$$ver#g" \
	$< > $@-t; \
	chmod a-w $@-t
	mv $@-t $@

$(TARFILE):
	$(MAKE) dist

RPMBUILDOPTS	= --define "_sourcedir $(abs_builddir)" \
		  --define "_specdir $(abs_builddir)" \
		  --define "_builddir $(abs_builddir)" \
		  --define "_srcrpmdir $(abs_builddir)" \
		  --define "_rpmdir $(abs_builddir)"

srpm: clean
	$(MAKE) $(SPEC) $(TARFILE)
	rpmbuild $(WITH_LIST) $(RPMBUILDOPTS) --nodeps -bs $(SPEC)

rpm: clean _version
	$(MAKE) $(SPEC) $(TARFILE)
	rpmbuild $(WITH_LIST) $(RPMBUILDOPTS) -ba $(SPEC)

# release/versioning
BUILT_SOURCES	= .version
.version:
	echo $(VERSION) > $@-t && mv $@-t $@

dist-hook:
	echo $(VERSION) > $(distdir)/.tarball-version

.PHONY: _version

_version:
	cd $(srcdir) && rm -rf autom4te.cache .version && autoreconf -i
	$(MAKE) $(AM_MAKEFLAGS) Makefile

maintainer-clean-local:
	rm -rf m4

###

bin_PROGRAMS = jasmines jasminec

DEFAULT_INCLUDES = -I. -I/usr/include

jasmines_SOURCES = udp-common.c tcp-common.c buffer.c misc.c server.c server-udp.c server-tcp.c tcp-queue.c
jasminec_SOURCES = udp-common.c tcp-common.c buffer.c misc.c client.c

jasmines_LDADD = -lpthread
jasminec_LDADD = -lpthread
