# Changelog

## [1.2.3](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/compare/v1.2.2...v1.2.3) (2026-10-30)


### Bug Fixes

* require wyrestorm-networkhd 3.1.1 ([ac28394](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/ac28394ce0637a6a78974d20fa10d476d85b78a6))
* require wyrestorm-networkhd 3.1.1 ([df58def](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/df58defc1ebb209d16cb4d40d1aa3555bc6504ad))

## [1.2.2](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/compare/v1.2.1...v1.2.2) (2026-10-30)


### Bug Fixes

* 1.2.2 — final audit fixes, strict typing, least-privilege CI ([5b7afef](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/5b7afefaeb9aca40a49e0699ec85f3092986df8d))
* keep the stored password out of the reconfigure form, point reauth to Reconfigure on a key mismatch ([301bf10](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/301bf107928ab2737ac0102334ac3f4ac72198bb))
* retry setup on a host key mismatch, cache the controller version, keep devices current ([3923e5a](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/3923e5a5cc4e1a62645f4e6336e423b249b7cf6f))
* type-check strictly against Home Assistant 2026.10 ([73bf049](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/73bf04971963a095524b40d04e3ead80dfbe5601))


### Documentation

* describe the checks CI runs, private vulnerability reporting ([edf125e](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/edf125e66819bf7c770d9f8c89327564b83e8f67))

## [1.2.1](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/compare/v1.2.0...v1.2.1) (2026-10-30)


### Bug Fixes

* remove stale devices outright and drop the obsolete update_interval key ([96fa031](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/96fa0315447e09f0d1b37e5a33a86aa03a72d55b))
* remove stale devices outright; drop obsolete update_interval key ([3722225](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/372222596e9d92312b992f31ed0258a669ee2939))

## [1.2.0](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/compare/v1.1.0...v1.2.0) (2026-10-30)


### Features

* add entities for new endpoints without a reload ([af61dbd](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/af61dbda247f3baca552afa63dfa53e4cdbd4422))
* declare the gold quality scale ([afd67c4](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/afd67c4813b83e360be68b441062932524755548))
* discover controllers with zeroconf ([9cc8f33](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/9cc8f33de8e32f3f0993a6a98e03f57cd44324a5))
* Gold quality scale — discovery, MAC identity, dynamic and stale devices ([17a9e59](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/17a9e59e7f473b604fcc4abfde21e820281081b9))
* identify the controller by its MAC address ([0ffb36f](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/0ffb36f9b9d87ac15040942c00350b5990422510))
* poll at a fixed 60 s fallback interval, drop the interval option ([19ea996](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/19ea996c698d14e762d24368032278520efb1a2c))
* remove devices the controller no longer reports ([603e4b9](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/603e4b9a1a5054be89be63249866395a903d81d2))
* translate setup and update errors ([5f84708](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/5f847080a37fe85c39742593ed4b90bc974551d6))


### Bug Fixes

* keep the real controller device for entries reconfigured under 1.0.x ([94cb844](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/94cb844d41d3c8763c192580703bf5144e89e024))


### Documentation

* document discovery, data updates, use cases and removal ([58bf587](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/58bf587732f7005c644a5c0fd6878bcd2ca2564c))
* use Reconfigure when a host-identified controller changes IP ([b535070](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/b535070c24a25001fdb96f3e057e9e84d6b910b9))

## [1.1.0](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/compare/v1.0.1...v1.1.0) (2026-10-30)


### Features

* pin the controller's SSH host key (trust on first use, optional fingerprint) ([a154b71](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/a154b71097ab40dfba90c0d1649a869a8f265fc5))
* pin the controller's SSH host key (trust on first use, optional fingerprint) ([cf69bf7](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/cf69bf765fcc9ddb711eea9ed51f9a695c6e2a29))


### Bug Fixes

* avoid angle brackets in the fingerprint help text (hassfest treats them as HTML) ([6bc4ab2](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/6bc4ab2099cd419dca8b32894fe352497a378a90))
* pin the same client after trust on first use and keep polling on a key mismatch ([fbd532e](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/fbd532ec38663e2ef993137ea097ac1e50f5e131))
* require wyrestorm-networkhd 3.1 for host key pinning ([53857f4](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/53857f42f68100f0c3020bc4c86e722cd4019928))


### Documentation

* describe runtime host key mismatch behaviour in the Security section ([6973488](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/69734884115b5c17214a10abb2d22f6b59b456ed))
* document SSH host key pinning and the fingerprint field ([a5c3b49](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/a5c3b498f7a8b6f7a3e98044806617315c40e883))

## [1.0.1](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/compare/v1.0.0...v1.0.1) (2026-10-30)


### Bug Fixes

* 1.0.1 — reauth, reconnect before commands, service input validation ([95b0bc3](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/95b0bc3d4c0ee240ebd06dab2e6da7f58603816c))
* reconnect before commands and keep entity state honest after them ([823da21](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/823da212fb75ae194d971420b605c50f54243bae))
* reject empty device lists and an empty source in services ([80277ff](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/80277ffc63516f4ee1a3cac24a1bda2c7bb5a65b))
* require Home Assistant 2026.8 ([97529a1](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/97529a15e63d76428eed6caa12daec9b0de7d088))
* start a reauth flow when the controller rejects the credentials ([6697719](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/66977191a52ec154ada236da3c08b2f8c53c13d1))


