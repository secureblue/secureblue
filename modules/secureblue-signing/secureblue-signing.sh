#!/usr/bin/env bash

# SPDX-FileCopyrightText: Copyright 2025 Blue-Build
# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

CONTAINER_DIR='/usr/etc/containers'
ETC_CONTAINER_DIR='/etc/containers'
MODULE_DIRECTORY="${MODULE_DIRECTORY:-/tmp/modules}"
IMAGE_REGISTRY_TITLE=$(echo "${IMAGE_REGISTRY}" | cut -d'/' -f2-)

echo "Setting up container signing in policy.json and cosign.yaml for ${IMAGE_NAME}"
echo "Registry to write: ${IMAGE_REGISTRY}"

mkdir -p "${CONTAINER_DIR}/registries.d" "${ETC_CONTAINER_DIR}/registries.d"

cp "${MODULE_DIRECTORY}/secureblue-signing/policy.json" "${CONTAINER_DIR}/policy.json"
cp "${MODULE_DIRECTORY}/secureblue-signing/policy.json" "${ETC_CONTAINER_DIR}/policy.json"

POLICY_FILE="${CONTAINER_DIR}/policy.json"

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
    ] } + .' "${POLICY_FILE}" > POLICY.tmp

# covering our bases here since /usr/etc is technically unsupported, reevaluate once bootc is the primary deployment tool
cp POLICY.tmp "${CONTAINER_DIR}/policy.json"
cp POLICY.tmp "${ETC_CONTAINER_DIR}/policy.json"
rm POLICY.tmp

sed -i --sandbox -e "s|ghcr.io/IMAGENAME|${IMAGE_REGISTRY}|g" "${MODULE_DIRECTORY}/secureblue-signing/registry-config.yaml"
cp "${MODULE_DIRECTORY}/secureblue-signing/registry-config.yaml" "${CONTAINER_DIR}/registries.d/${IMAGE_REGISTRY_TITLE}.yaml"
cp "${MODULE_DIRECTORY}/secureblue-signing/registry-config.yaml" "${ETC_CONTAINER_DIR}/registries.d/${IMAGE_REGISTRY_TITLE}.yaml"
rm "${MODULE_DIRECTORY}/secureblue-signing/registry-config.yaml"
