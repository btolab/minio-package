#!/bin/bash

set -o pipefail -o errtrace -o errexit -o nounset -o functrace
shopt -s nullglob

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

PROJECT=$1

cd "${SCRIPT_PATH}/${PROJECT}" || exit 1

SOURCES=("minio.service")
for SOURCE in "${SOURCES[@]}" ; do
    cp -v "${SCRIPT_PATH}/${SOURCE}" "${SRCDIR}/"
done

spectool -g -C "${SRCDIR}" ../"${PROJECT}.spec"

cp ../"${PROJECT}.spec" "${SCRATCH}"/rpm.spec

X=0
# shellcheck disable=SC2045
for PATCH in $(ls -r ../patches/"${PROJECT}"/*.patch) ; do
    cp "${PATCH}" "${SRCDIR}/"
    PL="Patch10${X}: $(basename "${PATCH}")"
    PA="%patch -P 10${X} -p1"
    sed -i -e "/^Source0/a ${PL}" "${SCRATCH}"/rpm.spec
    sed -i -e "/^%setup /a ${PA}" "${SCRATCH}"/rpm.spec
    X=$((X+1))
done

rpmbuild --define "_topdir ${SCRATCH}/rpmbuild" --define "_rpmdir ${RPMDIR}" -bb "${SCRATCH}/rpm.spec"
