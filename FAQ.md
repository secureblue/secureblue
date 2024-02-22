# FAQ

#### Why is flatpak included? Should I use flatpak?

https://github.com/secureblue/secureblue/issues/125#issuecomment-1859610560

#### Should I use electron apps? Why don't they work well with hardened_malloc?

https://github.com/secureblue/secureblue/issues/193#issuecomment-1953323680

#### My fans are really loud, is this normal?

During rpm-ostree operations, it's normal. Outside of that:

- Make sure you followed the nvidia steps in the readme if you're using nvidia.
- Make sure you're using a `laptop` image if you're using a laptop.
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
3. Consider using distrobox or nix to install it
4. Layer it using `rpm-ostree install`, as a last option

#### Another security project has a feature that's missing in secureblue, can you add it?

First check if the README already has an equivalent or better feature. If it doesn't, open a new github issue.

#### I need Javascript JIT in chromium, how do I enable it?

Remove `CHROMIUM_FLAGS+=" --js-flags='--jitless --no-expose-wasm'"` from `/etc/chromium/chromium.conf` and remove `"DefaultJavaScriptJitSetting": 2,` from `/etc/chromium/policies/managed/hardening.json`