### Documentation

* space-free alias examples, reauth, known limitations ([e71dcf3](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/e71dcf3fca195fbddf41f759f5e61f70821600ee))

## [1.0.0](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/compare/v0.2.4...v1.0.0) (2026-10-30)


### ⚠ BREAKING CHANGES

* requires wyrestorm-networkhd>=3.0.0,<4.
* services.yaml now documents the registered services matrix_set (source_device optional = disconnect, target_device) and power_control (devices, power_state) instead of set_matrix/set_power; matrix_set takes a single source_device; a new optional config_entry_id field selects the controller. update_interval moved from the connection form to the options flow. iot_class is now local_push. Input Source selects and display power buttons lose their "configuration" entity category.

### Features

* add diagnostics, translations, icons and local brand image ([dcca48d](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/dcca48d32f34a2894569e3fa7748ddce803a89c2))
* reconnect, availability and per-controller services ([f3745b8](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/f3745b8c3b57f363e9a2a2567a8fbbdd0244571a))
* require wyrestorm-networkhd 3.x ([4c2c331](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/4c2c3310d3505cc5d6b1c7109562f335b95bf7c3))


### Documentation

* ask for HA, library and controller versions and a debug log in bug reports ([d6103e0](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/d6103e051960dce44badf37d2ddc95d0eb99cbba))
* correct make help descriptions ([d0be4d4](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/d0be4d4ecb9d5db745d2a31468249d766f36e194))
* rewrite CONTRIBUTING for Python 3.14 and the HA test setup ([5bbc284](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/5bbc284c0e50c762c1c1efa3f8838bd943021075))
* rewrite README to match the integration ([910b8ec](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/910b8ec43ba56c3a4a1e67d5b3ba54023ee4f749))
* update CLAUDE.md for the reworked coordinator and services ([8f789f4](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/8f789f4c6320ed162d1b2337699e1694e91b1c4b))

## [0.2.4](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/compare/v0.2.3...v0.2.4) (2025-09-03)


### Bug Fixes

* correct controller reboot API method path ([39a609b](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/39a609b1783f94824be3a2c278bc7ab7a754ca33))

## [0.2.3](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/compare/v0.2.2...v0.2.3) (2025-08-31)


### Bug Fixes

* remove redundant device status refresh in data update ([349ac94](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/349ac94454fa771d1646f8e9fa0379c99de1981b))

## [0.2.2](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/compare/v0.2.1...v0.2.2) (2025-08-31)


### Bug Fixes

* remove unnecessary delay in matrix assignments refresh ([7f57b10](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/7f57b105976854a8801da3fc75eb67cbd355f221))

## [0.2.1](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/compare/v0.2.0...v0.2.1) (2025-08-31)


### Bug Fixes

* add delay between matrix assignments and device status refresh ([518f82e](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/518f82e3f7682dce4744dd8a25c4f09da93c5869))
* increase delay between matrix assignments and device status refresh ([896934a](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/896934ac1db78dd702aa8fe3117bb0c1ae415d1b))

## [0.2.0](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/compare/v0.1.10...v0.2.0) (2025-08-31)


### Features

* refresh device status on matrix changes and improve performance documentation ([f739f6f](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/f739f6f3f53e26e5e538e994edb456baedbc5ad3))


### Bug Fixes

* correct manifest.json key ordering and move HACS validation before release ([78d0f43](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/78d0f43a4fb39f08c0a3050f0bfdf49f4f8b885b))

## [0.1.10](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/compare/v0.1.9...v0.1.10) (2025-08-31)


### Bug Fixes

* create HACS-compatible zip with files at root level ([2702334](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/2702334f7327d2e8b7ad81e7da5af7e570441e50))

## [0.1.9](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/compare/v0.1.8...v0.1.9) (2025-08-31)


### Bug Fixes

* correct config flow domain registration to use parameter instead of class attribute ([151f53e](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/151f53e496dbae426523044bd56fae34fad86218))
* sort manifest.json keys alphabetically for consistency ([cd44c1b](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/cd44c1b44478a0b0f65f2c9bcd711de7c119332e))

## [0.1.8](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/compare/v0.1.7...v0.1.8) (2025-08-31)


### Bug Fixes

* make HACS validation non-blocking and simplify hacs.json ([2121617](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/21216174d2064e28e7a27cbbbdd302ca6728e321))

## [0.1.7](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/compare/v0.1.6...v0.1.7) (2025-08-31)


### Bug Fixes

* suppress false positive security warnings for default credentials ([cec7e8f](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/cec7e8f680245dd53ae626c674f02c1e176c5123))
* update hacs.json for HACS validation compliance ([987963e](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/987963e1f19a997431cd24f65a7277b1dad71e5f))
* update release workflow to exclude cache and temp files from zips ([bafb476](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/bafb47681630095f1066b4312bbba1ec6a0286b3))

