#!/usr/bin/env -S awk -f

# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

BEGIN {
    print "Checking shebang lines of shell scripts..."
    failure = 0
}

FNR == 1 && (FILENAME ~ /\.sh$/ || /^#![[:blank:]]*(\/usr)?\/bin\/(env[[:blank:]]+)?(ba)?sh[[:blank:]]*$/) {
    if ($0 !~ /^#!/) {
        print FILENAME " is missing a shebang line."
        failure = 1
    } else if (FILENAME ~ /^files\/system\// && $0 !~ /^#!(\/usr)?\/bin\/(ba)?sh$/) {
        print FILENAME " has non-normalized shebang line: \"" $0 "\" (should be absolute)"
        failure = 1
    } else if (FILENAME !~ /^files\/system\// && $0 != "#!/usr/bin/env bash") {
        print FILENAME " has non-normalized shebang line: \"" $0 "\" (should be \"#!/usr/bin/env bash\")"
        failure = 1
    }
}

END {
    if (failure)
        exit 1
    else
        print "No issues found."
}
