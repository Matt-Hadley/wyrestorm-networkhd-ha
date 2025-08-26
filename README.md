# WyreStorm NetworkHD Home Assistant Integration

[![GitHub Release](https://img.shields.io/github/release/Matt-Hadley/wyrestorm-networkhd-ha.svg?style=flat-square)](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/releases)
[![License](https://img.shields.io/github/license/Matt-Hadley/wyrestorm-networkhd-ha.svg?style=flat-square)](LICENSE)

A comprehensive Home Assistant integration for WyreStorm NetworkHD devices, providing real-time control and monitoring of matrix switching, device status, and display power management.

## Features

🎯 **Real-time Device Monitoring** - Live status updates for all encoders and decoders  
🔀 **Matrix Switching Control** - Route sources to displays with instant feedback  
⚡ **Display Power Management** - CEC/RS232/IR power control for connected displays  
📊 **Comprehensive Status Sensors** - Controller connectivity, video activity, and display power  
🎛️ **Source Selection** - Easy source switching for decoder devices  
🔧 **Advanced Services** - Automation-ready custom services  
⚙️ **Configurable Polling** - Adjustable update intervals (10-300 seconds)

## Supported Devices

- WyreStorm NetworkHD 110/140 series
- WyreStorm NetworkHD 400/500 series  
- WyreStorm NetworkHD 600 series
- Any WyreStorm NetworkHD device with SSH API support

## Installation

### HACS (Recommended)

1. Add this repository to HACS as a custom repository
2. Install "WyreStorm NetworkHD" from HACS
3. Restart Home Assistant
4. Go to Configuration > Integrations
5. Click "+" and search for "WyreStorm NetworkHD"

### Manual Installation

1. Download the latest release
2. Copy the `custom_components/wyrestorm_networkhd` folder to your `config/custom_components/` directory
3. Restart Home Assistant
4. Add the integration through the UI

## Configuration

The integration is configured entirely through the Home Assistant UI:

### Initial Setup
1. **Host**: IP address of your NetworkHD controller
2. **Username**: SSH username (default: `wyrestorm`)
3. **Password**: SSH password (default: `networkhd`)
4. **Port**: SSH port (default: `10022`)
5. **Update Interval**: Polling frequency in seconds (default: 60, range: 10-300)

### Options (Configurable After Setup)
- **Update Interval**: Modify the polling frequency through integration options

## Entities

The integration creates multiple entity types for comprehensive device control and monitoring:

### Binary Sensors

#### Controller Link
- **Entity ID**: `binary_sensor.{device_name}_controller_link`
- **Purpose**: Indicates if the device is online and responding to the controller
- **Data Source**: `config_get_devicejsonstring()` → `online` field
- **Real-time Updates**: Endpoint notifications

#### Video Input Active  
- **Entity ID**: `binary_sensor.{device_name}_video_input_active`
- **Purpose**: Shows if the encoder has an active HDMI input signal (source connected)
- **Data Source**: `config_get_device_status()` → `hdmi in active` field
- **Real-time Updates**: Video notifications
- **Device Types**: Encoders only

#### Video Output Active
- **Entity ID**: `binary_sensor.{device_name}_video_output_active`  
- **Purpose**: Shows if the decoder is outputting an active HDMI signal (display connected)
- **Data Source**: `config_get_device_status()` → `hdmi out active` field
- **Real-time Updates**: Video notifications
- **Device Types**: Decoders only


### Select Entities

#### Input Source
- **Entity ID**: `select.{device_name}_input_source`
- **Purpose**: Select which encoder (source) feeds to this decoder (display)
- **Options**: List of available encoder devices + "None" (disconnect)
- **Data Source**: `matrix_get()` for current assignments
- **Device Types**: Decoders only

### Button Entities

#### Display Power On/Off
- **Entity IDs**: 
  - `button.{device_name}_display_power_on`
  - `button.{device_name}_display_power_off`
- **Purpose**: Send power on/off commands to connected displays
- **Method**: Uses sink power commands (CEC/RS232/IR depending on configuration)
- **Device Types**: Decoders only

## Data Sources and API Mapping

The integration uses multiple WyreStorm API endpoints to provide comprehensive device information:

### Primary Data Sources

#### 1. Device JSON String (`config_get_devicejsonstring()`)
```json
{
  "aliasName": "Kitchen",
  "deviceType": "Receiver",
  "online": true,
  "ip": "192.168.0.169",
  "trueName": "NHD-400-RX-E4CE021114AB"
}
```
**Used For:**
- Controller Link binary sensor state
- Device identification and naming
- IP address information

#### 2. Device Status (`config_get_device_status()`)
```json
{
  "aliasname": "Kitchen",
  "hdmi in active": "false",
  "hdmi out active": "true",
  "hdmi out resolution": "1920x1080",
  "audio output format": "lpcm",
  "hdcp": "hdcp14"
}
```
**Used For:**
- Video Input/Output Active binary sensor states
- Additional device attributes (resolution, audio format, HDCP status)

#### 3. Matrix Status (`matrix_get()`)
**Used For:**
- Current source assignments for Input Source select entities
- Available source options for decoders

### Real-time Notifications

The integration subscribes to real-time device notifications for instant updates:

#### Endpoint Notifications
- **Updates**: Controller Link binary sensors
- **Trigger**: Device online/offline state changes

#### Video Notifications  
- **Updates**: Video Input/Output Active binary sensors
- **Trigger**: HDMI signal presence changes


### Update Strategy

- **Polling**: Configurable interval (10-300 seconds) for API data refresh
- **Notifications**: Real-time updates for immediate status changes
- **Data Combination**: Merges information from multiple sources for comprehensive device status

## Device Naming Convention

Devices are automatically named using the format:
- **Controllers**: `Controller - {host_ip}`
- **Encoders**: `Encoder - {alias_name_or_ip}`
- **Decoders**: `Decoder - {alias_name_or_ip}`

## Services

### `wyrestorm_networkhd.matrix_set`
Route sources to displays.

```yaml
service: wyrestorm_networkhd.matrix_set
data:
  source_device: "AppleTV"
  target_device: 
    - "Kitchen"
    - "Dining"
```

### `wyrestorm_networkhd.power_control`
Control display power via sink power commands.

```yaml
service: wyrestorm_networkhd.power_control
data:
  devices:
    - "Kitchen" 
    - "Dining"
  power_state: "on"  # or "off"
```

## Automation Examples

### Scene-based Matrix Switching
```yaml
automation:
  - alias: "Movie Night Setup"
    trigger:
      - platform: state
        entity_id: input_boolean.movie_mode
        to: "on"
    action:
      # Route Blu-ray player to all displays
      - service: wyrestorm_networkhd.matrix_set
        data:
          source_device: "BluRay"
          target_device:
            - "Kitchen"
            - "Dining"
      # Turn on all displays
      - service: wyrestorm_networkhd.power_control
        data:
          devices:
            - "Kitchen"
            - "Dining" 
          power_state: "on"
```

### Display Power Management Based on Activity

#### Turn On Displays When Source Comes Online
```yaml
automation:
  - alias: "Auto Power On Displays When Source Active"
    trigger:
      - platform: state
        entity_id: 
          - binary_sensor.appletv_video_input_active
          - binary_sensor.bluray_video_input_active
        to: "on"
    condition:
      # Only trigger if the encoder is currently routed to decoders
      - condition: template
        value_template: >
          {% set encoder = trigger.entity_id.split('.')[1].split('_video_input_active')[0] %}
          {% set kitchen_source = states('select.kitchen_input_source') %}
          {% set dining_source = states('select.dining_input_source') %}
          {{ encoder == kitchen_source or encoder == dining_source }}
    action:
      # Turn on displays that are currently set to this encoder
      - service: wyrestorm_networkhd.power_control
        data:
          devices: >
            {% set encoder = trigger.entity_id.split('.')[1].split('_video_input_active')[0] %}
            {% set devices = [] %}
            {% if states('select.kitchen_input_source') == encoder %}
              {% set devices = devices + ['kitchen'] %}
            {% endif %}
            {% if states('select.dining_input_source') == encoder %}
              {% set devices = devices + ['dining'] %}
            {% endif %}
            {{ devices }}
          power_state: "on"

#### Turn Off Displays When Source Goes Offline  
  - alias: "Auto Power Off Displays When Source Inactive"
    trigger:
      - platform: state
        entity_id: 
          - binary_sensor.appletv_video_input_active
          - binary_sensor.bluray_video_input_active
        to: "off"
        for:
          minutes: 5
    condition:
      # Only trigger if the encoder is currently routed to decoders
      - condition: template
        value_template: >
          {% set encoder = trigger.entity_id.split('.')[1].split('_video_input_active')[0] %}
          {% set kitchen_source = states('select.kitchen_input_source') %}
          {% set dining_source = states('select.dining_input_source') %}
          {{ encoder == kitchen_source or encoder == dining_source }}
    action:
      # Turn off displays that are currently set to this encoder
      - service: wyrestorm_networkhd.power_control
        data:
          devices: >
            {% set encoder = trigger.entity_id.split('.')[1].split('_video_input_active')[0] %}
            {% set devices = [] %}
            {% if states('select.kitchen_input_source') == encoder %}
              {% set devices = devices + ['kitchen'] %}
            {% endif %}
            {% if states('select.dining_input_source') == encoder %}
              {% set devices = devices + ['dining'] %}
            {% endif %}
            {{ devices }}
          power_state: "off"
```

### Status Monitoring and Notifications
```yaml
automation:
  - alias: "Notify When Encoder Goes Offline"
    trigger:
      - platform: state
        entity_id: 
          - binary_sensor.appletv_controller_link
          - binary_sensor.bluray_controller_link
        to: "off"
        for:
          minutes: 2
    action:
      - service: notify.mobile_app_phone
        data:
          title: "WyreStorm Alert"
          message: "{{ state_attr(trigger.entity_id, 'friendly_name') }} has gone offline"
```

## Development

### Requirements
- Docker Desktop
- Python 3.11+
- Home Assistant 2024.1+

### Local Development Setup

1. Clone the repository:
```bash
git clone https://github.com/Matt-Hadley/wyrestorm-networkhd-ha.git
cd wyrestorm-networkhd-ha
```

2. Set up the development environment:
```bash
./setup_dev.sh
```

3. Start Home Assistant:
```bash
docker-compose up -d
```

4. Access Home Assistant at http://localhost:8123

### Testing

The integration includes comprehensive testing:

```bash
# Install test dependencies
pip install -r requirements_test.txt

# Run tests
pytest tests/

# Run with coverage
pytest --cov=custom_components.wyrestorm_networkhd tests/
```

## Troubleshooting

### Connection Issues
- **SSH Access**: Verify SSH is enabled on your NetworkHD controller
- **Network Connectivity**: Ensure port 10022 is accessible from Home Assistant
- **Credentials**: Confirm username/password (defaults: `wyrestorm`/`networkhd`)
- **Firewall**: Check that no firewall is blocking the connection

### Device Discovery Issues
- **Device Status**: Ensure devices are online and responding to SSH
- **Logs**: Check Home Assistant logs for connection errors
- **API Response**: Verify devices appear in controller's device list

### Entity States Not Updating
- **Polling Interval**: Check if update interval is appropriate for your needs
- **Notifications**: Verify real-time notifications are being received
- **Data Sources**: Confirm API endpoints are returning expected data

### Display Power Control Not Working
- **Sink Power Setup**: Verify sink power is configured on decoder devices
- **Display Compatibility**: Ensure connected displays support CEC/RS232/IR control
- **Notification Monitoring**: Check if sink power notifications are being received

### Performance Issues
- **Polling Frequency**: Reduce update interval if experiencing high load
- **Network Latency**: Consider network performance to controller
- **Device Count**: Large numbers of devices may require longer intervals

### Enable Debug Logging
Add to your `configuration.yaml`:
```yaml
logger:
  logs:
    custom_components.wyrestorm_networkhd: debug
    wyrestorm_networkhd: debug
```

### Common Log Messages
- `"Using polling interval of X seconds"` - Confirms configured update interval
- `"Processing devices from combined JSON and status data"` - Normal data processing
- `"Successfully processed X real devices"` - Successful device discovery
- `"Controller Link"` notifications - Real-time connectivity updates
- `"Sink power notification"` - Display power status changes

## Advanced Configuration

### Customizing Entity Names
Device names can be customized by changing the alias names on your WyreStorm controller. The integration will automatically use these names for entity creation.

### Integration Options
After initial setup, you can modify:
- **Update Interval**: Change polling frequency through integration options
- **Reload Required**: Integration automatically reloads when options are changed

### Network Optimization
For optimal performance:
- Use wired network connections when possible
- Consider update intervals based on your automation needs
- Monitor network traffic if using very short polling intervals

## API Reference

The integration uses the [wyrestorm-networkhd](https://github.com/Matt-Hadley/wyrestorm-networkhd-py) Python library, which provides:

- **SSH Connection Management**: Automatic reconnection and error handling
- **API Command Interface**: Full access to WyreStorm API commands
- **Real-time Notifications**: Event-driven status updates
- **Data Parsing**: Structured responses from device APIs

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with appropriate tests
4. Commit your changes (`git commit -m 'Add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

### Development Guidelines
- Follow Home Assistant integration standards
- Add tests for new functionality
- Update documentation for user-facing changes
- Use proper logging levels (debug/info/warning/error)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Credits

Built on the excellent [wyrestorm-networkhd](https://github.com/Matt-Hadley/wyrestorm-networkhd-py) Python library.

## Support

- **Issues**: Report bugs and request features via [GitHub Issues](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/issues)
- **Discussions**: Join the conversation in [GitHub Discussions](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/discussions)
- **Home Assistant Community**: Get help in the [Home Assistant Community Forum](https://community.home-assistant.io/)