## [0.1.6](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/compare/v0.1.5...v0.1.6) (2025-08-31)


### Bug Fixes

* correct module path in test patch decorators ([d150979](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/d1509796a2a7ee47b1a43717ebbde9a5c99ef665))
* resolve mypy error in config_flow.py ([e653855](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/e653855acc5bd667d56c0d59c08742528a2b5b54))

## [0.1.5](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/compare/v0.1.4...v0.1.5) (2025-08-31)


### Bug Fixes

* import test fixtures in conftest.py for global availability ([eab0559](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/eab05596b34ee5c6b3bfc0b558240fe66df613ae))

## [0.1.4](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/compare/v0.1.3...v0.1.4) (2025-08-31)


### Bug Fixes

* remove pytest-asyncio version constraint to resolve dependency conflict ([ee2047e](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/ee2047ede404375635f08e18c481a7a38cb7b941))

## [0.1.3](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/compare/v0.1.2...v0.1.3) (2025-08-31)


### Bug Fixes

* remove pytest-cov version constraint to resolve dependency conflict ([bce42df](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/bce42df8bde1e61ac1a3eddd59fdd3d88ad8dc6f))

## [0.1.2](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/compare/v0.1.1...v0.1.2) (2025-08-31)


### Bug Fixes

* use pytest-homeassistant-custom-component for testing ([efd8146](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/efd8146d5feda41033c2ded7590b284429f76fb6))

## [0.1.1](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/compare/v0.1.0...v0.1.1) (2025-08-31)


### Bug Fixes

* add homeassistant test dependency for GitHub Actions ([c305840](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/c305840ec27581ef6bd5131bdcbcac007a750760))

## 0.1.0 (2025-08-30)


### Features

* add comprehensive CI/CD infrastructure and project scaffolding ([123baac](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/123baac04791c65c75b5a466a73d6f8d04b2ba83))
* add comprehensive test suite and development infrastructure ([a59ff5d](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/a59ff5d935eb584384e0eded6785c00c921d0194))
* add controller reboot button ([fbedc2a](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/fbedc2a383294aeaefc875e9f6946e2fef0f0168))
* add device_jsonstring selective refresh option ([97b6bd8](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/97b6bd82a4a49d01a535c2ea3597db479576b586))
* add real-time notification support for instant updates ([3407a25](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/3407a25bb6a352d45a84ca25475953f87a3d6e5d))
* complete wyrestorm_networkhd_2 integration with comprehensive entity support ([c5c4c69](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/c5c4c69c5ccfd6d92bb73caf0768fbdf1dcbc4c8))
* enhance availability checks for binary sensors, buttons, and selects ([21c9c53](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/21c9c53faeaad1984559497ee4ecc414d714f696))
* implement selective refresh optimization to reduce API overhead ([88eef64](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/88eef648636860cf219e4e42b3424d61e855fcbe))
* implement smart device info caching to reduce API load ([52aedd0](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/52aedd028be704679842a1969e2bb430dfe39afb))
* initial Home Assistant integration for WyreStorm NetworkHD ([4ee164b](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/4ee164b6fd4de0ebea7e803e63394fb797db8f61))
* refactor WyreStorm integration by consolidating device utilities and enhancing entity setup logic ([63db7ea](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/63db7ea5bca3ec9811da23bce9901f7124fff75e))


### Bug Fixes

* add missing voluptuous dependency to pyproject.toml ([b213bbd](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/b213bbdd1bbe4b8dbc4948bbdb3e87457f5b0c7d))
* correct Home Assistant config flow class naming convention ([097a895](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/097a895b9e70680fe85771a144a8d8a861d0983e))
* correct notification handlers and HACS validation requirements ([0049090](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/00490903fdd84b06dae187bb1aa9b28ae8655289))
* remove incorrect DOMAIN constants from model files ([74a5cc3](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/74a5cc3df6c4016b73ef86c08b0da6b3d5538767))
* remove invalid release-please action parameters ([35e2325](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/35e2325fe4f6e54e7ec00d084487f3c81e1a5f20))
* remove problematic xfail tests and fix device equality test ([e81b717](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/e81b717eebb0d81f211f4c8b5659bcc8eb8e6a79))
* resolve all mypy type checking errors ([0f6ec09](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/0f6ec09750f6f0589d5a350c816c82a902c0553a))
* resolve test fixture import linting issues and clean up redundant noqa comments ([4ed9f5d](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/4ed9f5dd2e276760874ec847b8b0cab433b87304))
* update all tests to work with new coordinator structure ([603c4fd](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/603c4fdee8f630edbb472503f0ad0458cba23329))


### Documentation

* comprehensive documentation improvements for gold standard integration ([a558997](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/a558997db7a8720d4238180e05a00b42b2ff6667))
* update README and CONTRIBUTING for current project structure ([bd2a483](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/commit/bd2a483140eaa9937b0881341472d4db9f767c4e))
