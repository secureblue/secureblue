# Deprecated Images

The following image types have been deprecated:

## framework

Rationale: [Deprecated upstream](https://github.com/ublue-os/framework#this-image-is-deprecated)

Rebase to: The equivalent image replacing `-framework` with `-main`. For example, for `kinoite-framework-hardened`, rebase to `kinoite-main-hardened`.

## main-laptop

Rationale: Upstream recommendations have changed and improvements are being made to PPD. 

Rebase to: The equivalent image without `-laptop`. For example, for `kinoite-main-laptop-hardened`, rebase to `kinoite-main-hardened`.

## nvidia-laptop

Rationale: Upstream recommendations have changed and improvements are being made to PPD. Additionally, nvidia optimus configuration has moved to upstream `just` commands.

Rebase to: The equivalent image without `-laptop`. For example, for `kinoite-nvidia-laptop-hardened`, rebase to `kinoite-nvidia-hardened` and reboot. Then, run `ujust configure-nvidia-optimus`.
