#!/usr/bin/env bash

# SPDX-License-Identifier: Apache-2.0
#
# Tests for the input validation helpers in uki/install.sh. The installer is
# sourced, which stops before the first prompt (see the BASH_SOURCE guard), so
# nothing here touches a disk and no root is needed.

# Literals below deliberately contain unexpanded $(...), and the installer is
# sourced rather than passed to shellcheck.
# shellcheck disable=SC1091,SC2016
set -uo pipefail

here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
source "${here}/install.sh"
cd "${here}" || exit 1
set +e

pass=0
fail=0

ok() {
    pass=$((pass + 1))
    printf 'ok %d - %s\n' "$((pass + fail))" "$1"
}

not_ok() {
    fail=$((fail + 1))
    printf 'not ok %d - %s\n' "$((pass + fail))" "$1"
    printf '    %s\n' "$2"
}

accept() {
    local desc=$1
    shift
    if "$@" > /dev/null 2>&1; then
        ok "${desc}"
    else
        not_ok "${desc}" "expected acceptance, got rejection"
    fi
}

reject() {
    local desc=$1
    shift
    if "$@" > /dev/null 2>&1; then
        not_ok "${desc}" "expected rejection, got acceptance"
    else
        ok "${desc}"
    fi
}

echo '# LUKS password'
accept 'accepts a 12 character password' luks_password_rejection 'correct horse'
accept 'accepts a long password with symbols' luks_password_rejection 'a-V3ry/l0ng password!'
reject 'rejects an empty password' luks_password_rejection ''
reject 'rejects an 11 character password' luks_password_rejection 'abcdefghijk'
reject 'rejects the default login password' luks_password_rejection 'secureblue'
reject 'rejects control characters' luks_password_rejection $'abcdefghij\tkl'

echo '# disk path syntax'
for bad in '' ' ' '/dev/does-not-exist' '/dev/null' '/dev/sda;reboot' \
    '/dev/sda$(reboot)' '/dev/sda 1' 'dev/sda' '../../dev/sda' '"/dev/sda"'; do
    reject "rejects '${bad}'" resolve_disk "${bad}"
done

echo '# username'
# A pristine target /etc.
tmpdir=$(mktemp -d)
trap 'rm -rf "${tmpdir}"' EXIT
mkdir -p "${tmpdir}/etc"
printf 'root:x:0:0:root:/root:/bin/bash\n' > "${tmpdir}/etc/passwd"
printf 'root:x:0:\nwheel:x:10:\n' > "${tmpdir}/etc/group"
printf 'root:*:19000:0:99999:7:::\n' > "${tmpdir}/etc/shadow"
# shellcheck disable=SC2034 # used by the sourced validators
etc_dir="${tmpdir}/etc"

for good in alice a user-1 user_1 _svc; do
    accept "accepts '${good}'" username_rejection "${good}"
done
accept 'accepts a 32 character name' username_rejection "$(printf 'a%.0s' {1..32})"
reject 'rejects a 33 character name' username_rejection "$(printf 'a%.0s' {1..33})"

# Everything that used to end up verbatim in passwd, shadow, group, a sed
# replacement or a path.
while IFS= read -r bad; do
    reject "rejects $(printf '%q' "${bad}")" username_rejection "${bad}"
done << 'EOF'

 
Alice
1alice
-flag
al ice
alice:bob
alice:x:0:0::/root:/bin/bash
alice,root
alice/../../etc
../etc
..
/
root
admin
daemon
nobody
sshd
systemd-network
alice&
alice\1
alice;id
alice$(id)
alice`id`
alice*
alice~
alice.
alice@example.com
alice+bob
EOF

echo '# username collisions'
accept 'accepts a name that is not in use' username_rejection alice
printf 'bob:x:1000:1000:bob:/var/home/bob:/bin/bash\n' >> "${tmpdir}/etc/passwd"
reject 'rejects a name already in passwd' username_rejection bob
printf 'carol:x:1000:\n' >> "${tmpdir}/etc/group"
reject 'rejects a name already in group' username_rejection carol
reject 'rejects any name when UID 1000 is taken' username_rejection dave
printf 'root:x:0:0:root:/root:/bin/bash\n' > "${tmpdir}/etc/passwd"
printf 'root:x:0:\nwheel:x:10:\n' > "${tmpdir}/etc/group"
printf 'dave:!:19000:0:99999:7:::\n' >> "${tmpdir}/etc/shadow"
reject 'rejects a name already in shadow' username_rejection dave

echo '# in-use detection (the check that protects the running system)'
root_src=$(findmnt -no SOURCE / 2>/dev/null || true)
root_src=${root_src%%\[*}
root_disk=''
if [[ -n ${root_src} && -b ${root_src} ]]; then
    root_disk=$(parent_disk_of "${root_src}" 2>/dev/null) || root_disk=''
fi
if [[ -n ${root_disk} ]]; then
    accept "detects /dev/${root_disk} (backs /) as in use" disk_is_in_use "/dev/${root_disk}"
    reject 'does not report /dev/null as in use' disk_is_in_use /dev/null
else
    echo 'skip - / is not on a plain block device here'
fi

echo
printf '# %d passed, %d failed\n' "${pass}" "${fail}"
[[ ${fail} -eq 0 ]]
