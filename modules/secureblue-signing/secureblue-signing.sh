#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -euo pipefail

CONTAINER_DIR="/usr/etc/containers"
MODULE_DIRECTORY="${MODULE_DIRECTORY:-"/tmp/modules"}"
IMAGE_NAME_FILE="${IMAGE_NAME//\//_}"
IMAGE_REGISTRY_TITLE=$(echo "$IMAGE_REGISTRY" | cut -d'/' -f2-)

echo "Setting up container signing in policy.json and cosign.yaml for $IMAGE_NAME"
echo "Registry to write: $IMAGE_REGISTRY"

if ! [ -d "$CONTAINER_DIR" ]; then
    mkdir -p "$CONTAINER_DIR"
fi

if ! [ -d $CONTAINER_DIR/registries.d ]; then
   mkdir -p "$CONTAINER_DIR/registries.d"
fi

if ! [ -d "/usr/etc/pki/containers" ]; then
    mkdir -p "/usr/etc/pki/containers"
fi

if ! [ -f "$CONTAINER_DIR/policy.json" ]; then
    cp "$MODULE_DIRECTORY/signing/policy.json" "$CONTAINER_DIR/policy.json"
fi

mv "/usr/etc/pki/containers/$IMAGE_NAME.pub" "/usr/etc/pki/containers/$IMAGE_REGISTRY_TITLE.pub"

POLICY_FILE="$CONTAINER_DIR/policy.json"

yq -i -o=j '.transports.docker |=
    {"'"$IMAGE_REGISTRY"'": [
            {
                "type": "sigstoreSigned",
                "keyPath": "/usr/etc/pki/containers/'"$IMAGE_REGISTRY_TITLE"'.pub",
                "signedIdentity": {
                    "type": "matchRepository"
                }
            }
        ]
    }
+ .' "$POLICY_FILE"

mv "$MODULE_DIRECTORY/signing/registry-config.yaml" "$CONTAINER_DIR/registries.d/$IMAGE_REGISTRY_TITLE.yaml"
sed -i "s ghcr.io/IMAGENAME $IMAGE_REGISTRY g" "$CONTAINER_DIR/registries.d/$IMAGE_REGISTRY_TITLE.yaml"
