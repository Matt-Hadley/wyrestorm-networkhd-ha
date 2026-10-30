---
name: 🐛 Bug Report
about: Report a bug to help us improve
title: "[BUG] "
labels: ["bug"]
assignees: ""
---

## What happened?

<!-- Describe the bug in a few sentences -->

## What did you expect to happen?

<!-- Describe what you expected to happen -->

## Steps to reproduce

1.
2.
3.

## Environment

- Home Assistant version: <!-- Settings > About -->
- Integration version: <!-- HACS, or manifest.json -->
- wyrestorm-networkhd library version:
- Controller model: <!-- NHD-000-CTL or NHD-CTL-PRO -->
- Controller firmware / API version: <!-- output of `config get version` on the controller -->
- Transmitter / receiver models and firmware:

## Debug log

<!--
Enable debug logging in configuration.yaml, restart, reproduce the problem and paste the relevant log lines:

logger:
  logs:
    custom_components.wyrestorm_networkhd: debug
    wyrestorm_networkhd: debug

Remove passwords, public IP addresses and anything else you do not want to share. A diagnostics download from the
integration entry (already redacted) also helps.
-->

```text

```

## Additional context

<!-- Any other details that might help -->
