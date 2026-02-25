#!/usr/bin/env bats

# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

setup() {
    TEMP_TEST_DIR=$(mktemp -d)
    PATH="${TEMP_TEST_DIR}:${PATH}"
    cp files/system/usr/libexec/deprecated-images.json "${TEMP_TEST_DIR}/deprecated-images.json"
    sed --sandbox \
        -e "s@/usr/libexec/deprecated-images\\.json@${TEMP_TEST_DIR}/deprecated-images.json@g" \
        files/system/usr/libexec/secureblue-motd > "${TEMP_TEST_DIR}/secureblue-motd"
    chmod +x "${TEMP_TEST_DIR}/secureblue-motd"
}

teardown() {
    PATH="${PATH#*:}"
    rm -rf "$TEMP_TEST_DIR"
}

mock_rpm_ostree_status() {
    cat <<EOF > "${TEMP_TEST_DIR}/rpm-ostree"
#!/bin/sh
cat <<'EOT'
{"deployments":[{"container-image-reference":"ostree-image-signed:docker://ghcr.io/secureblue/$1","timestamp":$2}]}
EOT
EOF
    chmod +x "${TEMP_TEST_DIR}/rpm-ostree"
}

mock_mokutil() {
    cat <<EOF > "${TEMP_TEST_DIR}/mokutil"
#!/bin/sh
cat <<'EOT'
$1
EOT
exit '$2'
EOF
    chmod +x "${TEMP_TEST_DIR}/mokutil"
}

@test "MOTD runs correctly with up-to-date image" {
    test_image_name='kinoite-main-hardened:latest'
    mock_rpm_ostree_status "$test_image_name" "$(date +%s)"
    mock_mokutil 'secureblue secureboot key' 0
    run secureblue-motd
    (( status == 0 ))
    [[ "$output" == *"Welcome to secureblue!"*"Your image is:"*"$test_image_name"* ]]
    [[ ! "$output" =~ 'deprecated image'|'not enrolled'|'unsupported'|'over 1 week old' ]]
}

@test "MOTD warns about deprecated image" {
    test_image_name='kinoite-main-userns-hardened:latest'
    mock_rpm_ostree_status "$test_image_name" "$(date +%s)"
    mock_mokutil 'secureblue secureboot key' 0
    run secureblue-motd
    (( status == 0 ))
    [[ "$output" == *"Welcome to secureblue!"*"Your image is:"*"$test_image_name"* ]]
    [[ $output == *"You are on a deprecated image"* ]]
}

@test "MOTD does not warn about Secure Boot if mokutil fails" {
    test_image_name='kinoite-main-hardened:latest'
    mock_rpm_ostree_status "$test_image_name" "$(date +%s)"
    mock_mokutil '' 1
    run secureblue-motd
    (( status == 0 ))
    [[ "$output" == *"Welcome to secureblue!"*"Your image is:"*"$test_image_name"* ]]
    [[ ! "$output" =~ 'deprecated image'|'not enrolled'|'unsupported'|'over 1 week old' ]]
}

@test "MOTD warns about missing Secure Boot key" {
    test_image_name='kinoite-main-hardened:latest'
    mock_rpm_ostree_status "$test_image_name" "$(date +%s)"
    mock_mokutil 'fedoraca' 0
    run secureblue-motd
    (( status == 0 ))
    [[ "$output" == *"Welcome to secureblue!"*"Your image is:"*"$test_image_name"* ]]
    [[ $output == *"Secure Boot key is not enrolled"* ]]
}

@test "MOTD warns about missing image tag" {
    test_image_name='kinoite-main-hardened'
    mock_rpm_ostree_status "$test_image_name" "$(date +%s)"
    mock_mokutil 'secureblue secureboot key' 0
    run secureblue-motd
    (( status == 0 ))
    [[ "$output" == *"Welcome to secureblue!"*"Your image is:"*"$test_image_name"* ]]
    [[ $output == *"You are missing an image tag, which is unsupported by secureblue."* ]]
}

@test "MOTD warns about non-latest image tag" {
    test_image_name='kinoite-main-hardened:some-other-tag'
    mock_rpm_ostree_status "$test_image_name" "$(date +%s)"
    mock_mokutil 'secureblue secureboot key' 0
    run secureblue-motd
    (( status == 0 ))
    [[ "$output" == *"Welcome to secureblue!"*"Your image is:"*"$test_image_name"* ]]
    [[ $output == *"You are on a specific tag, which is unsupported by secureblue."* ]]
}

@test "MOTD warns about outdated image" {
    test_image_name='kinoite-main-hardened:latest'
    mock_rpm_ostree_status "$test_image_name" "$(date -d '2 weeks ago' +%s)"
    mock_mokutil 'secureblue secureboot key' 0
    run secureblue-motd
    (( status == 0 ))
    [[ "$output" == *"Welcome to secureblue!"*"Your image is:"*"$test_image_name"* ]]
    [[ $output == *"Your current image is over 1 week old"*"ujust update-system"* ]]
}
