## Build instructions

1. In the repository root, run `uki/create-uki-keys.sh`. Back up the `uki/keys/` that were generated, and upload the contents of `uki/keys/db/db.key` as the `UKI_DB_KEY` secret to GitHub.
2. Manually trigger the `Sign UKI addons` and `Sign systemd-boot` workflows on GitHub.
3. Trigger a secureblue build as usual. The UKI will be built after the normal `silverblue-main-hardened` image is done.

## Test instructions

### Preparing the VM

1. Create a VM in virt-manager with:
    - A 32+ GiB VirtIO disk
    - 16 GiB memory (this is to act as a tmpfs while pulling the container).
    - Use UEFI-based firmware with Secure Boot enabled (`OVMF_CODE_4M.secboot.qcow2`).
    - An emulated TPM (CRB).
2. Download the [CoreOS ISO](https://builds.coreos.fedoraproject.org/prod/streams/stable/builds/44.20260523.3.1/x86_64/fedora-coreos-44.20260523.3.1-live-iso.x86_64.iso) and attach to the VM.
3. If you want to use Platform Key-based secure boot, enter Setup Mode by removing the Platform Key:
    - In virt-manager: Boot Options > Enable boot menu
    - Start the VM, press Esc during boot menu
    - Go to EFI Firmware Setup
    - Go to Device Manager > Secure Boot Configuration
    - Set Secure Boot Mode to Custom Mode
    - Custom Secure Boot Options > PK Options > Delete PK
    - Exit setup and reboot into CoreOS

Installation also works on bare metal.

### Installing secureblue UKI (testing)

Once CoreOS has booted:

- Set your keyboard layout (e.g. `sudo loadkeys uk`)
- If you're installing on bare metal with WiFi, connect to the Internet.
- Now download, verify and run the installer:

```
$ git clone https://github.com/secureblue/secureblue.git
$ sha256sum secureblue/uki/install.sh
974d39f8147567b51638c46641da243efc3b61a5a1a90e84e23efe432e17e6ff  secureblue/uki/install.sh
$ sha256sum secureblue/cosign.pub
9cbd48de48d467f86e0f31f9454c6e0bb663f3d033ecd92143f62577eb1cb5eb  secureblue/cosign.pub
$ sudo secureblue/uki/install.sh
```
