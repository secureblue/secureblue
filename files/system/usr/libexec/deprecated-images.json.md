# Deprecated Images

The following image types have been deprecated:

## wayblue-hyprland

Rationale: Our Hyprland images have low usage. More importantly though, Hyprland has a long history of antagonism towards security improvements. Please see https://bugs.gentoo.org/930831#c6 for more info.
Rebase to: One of secureblue's `sericea` images.

## wayblue-sway

Rationale: Deduplication and supply chain improvements. We already have `sericea` images that pull directly from Fedora, without depending on ublue's akmods. Wayblue on the other hand still depends on ublue's akmods.
Rebase to: One of secureblue's `sericea` images.

## wayblue-wayfire

Rationale: Lack of usage and consolidation. Stats report no usage.
Rebase to: One of secureblue's `sericea` images.

## wayblue-river

Rationale: Low usage and consolidation. Stats report very low usage.
Rebase to: One of secureblue's `sericea` images.

## userns

Rationale: See https://github.com/secureblue/secureblue/releases/tag/v4.3.0

Rebase to: The equivalent image removing `-userns`. For example, for `kinoite-nvidia-userns-hardened`, rebase to `kinoite-nvidia-hardened`. Then, if needed, run `ujust toggle-unconfined-domain-userns-creation` to re-enable unconfined user namespaces for unconfined processes and/or `ujust toggle-container-domain-userns-creation` for container domain processes. You can also rerun the install script if you prefer.

## bluefin/aurora

Rationale: See https://github.com/secureblue/secureblue/releases/tag/v3.2.2

Rebase to: The equivalent image replacing `bluefin` with `silverblue` or `aurora` with `kinoite`. For example, for `aurora-nvidia-hardened`, rebase to `kinoite-nvidia-hardened`.

## server

Rationale: Upstream decisions have required us to fork. This brings with it the following critical migration steps *before* rebasing:

- Password-based auth is no longer supported, ensure you are able to log-in using pubkey or another supported method. If you do not do this, you risk being locked out of your host.
- Tailscale and cockpit are no longer included by default (but the tailscale repo is). If you need either, ensure you have layered them before rebooting into your new deployment.

Rebase to: The equivalent image replacing `server` with `securecore`. For example, for `server-nvidia-hardened`, rebase to `securecore-nvidia-hardened`.

## framework

Rationale: [Deprecated upstream](https://github.com/ublue-os/framework#this-image-is-deprecated)

Rebase to: The equivalent image replacing `-framework` with `-main`. For example, for `kinoite-framework-hardened`, rebase to `kinoite-main-hardened`.

## main-laptop

Rationale: Upstream recommendations have changed and improvements are being made to PPD.

Rebase to: The equivalent image without `-laptop`. For example, for `kinoite-main-laptop-hardened`, rebase to `kinoite-main-hardened`.

## nvidia-laptop

Rationale: Upstream recommendations have changed and improvements are being made to PPD. Additionally, nvidia optimus configuration has moved to upstream `just` commands.

Rebase to: The equivalent image without `-laptop`. For example, for `kinoite-nvidia-laptop-hardened`, rebase to `kinoite-nvidia-hardened` and reboot.
