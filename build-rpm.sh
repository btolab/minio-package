#!/bin/bash

set -o pipefail -o errtrace -o errexit -o nounset -o functrace

traperror() {
    local el=${1:=??} ec=${2:=??} lc="$BASH_COMMAND"
    printf "ERROR in %s : line %d error %d\\n      [%s]\\n" "$0" "$el" "$ec" "$lc" 1>&2
    exit "${2:=1}"
}
trap 'traperror ${LINENO} ${?}' ERR
logger() { echo "$(date +"[%d-%h-%Y %H:%M:%S %Z]")" "$*"; } # add tee here for "real" logging

SCRIPT_NAME=$(basename "$0")

finish() {
    if [[ -n $SCRATCH && -d $SCRATCH ]]; then
        rm -rf "${SCRATCH}"
    fi
}
trap finish EXIT
SCRATCH=$(mktemp -d -t "${SCRIPT_NAME}".XXXXXXXX)

SCRIPT_PATH="$(git rev-parse --show-toplevel)"

RPMDIR="${SCRIPT_PATH}/artifacts"
SRCDIR=$(rpm --define "_topdir ${SCRATCH}/rpmbuild" --eval "%{_sourcedir}")
SPECDIR=$(rpm --define "_topdir ${SCRATCH}/rpmbuild" --eval "%{_specdir}")
SRPMDIR=$(rpm --define "_topdir ${SCRATCH}/rpmbuild" --eval "%{_srcrpmdir}")
BUILDDIR=$(rpm --define "_topdir ${SCRATCH}/rpmbuild" --eval "%{_builddir}")

for i in $RPMDIR $SRCDIR $SPECDIR $SRPMDIR $BUILDDIR ; do
	[ ! -d "$i" ] && mkdir -p "$i"
done

cd "${SCRIPT_PATH}/minio" || exit 1

SOURCES=("minio.service")
for SOURCE in "${SOURCES[@]}" ; do
    cp -v "${SCRIPT_PATH}/${SOURCE}" "${SRCDIR}/"
done

spectool -g -C "${SRCDIR}" ../minio.spec

rpmbuild --define "_topdir ${SCRATCH}/rpmbuild" --define "_rpmdir ${RPMDIR}" -bb "${SCRIPT_PATH}/minio.spec"
