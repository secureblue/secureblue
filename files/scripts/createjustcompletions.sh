#!/usr/bin/env bash

set -oue pipefail

just --completions bash | sed -E 's/([\(_" ])just/\1ujust/g' > /usr/share/bash-completion/completions/ujust
