# Custom scripts

You can add custom scripts to this directory and declare them to be run at build time in the `scripts:` section of `recipe.yml`. Custom scripts can be run at either the `pre:` execution phase right after the custom repositories are added, or at the `post:` phase after all of the automatic build steps.

Your scripts will be given exactly one argument when they are executed, which specifies its precise execution phase (`pre` or `post`). The primary purpose of this argument is to streamline the reuse of scripts for multiple stages. This argument is provided for both manually declared scripts and scripts ran by `autorun.sh`.

## Creating a script

Look at `example.sh` for an example shell script. You can rename and copy the file for your own purposes. In order for the script to be executed, either move it to `scripts/pre/` or `scripts/post/` (if using `autorun.sh`) or declare it in the `recipe.yml`.

All commands from RPMs you've declared in the `recipe.yml` should be available when running scripts at the `post` execution phase.

When creating a script, please make sure

- ...its filename ends with `.sh`.
  - This follows convention for (especially bash) shell scripts.
  - `autorun.sh` only executes files that match `*.sh`.
- ...it starts with a [shebang](<https://en.wikipedia.org/wiki/Shebang_(Unix)>) like `#!/usr/bin/env bash`.
  - This ensures the script is ran with the correct interpreter / shell.
- ...it contains the command `set -oue pipefail` near the start.
  - This will make the image build fail if your script fails. If you do not care if your script works or not, you can omit this line.

## `autorun.sh`

`autorun.sh` is a script that automatically runs all scripts in the folders `scripts/pre/` and `scripts/post/` at the correct execution phases. It is enabled by default, but you can disable it by removing it from `recipe.yml`. Manually listed scripts can be combined with `autorun.sh`.

There are a few rules, which aim to simplify your script management:

- `autorun.sh` will only execute scripts at the FIRST level within the directory, which
  means that anything stored in e.g. `scripts/pre/deeperfolder/` will NOT execute.
  This is intentional, so that you can store libraries and helper scripts
  within subdirectories.
- You script directories and the scripts within them can be symlinks, to allow
  easy reuse of scripts. For example, if you want the same scripts to execute
  during both the `pre` and `post` stages, you could simply symlink individual
  scripts or the entire `pre` and `post` directories to each other. However,
  remember to only use RELATIVE symlinks, to ensure that the links work
  properly. For example, `ln -s ../pre/foo.sh scripts/post/foo.sh`.
- All scripts execute in a numerically and alphabetically sorted order, which
  allows you to easily control the execution order of your scripts. If it's
  important that they execute in a specific order, then you should give them
  appropriate names. For example, `05-foo.s` would always execute before
  another script named `99-bar.sh`. It's recommended to use zero-padded,
  numerical prefixes when you want to specify the execution order.
- The manually listed scripts in `recipe.yml` should
  be stored directly within `scripts/`, or in a custom subdirectory that
  doesn't match any of the execution phases. For example, you could
  set the `pre:` section of `recipe.yml` to execute both `autorun.sh`
  and `fizzwidget/something.sh`, and then place a bunch of auto-executed
  scripts under `scripts/pre/` for the autorunner. This makes it very simple
  to reuse common scripts between multiple different `recipe.yml` files,
  while also having some scripts be specific to different `recipe.yml`s.
- You can safely specify `autorun.sh` as a script in `recipe.yml`,
  even if the special directories don't exist or don't contain any
  scripts. It will gracefully skip the processing if there's nothing to do.
