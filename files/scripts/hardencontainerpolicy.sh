#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

POLICY_FILE="/usr/etc/containers/policy.json"

if [[ ! -f "$POLICY_FILE" ]]; then
    echo "Error: $POLICY_FILE does not exist."
    exit 1
fi

sed -i 's/insecureAcceptAnything/reject/' "$POLICY_FILE"


yq -i -o=j '.transports.docker |=
    {"ghcr.io/jasonn3": [
        {
          "type": "sigstoreSigned",
          "keyPath": "/usr/etc/pki/containers/build-container-installer.pub",
          "signedIdentity": {
            "type": "matchRepository"
          }
        }
      ]
    }
+ .' "$POLICY_FILE"

yq -i -o=j '.transports.docker |=
    {"ghcr.io/zelikos": [
        {
          "type": "sigstoreSigned",
          "keyPath": "/usr/etc/pki/containers/davincibox.pub",
          "signedIdentity": {
            "type": "matchRepository"
          }
        }
      ]
    }
+ .' "$POLICY_FILE"