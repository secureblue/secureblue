# secureblue

The recommended method to install secureblue is to rebase from an upstream silverblue/kinoite installation. Before rebasing and during the installation, the following checks are recommended.

## Preinstall guide

> [!TIP]
> If you don't yet have a Fedora Atomic installation medium, you should obtain an image from the official Fedora Project website, [here](https://fedoraproject.org/atomic-desktops/). Once you have downloaded an image, it is *highly reccomended* that you [verify](https://fedoraproject.org/security) it for security and integrity.

### Fedora Installation
- Select the option to encrypt the drive you're installing to.
- Use a [strong password](https://security.harvard.edu/use-strong-passwords) when prompted.
- Leave the root account disabled.

### BIOS Hardening
- Ensure secureboot is enabled.
- Ensure your BIOS is up to date by checking its manufacturer's website.
- Disable booting from USB (some manufacturers allow firmware changes from live systems).
- Set a BIOS password to prevent tampering.
