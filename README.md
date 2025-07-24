# Micro-Air EasyStart Flex Integration for Home Assistant

This is still in early development!!!!!!

This custom integration connects to the Micro-Air EasyStart Flex via Bluetooth (using your existing ESPHome proxy or HA's Bluetooth integration). It provides sensors for status, faults, runtime, and more.

## Installation
- Add this repository to HACS as a custom integration.
- Restart Home Assistant.
- Go to Settings > Devices & Services > Add Integration > Search for "Micro-Air EasyStart Flex".
- Enter your device's Bluetooth MAC address when prompted.

## Features
- Sensors: Status (e.g., Idle/Starting/Running), Fault Code, Runtime Hours.
- Supports notifications and automations (e.g., alert on faults).
- Requires Bluetooth proxy in range.

For issues, see the [issue tracker](https://github.com/cbird527/ha-easystart-flex/issues).