# FAQ

#### Why is flatpak included? Should I use flatpak?

https://github.com/secureblue/secureblue/issues/125#issuecomment-1859610560

#### Should I use electron apps? Why don't they work well with hardened_malloc?

https://github.com/secureblue/secureblue/issues/193#issuecomment-1953323680

#### My fans are really loud, is this normal?

During rpm-ostree operations, it's normal. Outside of that:

- Make sure you followed the nvidia steps in the readme if you're using nvidia.
- Make sure you're using an `asus` image if you're using asus.

#### Should I use firejail?

[No](https://madaidans-insecurities.github.io/linux.html#firejail), use ``bubblejail`` if there's no flatpak available for an app. 

#### An app I use won't start due to a malloc issue. How do I fix it?

Override `LD_PRELOAD` for that app. For flatpaks, this is as simple as removing the environment variable via Flatseal.

#### On secureblue half of my CPU cores are gone. Why is this?

`mitigations=auto,nosmt` is set on secureblue. This means that if your CPU is vulnerable to attacks that utilize [Simultaneous Multithreading](https://en.wikipedia.org/wiki/Simultaneous_multithreading), SMT will be disabled.

#### Should I use a userns image or not? What's the difference?

[USERNS](USERNS.md)

#### How do I install `x`?

1. Check if it's already installed using `rpm -qa | grep x`
2. Check if there's a flatpak available at https://flathub.org
3. Consider using distrobox or brew to install it
4. Layer it using `rpm-ostree install`, as a last option

#### Another security project has a feature that's missing in secureblue, can you add it?

First check if the README already has an equivalent or better feature. If it doesn't, open a new github issue.

#### How do I install steam?

To use steam you can either:

- Install the [flatpak](https://flathub.org/apps/com.valvesoftware.Steam)
- Layer the rpm with `rpm-ostree install steam`

#### Why are bluetooth kernel modules disabled? How do I enable them?

Bluetooth has a long and consistent history of security issues. However, if you still need it, run `ujust toggle-bluetooth-modules`

#### Why are upgrades so large?

This is an issue with rpm-ostree image-based systems generally, and not specific to secureblue. Ideally upgrades would come in the form of a zstd-compressed container diff, but it's not there yet. Check out [this upstream issue](https://github.com/coreos/rpm-ostree/issues/4012) for more information.

#### Why can't I install new KDE themes?

The functionality that provides this, called GHNS, is disabled by default due to the risk posed by the installation of potentially damaging or malicious scripts. This has caused [real damage](https://blog.davidedmundson.co.uk/blog/kde-store-content/). 

If you still want to enable this functionality, run `ujust toggle-ghns`

#### Why doesn't my Xwayland app work?

Xwayland is disabled by default on GNOME, KDE Plasma, and Sway. Use `ujust toggle-xwayland` if you need it

#### Why I can't install nor use any GNOME user extensions?

This is because support for installing & using them has been intentionally disabled by default in secureblue.
Only GNOME system extensions are trusted, if they are installed.

To enable support for installing GNOME user extensions, you can run ujust command:
`ujust toggle-gnome-extensions`

#### My clock is wrong and it's not getting automatically set. How do I fix this?

If your system time is off by an excessive amount due to rare conditions like a CMOS reset, your network will not connect. A one-time manual reset will fix this. This should never be required except under very rare circumstances.

For more technical detail, see [#268](https://github.com/secureblue/secureblue/issues/268)

#### Why is DNS broken on my secureblue VM?

The DNSSEC setting we set in `/etc/systemd/resolved.conf.d/securedns.conf` causes known issues with network connectivity when secureblue is used in a VM. To fix it, comment out `DNSSEC=allow-downgrade` in that file and manually set a dns provider in network settings.

#### Why does chromium take a long time to open?

This is a [known issue](https://forums.developer.nvidia.com/t/550-54-14-cannot-create-sg-table-for-nvkmskapimemory-spammed-when-launching-chrome-on-wayland/284775) with the proprietary nvidia drivers. Your options are:

- (Recommended if available for your hardware) switch to a `-main` image and use Nouveau with NVK and [GSP](https://nouveau.freedesktop.org/PowerManagement.html)
- Enable xwayland with `ujust toggle-xwayland` and then set ozone-platform to x11 in `chrome://flags`

#### How do I get notified of secureblue changes?

On the secureblue github page, click "Watch", and then "Custom", and select Releases like so:

![image](https://github.com/user-attachments/assets/38146394-f730-4b84-8bfa-4fbbf29350ff)

#### Why don't my AppImages work?

AppImages depend on fuse2, which is unmaintained and depends on a suid root binary. For this reason, fuse2 support is removed by default. It's strongly recommended that you find alternative mechanisms to install your applications (flatpak, distrobox, etc). If you can't find an alternative and still need fuse2, you can add it back by layering something that depends on it. 

For example: `rpm-ostree install zfs-fuse`

#### Why don't KDE Vaults work?

Similar to the AppImage FAQ, the KDE Vault default backend `cryfs` depends on fuse2. For this reason it's recommended that you migrate to an alternative that doesn't depend on fuse2, for example `fscrypt`. If you don't want to do so, you can add fuse2 back by layering something that depends on it, as described in the AppImage FAQ.
