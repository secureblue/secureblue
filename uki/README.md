## Testing secureblue UKIs

### 1. System requirements

- 32+ GiB disk space
- 16+ GiB memory
  - This requirement will be reduced when ISOs are available. For now, lots of
    memory is needed to hold secureblue in RAM before installing it to disk.
- UEFI-based firmware
- For measured boot: a TPM 2.0

### 2. Preparing secure boot

secureblue offers two options for Secure Boot. You should choose one:

1. **shim** - Safe for all devices. However, your firmware must trust the
   Microsoft Third Party CA, which signs many bootloaders and ROMs. This greatly
   increases attack surface but is compatible with all hardware.
2. **secureblue Platform Key** - Only suitable for some devices. Your firmware
   will only trust secureblue. This offers improved security, but this can BRICK
   YOUR DEVICE by breaking the display if your external GPU requires an option
   ROM to work.

In general, the Platform Key option is suitable for laptops, but not for
desktops. However, modifying settings is entirely at your own risk, and you
should use shim if you are in doubt.

In future, the installer may gain the ability to determine whether installing a
Platform Key is safe.

- **To use shim** - proceed to step 3.
- **To use the secureblue Platform Key** - you must enter your UEFI firmware
  settings to put the device in Setup Mode. See step 2a.

#### 2a. Entering Setup Mode (for Platform Key users only)

##### On bare metal

To enter Setup Mode, instructions vary depending on the model of your device.
The setting may be called "Delete Platform Key", "Clear Secure Boot Keys", or
"Enter Setup Mode".

This is *not* the same thing as "Reset Secure Boot Keys", which restores factory
defaults.

##### On a VM with virt-manager

- Boot Options > Enable boot menu
- Start the VM, press Esc during boot menu
- Go to EFI Firmware Setup
- Go to Device Manager > Secure Boot Configuration
- Set Secure Boot Mode to Custom Mode
- Custom Secure Boot Options > PK Options > Delete PK
- Exit setup and reboot into CoreOS

### 3. Booting into CoreOS

- Download the [CoreOS ISO](https://fedoraproject.org/coreos/download/?stream=stable#baremetal),
  verify its checksum and flash it to a USB drive using Fedora Media Writer.
- Insert the media into the device (or, for VMs, attach the ISO) and power on.
- Use the boot menu to enter the CoreOS live environment.

### 4. Install secureblue

- If using a non-US keyboard: set your keyboard layout with
  `sudo loadkeys <layout>`.
  - Examples include `gb`, `de`, `fr`, `es`, `ru`, `it`, `br-abnt2`, `jp106`.
  - A full list can be seen with `localectl list-keymaps`.
- Connect to the Internet. For wired connections, this should happen
  automatically.
  - To connect via WiFi:
    `nmcli device wifi connect "YOUR_SSID" password "YOUR_PASSWORD"`
  - To verify: `nm-online`
- Download the secureblue repository.
  `git clone https://github.com/secureblue/secureblue.git --branch testing`
- Optional: verify the checksums of `secureblue/cosign.pub`,
  `secureblue/uki/install.sh` and `secureblue/uki/keys/db/db.der` with
  `sha256sum`.
- Start the installation: `sudo secureblue/uki/install.sh`
- Report any bugs to [secureblue's GitHub Issues page](https://github.com/secureblue/secureblue/issues).

## Making your own UKI build (advanced)

1. In the repository root, run `uki/create-uki-keys.sh`. Back up the `uki/keys/`
   directory that was generated, and upload the contents of `uki/keys/db/db.key`
   as the `UKI_DB_KEY` secret to GitHub.
2. Manually trigger the `Sign UKI addons` and `Sign systemd-boot` workflows on
   GitHub.
3. Trigger a secureblue build as usual. The UKI will be built after the normal
   images are done, using the `build-sealed-image` workflow.
