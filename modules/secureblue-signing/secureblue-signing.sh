#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -euo pipefail

CONTAINER_DIR="/usr/etc/containers"
ETC_CONTAINER_DIR="/etc/containers"
MODULE_DIRECTORY="${MODULE_DIRECTORY:-"/tmp/modules"}"
IMAGE_NAME_FILE="${IMAGE_NAME//\//_}"
IMAGE_REGISTRY_TITLE=$(echo "$IMAGE_REGISTRY" | cut -d'/' -f2-)

echo "Setting up container signing in policy.json and cosign.yaml for $IMAGE_NAME"
echo "Registry to write: $IMAGE_REGISTRY"

if ! [ -d "$CONTAINER_DIR" ]; then
    mkdir -p "$CONTAINER_DIR"
fi

if ! [ -d "$ETC_CONTAINER_DIR" ]; then
    mkdir -p "$ETC_CONTAINER_DIR"
fi

if ! [ -d $CONTAINER_DIR/registries.d ]; then
   mkdir -p "$CONTAINER_DIR/registries.d"
fi

if ! [ -d $ETC_CONTAINER_DIR/registries.d ]; then
   mkdir -p "$ETC_CONTAINER_DIR/registries.d"
fi

if ! [ -d "/usr/etc/pki/containers" ]; then
    mkdir -p "/usr/etc/pki/containers"
fi

if ! [ -d "/etc/pki/containers" ]; then
    mkdir -p "/etc/pki/containers"
fi

cp "$MODULE_DIRECTORY/secureblue-signing/policy.json" $CONTAINER_DIR/policy.json
cp "$MODULE_DIRECTORY/secureblue-signing/policy.json" $ETC_CONTAINER_DIR/policy.json

# covering our bases here since /usr/etc is technically unsupported, reevaluate once bootc is the primary deployment tool
cp "/etc/pki/containers/$IMAGE_NAME.pub" "/usr/etc/pki/containers/$IMAGE_REGISTRY_TITLE.pub"
cp "/etc/pki/containers/$IMAGE_NAME.pub" "/etc/pki/containers/$IMAGE_REGISTRY_TITLE.pub"
rm "/etc/pki/containers/$IMAGE_NAME.pub"

POLICY_FILE="$CONTAINER_DIR/policy.json"

jq --arg image_registry "${IMAGE_REGISTRY}" \
   --arg image_registry_title "${IMAGE_REGISTRY_TITLE}" \
   '.transports.docker |= 
    { $image_registry: [
        {
            "type": "sigstoreSigned",
            "keyPath": ("/usr/etc/pki/containers/" + $image_registry_title + ".pub"),
            "signedIdentity": {
                "type": "matchRepository"
            }
        }
    ] } + .' "${POLICY_FILE}" > POLICY.tmp

# covering our bases here since /usr/etc is technically unsupported, reevaluate once bootc is the primary deployment tool
cp POLICY.tmp /usr/etc/containers/policy.json
cp POLICY.tmp /etc/containers/policy.json
rm POLICY.tmp

sed -i "s ghcr.io/IMAGENAME $IMAGE_REGISTRY g" "$MODULE_DIRECTORY/secureblue-signing/registry-config.yaml"
cp "$MODULE_DIRECTORY/secureblue-signing/registry-config.yaml" "$CONTAINER_DIR/registries.d/$IMAGE_REGISTRY_TITLE.yaml"
cp "$MODULE_DIRECTORY/secureblue-signing/registry-config.yaml" "$ETC_CONTAINER_DIR/registries.d/$IMAGE_REGISTRY_TITLE.yaml"
rm "$MODULE_DIRECTORY/secureblue-signing/registry-config.yaml"
