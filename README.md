# WyreStorm NetworkHD Home Assistant Integration

[![GitHub Release](https://img.shields.io/github/release/Matt-Hadley/wyrestorm-networkhd-ha.svg?style=flat-square)](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/releases)
[![License](https://img.shields.io/github/license/Matt-Hadley/wyrestorm-networkhd-ha.svg?style=flat-square)](LICENSE)
[![HACS](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=flat-square)](https://hacs.xyz/)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2026.10%2B-41BDF5.svg?style=flat-square)](https://www.home-assistant.io/)

A Home Assistant custom integration for [WyreStorm](https://www.wyrestorm.com) NetworkHD AV-over-IP systems. NetworkHD
sends HDMI video over a network: transmitters (encoders) sit next to the sources, receivers (decoders) next to the
displays, and a controller manages which source each display shows. The integration connects to the NetworkHD controller
over SSH and lets you route transmitters to receivers, switch the displays attached to receivers on and off, and see
whether each endpoint is online and passing video.

It is built on the [wyrestorm-networkhd](https://github.com/Matt-Hadley/wyrestorm-networkhd-py) Python library.

## Use cases

- Switch the source of every display from a Home Assistant dashboard, a voice assistant or a scene ("Movie night": the
  media player on the living room TV, the game console on the den TV).
- Follow what is happening: route a camera or doorbell feed to the kitchen display when someone rings, then switch back.
- Turn displays on and off with the rest of the house: off when everyone leaves or at night, on when a source starts
  sending video.
- Notice problems: get notified when a transmitter or receiver drops off the network, or a source stops sending video.

## Requirements

- Home Assistant 2026.10 or newer.
- A NetworkHD controller: NHD-000-CTL or NHD-CTL-PRO.
- **SSH enabled on the controller (port 10022).** The controller's default API access is Telnet, which this integration
  does not support; enable SSH on the controller before adding the integration.
- NetworkHD transmitters and receivers supported by the
  [wyrestorm-networkhd](https://github.com/Matt-Hadley/wyrestorm-networkhd-py) library.

## Supported devices

Known to work:

- NHD-000-CTL controller (tested with firmware v9.4.7, API v1.28)
- NHD-400 transmitters and receivers (tested with firmware v2.5.6)

Expected to work, not tested: the NHD-CTL-PRO controller, and the other NetworkHD transmitters and receivers that the
controller lists (the integration only uses the controller's API, never talks to endpoints directly).

Not supported: controllers reachable only over Telnet (enable SSH), and WyreStorm products outside the NetworkHD range.

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

Home Assistant discovers NetworkHD controllers on its own network (see [Discovery](#discovery)): a **Discovered** card
appears under **Settings > Devices & services**; select **Add** and enter the SSH details below (without the host).
Otherwise go to **Settings > Devices & services > Add integration** and search for **WyreStorm NetworkHD**.

| Field                               | Default     | Notes                                                                                                                                                                                  |
| ----------------------------------- | ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Host                                |             | IP address or hostname of the controller. Find it in your router's list of clients (a host named `NHD-000-CTL-...`). Give the controller a fixed address (DHCP reservation) if you can |
| Username                            | `wyrestorm` | Controller SSH username; the factory default unless you changed it on the controller                                                                                                   |
| Password                            | `networkhd` | Controller SSH password; the factory default unless you changed it on the controller                                                                                                   |
| Port                                | `10022`     | The controller's SSH API port                                                                                                                                                          |
| SSH host key fingerprint (optional) |             | Pin the controller's key before the first connect (see [Security](#security))                                                                                                          |

The integration connects and queries the controller's version before creating the entry. If that fails you see one of:

- **Failed to connect** (`cannot_connect`): the controller is unreachable, SSH is not enabled, or the port is wrong.
- **Invalid authentication** (`invalid_auth`): the username or password was rejected.
- **Not a valid SSH host key fingerprint** (`invalid_host_key_fingerprint`): the fingerprint field could not be parsed.
- **Different SSH host key** (`host_key_mismatch`): the controller presented another key than the one you entered; the
  message shows the presented fingerprint.
- **Unexpected error** (`unknown`): anything else; check the Home Assistant log.

If you leave the fingerprint empty, the integration shows the SSH host key the controller presented and asks you to
confirm it; it is then pinned (see [Security](#security)).

Each controller can be added once. It is identified by its MAC address, which the controller announces over mDNS (the
SSH API does not report it); a controller that does not answer mDNS is identified by its host until it does.

### Reconfigure

**Reconfigure** on the integration entry changes the host, username, password, port and SSH host key fingerprint. The
new details are tested before they are saved. Changing the host keeps the same controller device and its entities; if
the new host announces a different MAC address, it is another controller and reconfigure stops with "different
controller". The password field starts empty; leave it empty to keep the current password. The fingerprint field is
pre-filled with the pinned key: edit it to pin another key, or clear it to confirm the key the controller presents now.

### Discovery

The controller announces itself over mDNS as a `_workstation._tcp` service named `NHD-000-CTL-<MAC> [<MAC>]`. Home
Assistant's zeroconf discovery picks that up and offers to add the controller. Discovery also follows a controller that
gets a new IP address: the entry is updated to the new address and reloaded. Only the address changes; the pinned SSH
host key still has to match, so a different device at that address is refused (see [Security](#security)).

mDNS is multicast and does not cross VLANs or subnets unless your network reflects it; add the controller by host then.
To learn the MAC of a controller added by host, the integration asks the controller directly (unicast mDNS to port 5353)
at every startup until it answers; that also works across subnets if UDP port 5353 is allowed.

### Reauthenticate

If the controller rejects the stored username or password (for example after it was changed on the controller), the
integration stops retrying and Home Assistant shows a **Reauthenticate** prompt for the entry. Enter the current
credentials; they are tested before they are saved. If the controller presents a different SSH host key, use
**Reconfigure** instead (see [Security](#security)).

## Devices and entities

The integration creates one device for the controller and one for each transmitter and receiver. Endpoint devices are
named `Transmitter - <alias>` and `Receiver - <alias>`, using the alias set on the controller (or the endpoint's IP
address or true name when it has no alias). Entity IDs are built from the device name and the entity name when the
entity is first added.

Transmitters and receivers added to the controller later get their devices and entities at the next refresh, without a
reload. Devices the controller no longer reports (an endpoint removed from the controller, or a controller device left
over from an old address) are removed after three refreshes in a row without them; you can also delete such a device
yourself from its device page.

The examples below use a controller at `192.0.2.10`, a transmitter with alias `Source1` and a receiver with alias
`Display1`. Aliases must not contain spaces: the controller's commands separate names with spaces.

### Controller: `WyreStorm NetworkHD (<host>)`

| Entity            | Example entity ID                                         | Notes                                                                      |
| ----------------- | --------------------------------------------------------- | -------------------------------------------------------------------------- |
| Reboot controller | `button.wyrestorm_networkhd_192_0_2_10_reboot_controller` | Configuration. Reboots the controller; the integration reconnects after it |

### Transmitter: `Transmitter - <alias>`

| Entity          | Example entity ID                                   | Notes                                                                                                                                  |
| --------------- | --------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| Controller link | `binary_sensor.transmitter_source1_controller_link` | Connectivity (diagnostic). On while the endpoint is online. Attributes: `device_type`, `ip_address`, `mac_address`, `firmware_version` |
| Video input     | `binary_sensor.transmitter_source1_video_input`     | On while the HDMI input frame rate is above 0. Attribute: `hdmi_in_frame_rate`                                                         |

### Receiver: `Receiver - <alias>`

| Entity            | Example entity ID                                 | Notes                                                                            |
| ----------------- | ------------------------------------------------- | -------------------------------------------------------------------------------- |
| Controller link   | `binary_sensor.receiver_display1_controller_link` | As for transmitters (diagnostic)                                                 |
| Video output      | `binary_sensor.receiver_display1_video_output`    | On while the HDMI output frame rate is above 0. Attribute: `hdmi_out_frame_rate` |
| Input source      | `select.receiver_display1_input_source`           | Options are `None` (disconnect) and every transmitter alias                      |
| Display power on  | `button.receiver_display1_display_power_on`       | Sends display power on to the display attached to the receiver                   |
| Display power off | `button.receiver_display1_display_power_off`      | Sends display power off                                                          |

### Availability

- If the controller cannot be reached, all entities become unavailable. The integration reconnects automatically on the
  next update, and a service call or button press also reconnects first. The loss and the recovery are each logged once.
- After **Reboot controller**, all entities are unavailable until the controller is back and the next update succeeds.
- If an endpoint is offline, its **Controller link** sensor shows off and its other entities are unavailable.

## Data updates

The controller pushes a notification when an endpoint goes online or offline and when a transmitter or receiver finds or
loses video; each one triggers a refresh (bursts are collapsed into one refresh, at most every 10 seconds). The
integration also polls the controller every 60 seconds as a fallback. A refresh sends three commands over the one SSH
connection (the device info, with MAC addresses and firmware versions, and the controller's version are re-read only
every 10 minutes, after an endpoint notification or after reconnecting). Alias renames and firmware updates show on the
devices at the next refresh that reads them. Changing a receiver's source re-reads only the routing; display power
commands do not refresh, because the controller does not report display power.

The polling interval is fixed. The controller answers one command at a time, so polling faster would delay your
commands. To poll on your own schedule instead, disable polling in the entry's **System options** and call
`homeassistant.update_entity` from an automation.

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

## Examples

### Show a source on a display when it starts sending video

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

### Switch all displays off at night

```yaml
automation:
  - alias: "Displays off at midnight"
    triggers:
      - trigger: time
        at: "00:00:00"
    actions:
      - action: wyrestorm_networkhd.power_control
        data:
          devices:
            - "Display1"
            - "Display2"
          power_state: "off"
```

### Get notified when an endpoint goes offline

```yaml
automation:
  - alias: "NetworkHD endpoint offline"
    triggers:
      - trigger: state
        entity_id:
          - binary_sensor.transmitter_source1_controller_link
          - binary_sensor.receiver_display1_controller_link
        to: "off"
        for: "00:05:00"
    actions:
      - action: notify.notify
        data:
          message: "{{ trigger.to_state.name }} has been offline for 5 minutes"
```

## Diagnostics

On the integration entry, choose **Download diagnostics**. The file contains the entry, the latest controller data and
the raw device status and info, with the host, username, password, IP addresses, gateway, MAC address fields and
discovery details redacted. Endpoint true names (for example `NHD-400-RX-E4CE02BB0001`) are kept: they identify the
devices and contain the endpoint's MAC address.

## Security

The integration pins the controller's SSH host key (trust on first use): when you add the controller it shows the key
the controller presented and asks you to confirm it, and from then on it refuses to connect, before sending the username
and password, if the controller presents a different key. Entries set up with 1.0.x pin the key presented on their first
connection after upgrading (logged once at INFO).

To pin the key before the first connection instead, enter its fingerprint in the **SSH host key fingerprint** field. Get
it from a machine you trust on the same network:

```bash
ssh-keyscan -p 10022 <host> | ssh-keygen -lf -
```

Paste the `SHA256:...` line(s); several fingerprints are allowed (one per line). Controllers usually offer an ECDSA and
an RSA key and the integration negotiates ECDSA, so paste both lines or the ECDSA one.

If the controller presents a different key later, entities go unavailable and a repair issue is shown with the presented
fingerprint; Home Assistant keeps checking at each poll without sending credentials (the key is rejected before login),
and recovers automatically if the pinned key comes back. (If the key differs when the entry is set up, at startup or on
reload, setup is retried the same way, so a new address found by discovery is picked up.) If you expect the change (the
controller was replaced or reset), use **Reconfigure** to enter the new fingerprint or clear the field to confirm the
new key. Otherwise find out what is answering at the controller's address. Diagnostics show whether a key is pinned and
the pinned fingerprint.

## Known limitations

- Only video routing and display power are exposed. Audio, USB, IR and serial routing, video walls and multiview layouts
  are not.
- Display power buttons send a command; the controller does not report whether the display is on, so there is no power
  state.
- Aliases with spaces cannot be used (see [Devices and entities](#devices-and-entities)).
- Only SSH is supported, not Telnet.
- Discovery needs mDNS from the controller to reach Home Assistant, which usually means the same VLAN or subnet.
- The polling interval is fixed at 60 seconds (changes are pushed, so this is a fallback).

## Troubleshooting

### "Failed to connect" when adding the controller

SSH is not enabled on the controller (its default API access is Telnet), the host is wrong, or port 10022 is blocked
between Home Assistant and the controller. Enable SSH on the controller, check the host, and check that
`ssh -p 10022 wyrestorm@<host>` works from another machine on the Home Assistant network.

### "Invalid authentication"

The controller rejected the username or password. The factory defaults are `wyrestorm` / `networkhd`; if they were
changed on the controller, use the current ones. If this happens to a working entry, Home Assistant asks you to
reauthenticate.

### Entities unavailable and a "SSH host key changed" repair

The controller presented a different SSH host key than the pinned one, so Home Assistant did not log in. If the
controller was replaced or reset, use **Reconfigure** and enter the new fingerprint (or clear the field to confirm the
new key). Otherwise find out what is answering at the controller's address. See [Security](#security).

### Endpoints unavailable

The endpoint is offline on the controller (its **Controller link** sensor is off). Check its power and network
connection; it becomes available again when the controller reports it online.

### Display power does nothing

The receiver sends the command to its display over CEC, RS-232 or IR, as set up on the controller. Check that display
control is set up for that receiver on the controller and that the display supports it.

### The controller is not discovered

mDNS does not reach Home Assistant, usually because the controller is on another VLAN or subnet. Add it by host instead,
or enable an mDNS reflector on your router.

### The controller keeps an IP-based identity

The integration learns the controller's MAC by asking it over unicast mDNS (UDP port 5353) at every startup. If a
firewall blocks that port between Home Assistant and the controller, the entry stays identified by its host, which still
works but means discovery cannot follow an address change. Allow UDP 5353 from Home Assistant to the controller and
restart, or give the controller a fixed address.

If such a controller changes IP address, discovery may offer it as a new controller. Do not accept it (that would add
the controller twice); use **Reconfigure** on the existing entry to enter the new address instead.

To enable debug logging, add this to `configuration.yaml` and restart:

```yaml
logger:
  logs:
    custom_components.wyrestorm_networkhd: debug
    wyrestorm_networkhd: debug
```

Include the log, the diagnostics file and your controller firmware version when you
[report a bug](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/issues).

## Removing the integration

This integration follows standard integration removal: go to **Settings > Devices & services**, select **WyreStorm
NetworkHD**, open the menu of the entry and select **Delete**. Nothing has to be cleaned up on the controller; you can
switch its SSH access off again if nothing else uses it. To remove the files too, remove the integration in HACS (or
delete `config/custom_components/wyrestorm_networkhd/`) and restart Home Assistant.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT; see [LICENSE](LICENSE).
