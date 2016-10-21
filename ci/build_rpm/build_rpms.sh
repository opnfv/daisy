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
set -eux
DAISYDIR = $1
function build_rpm_pkg {
      sudo docker build -t daisy4nfv_rpm .
      sudo docker run --rm -v DAISYDIR:/opt/daisy4nfv -t  daisy4nfv_rpm \
                      /opt/daisy4nfv/ci/build_rpm/build_rpms_docker.sh
}

function cleanup_container {
	containers_to_kill=$(docker ps --filter "label=daisy_image_version" \
		--format "{{.Names}}" -a)

	if [[ -z "$containers_to_kill" ]]; then
		echo "No containers to cleanup."
	else
		volumes_to_remove=$(docker inspect -f \
			'{{range .Mounts}} {{printf "%s\n" .Name }}{{end}}' \
			${containers_to_kill} | egrep -v '(^\s*$)' | sort | uniq)
	fi

	images_to_delete=$(docker images -a --filter "label=daisy_image_version" \
		--format "{{.ID}}")

	echo "Stopping containers... $containers_to_kill"
	(docker stop -t 2 ${containers_to_kill} 2>&1) > /dev/null

	echo "Removing containers... $containers_to_kill"
	(docker rm -v -f ${containers_to_kill} 2>&1) > /dev/null

	echo "Removing volumes... $volumes_to_remove"
	(docker volume rm ${volumes_to_remove} 2>&1) > /dev/null

	echo "Removing images... $images_to_delete"
	if [[ -z "$images_to_delete" ]]; then
		echo "No images to cleanup"
	else
		docker rmi -f $images_to_delete
	fi
}

build_rpm_pkg
cleanup_container
