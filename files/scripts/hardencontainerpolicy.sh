#!/usr/bin/env bash

# Tell build process to exit if there are any errors.
set -oue pipefail

sed -i 's/insecureAcceptAnything/reject/' /usr/etc/containers/policy.json


# Exception for build-container-installer to allow the ISO generation script to work
# https://github.com/JasonN3/build-container-installer/issues/123
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