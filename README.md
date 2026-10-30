# WyreStorm NetworkHD Home Assistant Integration

[![GitHub Release](https://img.shields.io/github/release/Matt-Hadley/wyrestorm-networkhd-ha.svg?style=flat-square)](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/releases)
[![License](https://img.shields.io/github/license/Matt-Hadley/wyrestorm-networkhd-ha.svg?style=flat-square)](LICENSE)
[![HACS](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=flat-square)](https://hacs.xyz/)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2026.8%2B-41BDF5.svg?style=flat-square)](https://www.home-assistant.io/)

A Home Assistant custom integration for WyreStorm NetworkHD AV-over-IP systems. It connects to the NetworkHD controller
over SSH and lets you route transmitters to receivers, switch the displays attached to receivers on and off, and see
whether each endpoint is online and passing video.

It is built on the [wyrestorm-networkhd](https://github.com/Matt-Hadley/wyrestorm-networkhd-py) Python library.

## Requirements

- Home Assistant 2026.8 or newer.
- A NetworkHD controller: NHD-000-CTL or NHD-CTL-PRO.
- **SSH enabled on the controller (port 10022).** The controller's default API access is Telnet, which this integration
  does not support; enable SSH on the controller before adding the integration.
- NetworkHD transmitters and receivers supported by the
  [wyrestorm-networkhd](https://github.com/Matt-Hadley/wyrestorm-networkhd-py) library.

Tested on an NHD-000-CTL (firmware v9.4.7, API v1.28) with NHD-400 transmitters and receivers (firmware v2.5.6).

## Installation

### HACS

1. In HACS, open the menu and choose **Custom repositories**.
2. Add `https://github.com/Matt-Hadley/wyrestorm-networkhd-ha` with category **Integration**.
3. Install **WyreStorm NetworkHD** and restart Home Assistant.

### Manual

1. Download `wyrestorm_networkhd.zip` from the
   [latest release](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/releases).
2. Unzip it into `config/custom_components/wyrestorm_networkhd/` (the zip holds the integration files directly, so
   create the folder first).
3. Restart Home Assistant.

## Configuration

Go to **Settings > Devices & services > Add integration** and search for **WyreStorm NetworkHD**.

| Field    | Default     | Notes                                    |
| -------- | ----------- | ---------------------------------------- |
| Host     |             | IP address or hostname of the controller |
| Username | `wyrestorm` | Controller SSH username                  |
| Password | `networkhd` | Controller SSH password                  |
| Port     | `10022`     | Controller SSH port                      |

The integration connects and queries the controller's version before creating the entry. If that fails you see one of:

- **Failed to connect** (`cannot_connect`): the controller is unreachable, SSH is not enabled, or the port is wrong.
- **Invalid authentication** (`invalid_auth`): the username or password was rejected.
- **Unexpected error** (`unknown`): anything else; check the Home Assistant log.

Each controller can be added once (its host identifies it).

### Options

**Configure** on the integration entry has one option:

- **Update interval (seconds)**: fallback polling interval, 10 to 300, default 60. The integration reloads when you
  change it.

### Reconfigure

**Reconfigure** on the integration entry changes the host, username, password and port. The new details are tested
before they are saved. Changing the host keeps the same controller device and its entities.

### Reauthenticate

If the controller rejects the stored username or password (for example after it was changed on the controller), the
integration stops retrying and Home Assistant shows a **Reauthenticate** prompt for the entry. Enter the current
credentials; they are tested before they are saved.

## Devices and entities

The integration creates one device for the controller and one for each transmitter and receiver. Endpoint devices are
named `Transmitter - <alias>` and `Receiver - <alias>`, using the alias set on the controller (or the endpoint's IP
address or true name when it has no alias). Entity IDs are built from the device name and the entity name when the
entity is first added.

The examples below use a controller at `192.168.1.50`, a transmitter with alias `Source1` and a receiver with alias
`Display1`. Aliases must not contain spaces: the controller's commands separate names with spaces.

### Controller: `WyreStorm NetworkHD (<host>)`

| Entity            | Example entity ID                                           | Notes                                                       |
| ----------------- | ----------------------------------------------------------- | ----------------------------------------------------------- |
| Reboot controller | `button.wyrestorm_networkhd_192_168_1_50_reboot_controller` | Reboots the controller; the integration reconnects after it |

### Transmitter: `Transmitter - <alias>`

| Entity          | Example entity ID                                   | Notes                                                                                                                                  |
| --------------- | --------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| Controller link | `binary_sensor.transmitter_source1_controller_link` | Connectivity (diagnostic). On while the endpoint is online. Attributes: `device_type`, `ip_address`, `mac_address`, `firmware_version` |
| Video input     | `binary_sensor.transmitter_source1_video_input`     | On while the HDMI input frame rate is above 0. Attribute: `hdmi_in_frame_rate`                                                         |

### Receiver: `Receiver - <alias>`

| Entity            | Example entity ID                                 | Notes                                                                            |
| ----------------- | ------------------------------------------------- | -------------------------------------------------------------------------------- |
| Controller link   | `binary_sensor.receiver_display1_controller_link` | As for transmitters                                                              |
| Video output      | `binary_sensor.receiver_display1_video_output`    | On while the HDMI output frame rate is above 0. Attribute: `hdmi_out_frame_rate` |
| Input source      | `select.receiver_display1_input_source`           | Options are `None` (disconnect) and every transmitter alias                      |
| Display power on  | `button.receiver_display1_display_power_on`       | Sends display power on to the display attached to the receiver                   |
| Display power off | `button.receiver_display1_display_power_off`      | Sends display power off                                                          |

### Availability and updates

- If the controller cannot be reached, all entities become unavailable. The integration reconnects automatically on the
  next update, and a service call or button press also reconnects first.
- After **Reboot controller**, all entities are unavailable until the controller is back and the next update succeeds.
- If an endpoint is offline, its **Controller link** sensor shows off and its other entities are unavailable.
- The controller pushes endpoint online/offline and video found/lost notifications, which trigger a refresh. Polling at
  the update interval is a fallback.

## Services

Devices are named by their alias or their true name. When more than one loaded controller has all the named devices, set
`config_entry_id` to choose one.

### `wyrestorm_networkhd.matrix_set`

Routes a transmitter to one or more receivers, or disconnects the receivers.

| Field             | Required | Description                                                       |
| ----------------- | -------- | ----------------------------------------------------------------- |
| `source_device`   | No       | Transmitter alias or true name. Leave out to disconnect receivers |
| `target_device`   | Yes      | Receiver alias(es) or true name(s); one name or a list            |
| `config_entry_id` | No       | The controller to use                                             |

```yaml
action: wyrestorm_networkhd.matrix_set
data:
  source_device: "Source1"
  target_device:
    - "Display1"
```

### `wyrestorm_networkhd.power_control`

Sends display power on or off to the displays attached to receivers.

| Field             | Required | Description                                            |
| ----------------- | -------- | ------------------------------------------------------ |
| `devices`         | Yes      | Receiver alias(es) or true name(s); one name or a list |
| `power_state`     | Yes      | `on` or `off`                                          |
| `config_entry_id` | No       | The controller to use                                  |

```yaml
action: wyrestorm_networkhd.power_control
data:
  devices:
    - "Display1"
  power_state: "on"
```

### Errors

- A device name that no loaded controller has, or that more than one has, fails with a validation error naming the
  devices (set `config_entry_id` in the second case).
- A `config_entry_id` that is not a loaded WyreStorm NetworkHD entry fails with a validation error.
- If the controller rejects or fails the command, the action fails with "Command to the NetworkHD controller at ...
  failed".

## Example automation

Route Source1 to Display1 and switch the display on when Source1 starts sending video:

```yaml
automation:
  - alias: "Display1: watch Source1"
    triggers:
      - trigger: state
        entity_id: binary_sensor.transmitter_source1_video_input
        to: "on"
    actions:
      - action: select.select_option
        target:
          entity_id: select.receiver_display1_input_source
        data:
          option: "Source1"
      - action: wyrestorm_networkhd.power_control
        data:
          devices: "Display1"
          power_state: "on"
```

## Diagnostics

On the integration entry, choose **Download diagnostics**. The file contains the entry, the latest controller data and
the raw device status and info, with the host, username, password, IP addresses, gateway and MAC addresses redacted.

## Security

The integration accepts the controller's SSH host key without verifying it, so nothing protects against another device
on your network impersonating the controller and receiving the SSH credentials. Keep the controller on a trusted network
segment.

## Known limitations

- Transmitters and receivers added to the controller after the integration is set up get devices and entities only
  after the integration entry is reloaded (or Home Assistant restarts).
- Aliases with spaces cannot be used (see [Devices and entities](#devices-and-entities)).

## Troubleshooting

- **Failed to connect**: check that SSH is enabled on the controller, that port 10022 is reachable from Home Assistant,
  and that the host is correct.
- **Endpoints unavailable**: check that they are online on the controller. Offline endpoints are kept and become
  available again when they come back.
- **Display power does nothing**: the receiver sends the command to its display; check that display control is set up
  for that receiver on the controller and that the display supports it.

To enable debug logging, add this to `configuration.yaml` and restart:

```yaml
logger:
  logs:
    custom_components.wyrestorm_networkhd: debug
    wyrestorm_networkhd: debug
```

Include the log, the diagnostics file and your controller firmware version when you
[report a bug](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/issues).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT; see [LICENSE](LICENSE).
