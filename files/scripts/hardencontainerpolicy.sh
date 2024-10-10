#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

sed -i 's/insecureAcceptAnything/reject/' /etc/containers/policy.json


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
+ .' /usr/etc/containers/policy.json

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
+ .' /usr/etc/containers/policy.json