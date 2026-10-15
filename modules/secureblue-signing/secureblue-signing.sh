#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025 Blue-Build
# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

CONTAINER_DIR=/usr/share/containers
MODULE_DIRECTORY="${MODULE_DIRECTORY:-/tmp/modules}"
IMAGE_REGISTRY_TITLE="${IMAGE_REGISTRY#*/}"
IMAGE_REGISTRY_TITLE="${IMAGE_REGISTRY_TITLE//"/"/-}"

echo "Setting up container signing in policy.json and cosign.yaml for ${IMAGE_NAME}"
echo "Registry to write: ${IMAGE_REGISTRY}"

mkdir -p "${CONTAINER_DIR}/registries.d"

# shellcheck disable=SC2016
envsubst '${IMAGE_REGISTRY}' \
    <"${MODULE_DIRECTORY}/secureblue-signing/registry-config.yaml" \
    >"${CONTAINER_DIR}/registries.d/${IMAGE_REGISTRY_TITLE}.yaml"

jq --arg image_registry "${IMAGE_REGISTRY}" \
    --arg image_registry_title "${IMAGE_REGISTRY_TITLE}" \
    '.transports.docker |=
    { $image_registry: [
        {
            "type": "sigstoreSigned",
            "keyPaths": [
              ("/usr/share/pki/containers/" + $image_registry_title + ".pub"),
              ("/usr/share/pki/containers/" + $image_registry_title + "-2025.pub")
            ],
            "signedIdentity": {
                "type": "matchRepository"
            }
        }
    ] } + .' "${MODULE_DIRECTORY}/secureblue-signing/policy.json" \
    >"${CONTAINER_DIR}/policy.json"
