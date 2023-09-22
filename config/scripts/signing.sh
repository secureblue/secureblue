#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

echo "Setting up container signing in policy.json and cosign.yaml for $IMAGE_NAME"
echo "Registry to write: $IMAGE_REGISTRY"

cp /usr/share/ublue-os/cosign.pub /usr/etc/pki/containers/"$IMAGE_NAME".pub

FILE=/usr/etc/containers/policy.json

yq -i -o=j '.transports.docker |=
    {"'"$IMAGE_REGISTRY"'": [
            {
                "type": "sigstoreSigned",
                "keyPath": "/usr/etc/pki/containers/'"$IMAGE_NAME"'.pub",
                "signedIdentity": {
                    "type": "matchRepository"
                }
            }
        ]
    }
+ .' "$FILE"

IMAGE_REF="ostree-image-signed:docker://$IMAGE_REGISTRY/$IMAGE_NAME"
printf '{\n"image-ref": "'"$IMAGE_REF"'",\n"image-default-tag": "latest"\n}' > /usr/share/ublue-os/image-info.json

cp /usr/etc/containers/registries.d/ublue-os.yaml /usr/etc/containers/registries.d/"$IMAGE_NAME".yaml
sed -i "s ghcr.io/ublue-os $IMAGE_REGISTRY g" /usr/etc/containers/registries.d/"$IMAGE_NAME".yaml
