set positional-arguments := true

# Audit secureblue
audit-secureblue *args:
    #!/bin/sh
    python3 /usr/libexec/secureblue/audit_secureblue.py "$@"
