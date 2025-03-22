set positional-arguments

# Audit secureblue
audit-secureblue *args:
    #!/bin/sh
    python3 /usr/libexec/secureblue/audit-secureblue.py "$@"
