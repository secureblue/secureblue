#!/usr/bin/env bats

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

setup() {
    TEST_DIR=$(mktemp -d)
    PATH="${TEST_DIR}:${PATH}"
    echo 'libhardened_malloc.so' > "${TEST_DIR}/ld.so.preload"
    # runcon only works on systems running SELinux
    cat <<'EOF' > "${TEST_DIR}/runcon"
#!/bin/bash
while [ "$1" != '--' ]; do shift; done
shift
exec -- "$@"
EOF
    sed --sandbox \
        -e "s@/etc/ld.so.preload\>@${TEST_DIR}/ld.so.preload@g" \
        -e "s@/usr/bin/runcon\>@${TEST_DIR}/runcon@g" \
        -e "s@/usr/bin/capsh\>@capsh@g" \
        files/system/usr/bin/with-standard-malloc \
        > "${TEST_DIR}/with-standard-malloc"
    chmod +x "${TEST_DIR}/with-standard-malloc" "${TEST_DIR}/runcon"
}

teardown() {
    PATH="${PATH#*:}"
    rm -rf "${TEST_DIR}"
}

@test "Should display usage info with no arguments" {
    run with-standard-malloc
    (( status == 0 ))
    [[ "${output}" == 'Usage: with-standard-malloc'* ]]
}

@test "Should display usage info with --help" {
    run with-standard-malloc --help
    (( status == 0 ))
    [[ "${output}" == 'Usage: with-standard-malloc'* ]]
}

@test "Should skip -- argument" {
    run with-standard-malloc -- echo 'Success!'
    (( status == 0 ))
    [[ "${output}" == 'Success!' ]]
}

@test "Should propagate exit code of wrapped command" {
    run with-standard-malloc sh -c 'exit 42'
    (( status == 42 ))
    [[ -z "${output}" ]]
}

@test "Should pass argument starting with dash" {
    cat <<'EOF' > "${TEST_DIR}/-e"
#!/bin/sh
printf '%s\n' "$*"
EOF
    chmod +x "${TEST_DIR}/-e"
    run with-standard-malloc -- -e one two three
    (( status == 0 ))
    [[ "${output}" == "one two three" ]]
}

@test "Should work if ld.so.preload doesn't exist" {
    rm "${TEST_DIR}/ld.so.preload"
    run with-standard-malloc echo 'Success!'
    (( status == 0 ))
    [[ "${output}" == 'Success!' ]]
}

@test "Should hide contents of ld.so.preload" {
    run with-standard-malloc cat "${TEST_DIR}/ld.so.preload"
    (( status == 0 ))
    [[ -z "${output}" ]]
}

@test "Should be able to read standard input" {
    run bats_pipe echo 'input string' \| with-standard-malloc sed 's/input/output/'
    (( status == 0 ))
    [[ "${output}" == 'output string' ]]
}

@test "Should preserve UID" {
    run with-standard-malloc id -ru
    (( status == 0 ))
    [[ "${output}" == "$(id -ru)" ]]
}

@test "Should preserve GID" {
    run with-standard-malloc id -rg
    (( status == 0 ))
    [[ "${output}" == "$(id -rg)" ]]
}

@test "Should map subuids" {
    subuid_start=$(awk -F: -v user="${USER}" '$1 == user { print $2; exit }' /etc/subuid)
    [[ -n "${subuid_start}" ]] || return 0 # skip if user has no subuids
    subuid_len=$(awk -F: -v user="${USER}" '$1 == user { print $3; exit }' /etc/subuid)
    run with-standard-malloc cat /proc/self/uid_map
    (( status == 0 ))
    grep -Eq "^[[:blank:]]*${subuid_start}[[:blank:]]+${subuid_start}[[:blank:]]+${subuid_len}$" <<<"${output}"
}

@test "Should map subgids" {
    subgid_start=$(awk -F: -v user="${USER}" '$1 == user { print $2; exit }' /etc/subgid)
    [[ -n "${subgid_start}" ]] || return 0 # skip if user has no subgids
    subgid_len=$(awk -F: -v user="${USER}" '$1 == user { print $3; exit }' /etc/subgid)
    run with-standard-malloc cat /proc/self/gid_map
    (( status == 0 ))
    grep -Eq "^[[:blank:]]*${subgid_start}[[:blank:]]+${subgid_start}[[:blank:]]+${subgid_len}$" <<<"${output}"
}

@test "Should ignore BASH_ENV" {
    cat <<'EOF' > "${TEST_DIR}/evil.sh"
#!/bin/sh
echo evil
EOF
    chmod +x "${TEST_DIR}/evil.sh"
    run env BASH_ENV="${TEST_DIR}/evil.sh" with-standard-malloc printenv BASH_ENV
    (( status == 1 ))
    [[ -z "${output}" ]]
}

@test "Should drop capabilities and not set no_new_privs" {
    [[ "$(id -u)" != 0 ]] || return 0 # skip this test if root
    run with-standard-malloc capsh --print
    (( status == 0 ))
    [[ "${output}" == $'Current: =\n'* ]]
    [[ "${output}" == *$'\nAmbient set =\n'* ]]
    [[ "${output}" == *$'\nCurrent IAB: \n'* ]]
    [[ "${output}" == *'(no-new-privs=0)'* ]]
}

@test "Should be able to run itself" {
    run with-standard-malloc with-standard-malloc echo 'Success!'
    (( status == 0 ))
    [[ "${output}" == 'Success!' ]]
}
