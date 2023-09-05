# `systemd` Module for Startingpoint

The `systemd` module streamlines the management of systemd units during image building. Units are divided into `system` and `user` categories, with `system` units managed directly using `systemctl` and `user` units using `systemctl --user`. You can specify which units to enable or disable under each category.

## Example Configuration:

```yaml
type: systemd
system:
  enable:
    - example.service
  disable:
    - example.target
user:
  enable:
    - example.timer
  disable:
    - example.service
```

In this example:

### System Units
- `example.service`: Enabled (runs on system boot)
- `example.target`: Disabled (does not run on system boot)

### User Units
- `example.timer`: Enabled (runs for the user)
- `example.service`: Disabled (does not run for the user)

This configuration achieves the same results as the following commands:

```sh
# System Units
systemctl enable example.service
systemctl disable example.target

# User Units
systemctl --user enable example.timer
systemctl --user disable example.service
```
