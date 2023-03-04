# Changelog

## [1.1.0](https://github.com/ublue-os/base/compare/v1.0.0...v1.1.0) (2023-03-03)


### Features

* add fedora 38 build ([#45](https://github.com/ublue-os/base/issues/45)) ([69fd4d7](https://github.com/ublue-os/base/commit/69fd4d7a57c5ce39331e47e8dedeb2a2f643190f))
* add how to review a PR ([#76](https://github.com/ublue-os/base/issues/76)) ([ae2e25b](https://github.com/ublue-os/base/commit/ae2e25b92f5ebebed2fcaad53ecfab651a639d12))
* ease customization by reading flatpaks and rpms to install from a recipe.yml. ([#79](https://github.com/ublue-os/base/issues/79)) ([a5e90a5](https://github.com/ublue-os/base/commit/a5e90a588f58a938405bf513d1032955be34028e))
* gha for building / publishing on pr ([#87](https://github.com/ublue-os/base/issues/87)) ([1726d18](https://github.com/ublue-os/base/commit/1726d182ee95ce5eb13f47212799a68b63c5aefc))
* Install VanillaOS' first-setup ([#55](https://github.com/ublue-os/base/issues/55)) ([43ddf0a](https://github.com/ublue-os/base/commit/43ddf0a123911f9dedc3a76dcfc314a7cb37e871))
* leave a warning for people to move to new repo ([#99](https://github.com/ublue-os/base/issues/99)) ([ffcb397](https://github.com/ublue-os/base/commit/ffcb3973bd540d679ab033ed94de6336b903e7dd))
* split flatpak update units into user and system ([#72](https://github.com/ublue-os/base/issues/72)) ([99c15be](https://github.com/ublue-os/base/commit/99c15be6f012cb590891c5ef16b2613dc538d144))
* swap out custom build for RPM of vanilla-first-setup ([#59](https://github.com/ublue-os/base/issues/59)) ([6927892](https://github.com/ublue-os/base/commit/6927892581dadf8f31419a0d9b070bb7268513ba))


### Bug Fixes

* add a warning that we change the flatpak configuration ([#80](https://github.com/ublue-os/base/issues/80)) ([9a349e2](https://github.com/ublue-os/base/commit/9a349e2625791b90c11f640938060344ec3e4bd5))
* Add vte dependency for first-setup ([#56](https://github.com/ublue-os/base/issues/56)) ([f8917a3](https://github.com/ublue-os/base/commit/f8917a3258196f85b8e3805f5ebcb1c9c0db06a7))
* allow forks to push to registry with label ([#86](https://github.com/ublue-os/base/issues/86)) ([14b1b7c](https://github.com/ublue-os/base/commit/14b1b7cb044ec616817aa30075609469dcb9986b))
* artifact upload/extract ([#88](https://github.com/ublue-os/base/issues/88)) ([6590066](https://github.com/ublue-os/base/commit/6590066ebcf72d6c4a56730dd682088db17d7df0))
* re-tag image ([#92](https://github.com/ublue-os/base/issues/92)) ([a831ce0](https://github.com/ublue-os/base/commit/a831ce00df84d94e2bdb48013f650bcbb5b39568))
* remove 38 ([#89](https://github.com/ublue-os/base/issues/89)) ([8a6f343](https://github.com/ublue-os/base/commit/8a6f3433ad45b0f9f3da974a691001c02f498fb1))
* remove 38 builds and fix logo metadata ([#62](https://github.com/ublue-os/base/issues/62)) ([521f0ad](https://github.com/ublue-os/base/commit/521f0adcda598a1bf494d969df375f0c0a03a10c))
* remove if statements ([#96](https://github.com/ublue-os/base/issues/96)) ([0c7bc17](https://github.com/ublue-os/base/commit/0c7bc17666ae038a0504d24a0e683f724c734527))
* remove old pr workflow sections ([#98](https://github.com/ublue-os/base/issues/98)) ([4a21580](https://github.com/ublue-os/base/commit/4a21580f4e4d40692449bae61a75a555e8569be1))
* rename package back to `base` ([#97](https://github.com/ublue-os/base/issues/97)) ([785b8f0](https://github.com/ublue-os/base/commit/785b8f0d8adb8513bbe94b8918bfc0033ee0ca45))
* restore download artifact step, support multi-line tags ([#90](https://github.com/ublue-os/base/issues/90)) ([c40bddf](https://github.com/ublue-os/base/commit/c40bddfdf39a61545700ecb8123a02abd24a4f8f))
* update cosign action ([#94](https://github.com/ublue-os/base/issues/94)) ([0aff9ba](https://github.com/ublue-os/base/commit/0aff9bac374c3494f57a360fd4426afe705bfee9))

## 1.0.0 (2023-02-04)


### Features

* Add code-of-conduct ([#39](https://github.com/ublue-os/base/issues/39)) ([aab8078](https://github.com/ublue-os/base/commit/aab8078cfdc7d2354e057a0ca4771d3a53d2df4c))
* add conventional commit linting and release notes generator ([b7820b4](https://github.com/ublue-os/base/commit/b7820b4ba312ca939d0dc977ed9f6a08d135324b))
* tag PR builds independently from matrix.version, latest, and stable ([b022183](https://github.com/ublue-os/base/commit/b02218386235e6d40a11a48b5b1171e9acf8d1eb))


### Bug Fixes

* Don't generate an image when README.md is updated ([#36](https://github.com/ublue-os/base/issues/36)) ([8c170cf](https://github.com/ublue-os/base/commit/8c170cfe89dd306eec0940f4dc50ed245c94bc2b))
* only generate date tag for main branch ([94aa5bb](https://github.com/ublue-os/base/commit/94aa5bb8df2aac0985d4c9422b19b0c03a3f25b0))
