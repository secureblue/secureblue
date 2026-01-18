# vim: set ft=make :
# SPDX-FileCopyrightText: Copyright 2025 Universal Blue
# SPDX-FileCopyrightText: Copyright 2025-2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

# Enable LUKS unlock via TPM
setup-luks-tpm-unlock:
    #!/usr/bin/bash
    run0 /usr/libexec/luks-enable-tpm2-autounlock.sh

# Disable LUKS unlock via TPM
remove-luks-tpm-unlock:
    #!/usr/bin/bash
    run0 /usr/libexec/luks-disable-tpm2-autounlock.sh

# Enabled LUKS unlock via a FIDO2 hardware key
setup-luks-fido2-unlock:
    #!/usr/bin/bash
    run0 /usr/libexec/luks-enable-fido2-unlock.sh

# Disable LUKS unlock via a FIDO2 hardware key
remove-luks-fido2-unlock:
    #!/usr/bin/bash
    run0 /usr/libexec/luks-disable-fido2-unlock.sh
