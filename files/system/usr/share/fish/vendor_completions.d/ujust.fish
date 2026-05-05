# SPDX-FileCopyrightText: Copyright 2026 The Secureblue Authors
#
# SPDX-License-Identifier: Apache-2.0

# Completions for ujust recipes
complete -c ujust -f -a '(ujust --summary | string split " ")'

# Completions for options
complete -c ujust -l choose -d 'Interactively select recipe to run'
complete -c ujust -l dump -d 'Print justfile'
complete -c ujust -l list -s l -d 'List available recipes'
complete -c ujust -l show -s s -d 'Show recipe'
complete -c ujust -l summary -d 'List names of available recipes'
complete -c ujust -l usage -d 'Print recipe usage information'

# `ujust with-standard-malloc` wraps an arbitrary command, so generate
# completions for that command.
complete -c ujust -n '__fish_seen_subcommand_from with-standard-malloc' -xa '(__fish_complete_subcommand --fcs-skip=2)'
