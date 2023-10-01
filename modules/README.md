# Making modules

If you want to extend Startingpoint with custom functionality that requires configuration, you should create a module. Modules are scripts in the subdirectories of this directory. The `type:` key in the recipe.yml should be used as both the name of the folder and script, with the script having an additional `.sh` suffix. Creating a custom module with the same name as a default module will override it.

Each module intended for public usage should include a `README.md` file inside it's directory with a short description of the module and documentation for each configuration option.

Modules get only the configuration options given to them in the recipe.yml, not the configuration of other modules or any top-level keys. The configuration is given as the first argument as a single-line json string. You can check out the default modules for examples on how to parse such string using `yq` or `jq`.  

Additionally, each module has access to four environment variables, `CONFIG_DIRECTORY` pointing to the Startingpoint directory in `/usr/share/ublue-os/`, `IMAGE_NAME` being the name of the image as declared in the recipe, `BASE_IMAGE` being the URL of the container image used as the base (FROM) in the image, and `OS_VERSION` being the `VERSION_ID` from `/usr/lib/os-release`.

When running modules, the working directory is the `CONFIG_DIRECTORY`.

A helper bash function called `get_yaml_array` is exported from the main build script.
```bash
# "$1" is the first cli argument, being the module configuration.
# If you need to read from some other JSON string, just replace "$1" with "$VARNAME".
get_yaml_array OUTPUT_VAR_NAME '.yq.key.to.array[]' "$1"
for THING in "${OUTPUT_VAR_NAME[@]}"; do
    echo "$THING"
done
```

All bash-based modules should start with the following lines to ensure the image builds fail on errors, and that the correct shell is used to run them.
```bash
#!/usr/bin/env bash
set -oue pipefail
```

## Style directions for official modules

These are general directions for writing official modules and their documentation to follow to keep a consistent style. Not all of these are to be mindlessly followed, especially the ones about grammar and writing style. It's good to keep these in mind if you intend to contribute back upstream, though, so that your module doesn't feel out of place.

### Bash

- Start with `#!/usr/bin/env bash` and `set -oue pipefail`
- Don't print "===", this is only for encapsulating the output of _different_ modules in `build.sh`
- Print something on each step and on errors for easier debugging
- Use CAPITALIZED names for variables that are read from the configuration

### README

- Title should be "`type` Module for Startingpoint", where the name/type of the module is a noun that shows the module's purpose
- There should be a subtitle "Example configuration", under which there should be a loosely documented yaml block showcasing each of the module's configuration options
    - For a YAML block, specify the language as "yaml", not "yml" (MkDocs only supports "yaml")
- At the start of each paragraph, refer to the module using its name or with "the module", not "it" or "the script"
- Use passive grammar when talking about the user, ie. "should be used", "can be configured", preferring references to what the module does, ie. "This module downloads the answer to the question of life, the universe and everything..."
