# `files` Module for Startingpoint

The `files` module simplifies the process of copying files to the image during the build time. These files are sourced from the `config/files` directory, which is located at `/tmp/config/files` inside the image.

> **Warning**
> If you want to place anything in `/etc` of the final image, you MUST place them in `/usr/etc` in your repo, so that they're written to `/usr/etc` on the final system. That is the proper directory for "system" configuration templates on immutable Fedora distros, whereas the normal `/etc` is ONLY meant for manual overrides and editing by the machine's admin AFTER installation! See issue https://github.com/ublue-os/startingpoint/issues/28.

## Example Configuration:

```yaml
type: files
files:
  usr: /usr
```

In the example above, `usr` represents the directory located inside the `config/files` in the repository, while `/usr` designates the corresponding destination within the image.
