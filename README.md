# Netflame Stove - Home Assistant Integration

Home Assistant integration to control Netflame pellet stoves.

## Features

- On/off control
- Temperature reading
- Power control (levels 1-9)
- Alarm reading
- Climate entity for HVAC mode and power presets
- Sensors for temperature and alarms

## Installation

### Via HACS

1. Open HACS in your Home Assistant instance
2. Go to "Integrations"
3. Search for "Netflame Stove"
4. Install the integration
5. Restart Home Assistant

### Manual Installation

1. Clone this repository into your `custom_components` folder:
```bash
git clone https://github.com/evaristocuesta/netflame-homeassistant-integration.git ~/.homeassistant/custom_components/netflame
```

2. Restart Home Assistant

## Configuration

You will need to provide:
- **Serial**: Serial number of your Netflame stove
- **Password**: Access password for the stove

## Requirements

- Home Assistant 2024.1.0 or higher
- Internet connection (the stove communicates with cloud servers)

## Codeowners

- [@evaristocuesta](https://github.com/evaristocuesta)

## Issue Tracking

If you encounter any issues, please open an issue in the [issue tracker](https://github.com/evaristocuesta/netflame-homeassistant-integration/issues)
