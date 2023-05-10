# Custom scripts

You can add custom scripts to this directory and declare them to be run at build time in the `scripts:` section of `recipe.yml`. Custom scripts can be run at either the `pre:` execution phase right after the custom repositories are added, or at the `post:` phase after all of the automatic build steps.

Your scripts will be given exactly one argument when they are executed, which specifies its precise execution phase (`pre` or `post`). The primary purpose of this argument is to streamline the reuse of scripts for multiple stages.

## `autorun.sh`

`autorun.sh` is enabled by default and automatically runs all scripts in the folders `scripts/pre/` and `scripts/post/` at the correct execution phases.
