# vim: set ft=make :
# Copyright 2025 Universal Blue
# Copyright 2025 The Secureblue Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

# Enable automatic LUKS unlock via TPM
setup-luks-tpm-unlock:
    #!/usr/bin/bash
    run0 /usr/libexec/luks-enable-tpm2-autounlock.sh

# Disable automatic LUKS unlock via TPM
remove-luks-tpm-unlock:
    #!/usr/bin/bash
    run0 /usr/libexec/luks-disable-tpm2-autounlock.sh

# Enabled automatic LUKS unlock via a FIDO2 hardware key
setup-luks-fido2-unlock:
    #!/usr/bin/bash
    run0 /usr/libexec/luks-enable-fido2-unlock.sh

# Disable automatic LUKS unlock via a FIDO2 hardware key
remove-luks-fido2-unlock:
    #!/usr/bin/bash
    run0 /usr/libexec/luks-disable-fido2-unlock.sh
